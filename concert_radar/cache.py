"""
concert_radar/cache.py — on-disk key/value cache with TTL, backed by sqlite.

Used by every external source (MusicBrainz life-span lookups, Last.fm similar
artists, Songkick pages, Bandsintown responses) so re-runs of the pipeline
don't re-hit rate-limited or slow endpoints. Session-state caching (as used
elsewhere in this app) doesn't survive a process restart on Railway; this
does, as long as the filesystem persists between requests on the same dyno.
"""

import json
import os
import sqlite3
import time
import threading

_LOCK = threading.Lock()
_DB_PATH = os.path.join(os.path.dirname(__file__), "data", "cache.sqlite")


def _ensure_db():
    os.makedirs(os.path.dirname(_DB_PATH), exist_ok=True)
    conn = sqlite3.connect(_DB_PATH)
    conn.execute(
        "CREATE TABLE IF NOT EXISTS kv ("
        " key TEXT PRIMARY KEY,"
        " value TEXT NOT NULL,"
        " expires_at REAL NOT NULL"
        ")"
    )
    conn.commit()
    return conn


def get(key):
    """Return the cached value for `key`, or None if missing/expired."""
    with _LOCK:
        conn = _ensure_db()
        try:
            row = conn.execute(
                "SELECT value, expires_at FROM kv WHERE key = ?", (key,)
            ).fetchone()
        finally:
            conn.close()
    if not row:
        return None
    value, expires_at = row
    if expires_at < time.time():
        return None
    try:
        return json.loads(value)
    except (TypeError, ValueError):
        return None


def set(key, value, ttl_seconds):
    """Store `value` (JSON-serialisable) under `key` for ttl_seconds."""
    with _LOCK:
        conn = _ensure_db()
        try:
            conn.execute(
                "INSERT INTO kv (key, value, expires_at) VALUES (?, ?, ?)"
                " ON CONFLICT(key) DO UPDATE SET value=excluded.value,"
                " expires_at=excluded.expires_at",
                (key, json.dumps(value), time.time() + ttl_seconds),
            )
            conn.commit()
        finally:
            conn.close()


def cached(key, ttl_seconds, fetch_fn):
    """Get-or-fetch helper: return cached value, else call fetch_fn() and store it."""
    hit = get(key)
    if hit is not None:
        return hit
    value = fetch_fn()
    if value is not None:
        set(key, value, ttl_seconds)
    return value


# TTL presets, in seconds, per spec.
TTL_MUSICBRAINZ_LIFESPAN = 30 * 24 * 3600   # life-span rarely changes; cache generously
TTL_LASTFM_SIMILAR       = 30 * 24 * 3600   # spec: 30 days
TTL_SONGKICK_PAGE        = 24 * 3600        # spec: 24h
TTL_BANDSINTOWN_EVENTS   = 24 * 3600        # events change daily (on-sale, sell-outs)
