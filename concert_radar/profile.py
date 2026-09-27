"""
concert_radar/profile.py — Phase 1: build the "who does this person actually
listen to, right now" profile that everything else in Concert Radar ranks
against.

Input is the already-parsed `dfm` DataFrame the rest of MusicDNA uses
(columns: ts, artistName, trackName, albumName, ms, ...) — produced by
app.py's zip parsing (10s+ plays, kids content already split out via
filters.split). We do NOT re-parse the Spotify export here; we reuse it,
per the existing app convention (see discovery.py, taste_drift.py, etc.).

Optionally refreshed with Spotify Web API top/recently-played artists via
spotify_api.py, to catch artists the user has picked up since their last
data export (extended-history exports are usually months stale).
"""

import math
import os
import re
import time
import unicodedata

import pandas as pd
import requests
import yaml

from concert_radar import cache

# ── Config (spec: both thresholds configurable) ────────────────────────────

DEFAULT_TOP_RANK_LIMIT = 200   # eligible "my artists" = affinity rank <= this
DEFAULT_MIN_HOURS      = 1.0   # AND total_hours >= this

_EXTRA_KIDS_KEYWORDS = {
    "bébé", "bebe", "baby", "lullaby", "berceuse", "comptine", "nursery",
}

_OVERRIDES_PATH = os.path.join(os.path.dirname(__file__), "overrides.yaml")

_MUSICBRAINZ_UA = "MusicDNA-ConcertRadar/1.0 (https://github.com/virgile-quenum/MusicDNA)"


# ── Normalisation (shared with matching.py, kept here to avoid an import
#    cycle since profile.py needs it for the extra kids filter too) ─────────

def normalise_name(name):
    """lowercase, strip accents, & -> and, drop punctuation, drop leading 'the'."""
    if not name:
        return ""
    n = unicodedata.normalize("NFKD", name)
    n = "".join(c for c in n if not unicodedata.combining(c))
    n = n.lower().strip()
    n = n.replace("&", " and ")
    n = re.sub(r"\bfeat\.?.*$", "", n)
    n = re.sub(r"\bft\.?.*$", "", n)
    n = re.sub(r"[^\w\s]", "", n)
    n = re.sub(r"^\s*the\s+", "", n)
    n = re.sub(r"\s+", " ", n).strip()
    return n


def _is_extra_kids(artist_name, track_name=""):
    a = (artist_name or "").lower()
    t = (track_name or "").lower()
    return any(kw in a or kw in t for kw in _EXTRA_KIDS_KEYWORDS)


# ── Overrides (overrides.yaml) ───────────────────────────────────────────────

def load_overrides():
    """
    overrides.yaml format:
      "R. Kelly": {status: not_touring, reason: "not touring"}
      "Empire Cast": {status: ended, reason: "TV cast, not a real band"}
    Returns dict keyed by normalised artist name.
    """
    if not os.path.exists(_OVERRIDES_PATH):
        return {}
    with open(_OVERRIDES_PATH, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    return {normalise_name(k): v for k, v in raw.items()}


# ── MusicBrainz life-span lookup (deceased artists / ended groups) ─────────

def _musicbrainz_lookup(artist_name):
    """Query MusicBrainz for an artist's life-span 'ended' flag. Returns
    dict {ended: bool, life_span: {...}} or None if not found / on error."""
    try:
        resp = requests.get(
            "https://musicbrainz.org/ws/2/artist",
            params={"query": "artist:" + artist_name, "fmt": "json", "limit": 1},
            headers={"User-Agent": _MUSICBRAINZ_UA},
            timeout=8,
        )
        if resp.status_code != 200:
            return None
        artists = resp.json().get("artists", [])
        if not artists:
            return None
        a = artists[0]
        life_span = a.get("life-span", {}) or {}
        return {"ended": bool(life_span.get("ended", False)), "life_span": life_span}
    except Exception:
        return None


def get_life_span(artist_name):
    """Cached (30d) MusicBrainz life-span check. Rate-limited to ~1req/s per
    MusicBrainz's own guidance."""
    key = "mb_lifespan:" + normalise_name(artist_name)

    def fetch():
        time.sleep(1.0)  # MusicBrainz asks for <=1 req/s, no auth
        return _musicbrainz_lookup(artist_name)

    return cache.cached(key, cache.TTL_MUSICBRAINZ_LIFESPAN, fetch)


def artist_status(artist_name, overrides):
    """
    Returns one of: "active", "ended", "not_touring", "unknown".
    Manual overrides win over MusicBrainz.
    """
    norm = normalise_name(artist_name)
    if norm in overrides:
        return overrides[norm].get("status", "active"), overrides[norm].get("reason", "")

    life_span = get_life_span(artist_name)
    if life_span is None:
        return "unknown", ""
    if life_span.get("ended"):
        return "ended", "MusicBrainz life-span: ended"
    return "active", ""


# ── Affinity scoring ─────────────────────────────────────────────────────────

def _apply_extra_kids_filter(dfm):
    mask = ~dfm.apply(
        lambda r: _is_extra_kids(r.get("artistName", ""), r.get("trackName", "")),
        axis=1,
    )
    return dfm[mask]


def build_artist_profile(dfm, top_rank_limit=DEFAULT_TOP_RANK_LIMIT,
                          min_hours=DEFAULT_MIN_HOURS, check_life_span=True,
                          now=None):
    """
    Build the per-artist affinity table.

    Returns a DataFrame with columns:
      artist, total_hours, plays, last_played, hours_last_12m,
      recency_weight, affinity_score, affinity_rank, status, status_reason,
      eligible
    sorted by affinity_score descending.
    """
    if dfm is None or dfm.empty:
        return pd.DataFrame(columns=[
            "artist", "total_hours", "plays", "last_played", "hours_last_12m",
            "recency_weight", "affinity_score", "affinity_rank",
            "status", "status_reason", "eligible",
        ])

    df = _apply_extra_kids_filter(dfm)
    if df.empty:
        return pd.DataFrame(columns=[
            "artist", "total_hours", "plays", "last_played", "hours_last_12m",
            "recency_weight", "affinity_score", "affinity_rank",
            "status", "status_reason", "eligible",
        ])

    ts_tz = df["ts"].dt.tz if hasattr(df["ts"], "dt") else None
    now = now or (pd.Timestamp.now(tz=ts_tz) if ts_tz else pd.Timestamp.now())
    cutoff_12m = now - pd.Timedelta(days=365)

    grouped = df.groupby("artistName").agg(
        total_ms=("ms", "sum"),
        plays=("trackName", "count"),
        last_played=("ts", "max"),
    ).reset_index().rename(columns={"artistName": "artist"})

    recent = df[df["ts"] >= cutoff_12m]
    recent_ms = recent.groupby("artistName")["ms"].sum().rename("recent_ms")
    grouped = grouped.merge(recent_ms, left_on="artist", right_index=True, how="left")
    grouped["recent_ms"] = grouped["recent_ms"].fillna(0)

    grouped["total_hours"]    = grouped["total_ms"] / 3_600_000
    grouped["hours_last_12m"] = grouped["recent_ms"] / 3_600_000

    # recency_weight = 0.5 + 0.5 * (hours_last_12m / total_hours)
    grouped["recency_weight"] = 0.5 + 0.5 * (
        grouped["hours_last_12m"] / grouped["total_hours"].replace(0, pd.NA)
    ).fillna(0)

    grouped["affinity_score"] = grouped["total_hours"].apply(math.log1p) * grouped["recency_weight"]

    grouped = grouped.sort_values("affinity_score", ascending=False).reset_index(drop=True)
    grouped["affinity_rank"] = grouped.index + 1

    overrides = load_overrides()
    statuses, reasons = [], []
    for artist in grouped["artist"]:
        if check_life_span:
            status, reason = artist_status(artist, overrides)
        else:
            status, reason = "unknown", ""
        statuses.append(status)
        reasons.append(reason)
    grouped["status"] = statuses
    grouped["status_reason"] = reasons

    grouped["eligible"] = (
        (grouped["affinity_rank"] <= top_rank_limit)
        & (grouped["total_hours"] >= min_hours)
        & (~grouped["status"].isin(["ended", "not_touring"]))
    )

    return grouped[[
        "artist", "total_hours", "plays", "last_played", "hours_last_12m",
        "recency_weight", "affinity_score", "affinity_rank",
        "status", "status_reason", "eligible",
    ]]


def get_my_artists(dfm, **kwargs):
    """Convenience: just the eligible-for-radar artists, ranked."""
    profile = build_artist_profile(dfm, **kwargs)
    return profile[profile["eligible"]].reset_index(drop=True)


# ── Optional refresh from Spotify Web API (stale-export catch-up) ──────────

def refresh_with_spotify_top_artists(profile_df, top_artists_items):
    """
    `top_artists_items` = list of Spotify API artist objects (from
    spotify_api.get_top_artists()). Boosts affinity_score slightly for
    artists that show up in the live top-artists call but are missing or
    ranked low in the export-derived profile — catches taste picked up since
    the export was generated. Does not invent history; just nudges rank.
    """
    if not top_artists_items:
        return profile_df

    live_names = {normalise_name(a.get("name", "")) for a in top_artists_items if a.get("name")}
    known_norm = set(profile_df["artist"].apply(normalise_name))

    missing = live_names - known_norm
    if not missing:
        return profile_df

    extra_rows = []
    for a in top_artists_items:
        if normalise_name(a.get("name", "")) in missing:
            extra_rows.append({
                "artist": a["name"], "total_hours": 0.0, "plays": 0,
                "last_played": pd.Timestamp.now(), "hours_last_12m": 0.0,
                "recency_weight": 1.0,
                # small nonzero score so it surfaces but never outranks real history
                "affinity_score": 0.1,
                "affinity_rank": None, "status": "unknown", "status_reason": "",
                "eligible": True,
            })
    if not extra_rows:
        return profile_df

    merged = pd.concat([profile_df, pd.DataFrame(extra_rows)], ignore_index=True)
    merged = merged.sort_values("affinity_score", ascending=False).reset_index(drop=True)
    merged["affinity_rank"] = merged.index + 1
    return merged
