"""
concert_radar/sources/bandsintown.py — Phase 3.A: Bandsintown public API.

GET https://rest.bandsintown.com/artists/{name}/events?app_id=...&date=start,end

A 404 means Bandsintown doesn't know the artist — not an error, just no
events from this source for them. Results are cached to disk for 24h
(events change: new dates added, shows sell out) and filtered down to the
target region before being handed back.
"""

import os
import time
import urllib.parse

import requests

from concert_radar import cache
from concert_radar.region import event_in_region

BASE_URL = "https://rest.bandsintown.com/artists/{artist}/events"


def _app_id():
    return os.environ.get("BANDSINTOWN_APP_ID", "")


def _fetch(artist_name, date_from, date_to):
    app_id = _app_id()
    if not app_id:
        return {"ok": False, "error": "missing_app_id", "events": []}

    url = BASE_URL.format(artist=urllib.parse.quote(artist_name))
    try:
        resp = requests.get(url, params={
            "app_id": app_id,
            "date": "%s,%s" % (date_from, date_to),
        }, timeout=10)
    except Exception as e:
        return {"ok": False, "error": "request_failed:%s" % type(e).__name__, "events": []}

    if resp.status_code == 404:
        # unknown artist to Bandsintown — log, not an error
        return {"ok": True, "error": None, "events": [], "unknown_artist": True}
    if resp.status_code != 200:
        return {"ok": False, "error": "http_%d" % resp.status_code, "events": []}

    try:
        data = resp.json()
    except Exception:
        return {"ok": False, "error": "bad_json", "events": []}

    if not isinstance(data, list):
        return {"ok": True, "error": None, "events": []}
    return {"ok": True, "error": None, "events": data}


def get_events_for_artist(artist_name, date_from, date_to):
    """
    Cached (24h) Bandsintown lookup for one artist. Returns the raw API
    response dict: {ok, error, events, unknown_artist?}.
    """
    key = "bandsintown:%s:%s:%s" % (artist_name.lower().strip(), date_from, date_to)
    return cache.cached(key, cache.TTL_BANDSINTOWN_EVENTS,
                         lambda: _fetch(artist_name, date_from, date_to))


def _normalise_event(raw, artist_name, region_communes):
    venue = raw.get("venue", {}) or {}
    city = venue.get("city", "")
    postcode = venue.get("region") or ""  # Bandsintown doesn't always give a real postcode
    if not event_in_region(city, postcode, region_communes):
        return None
    offers = raw.get("offers", []) or []
    ticket_url = offers[0].get("url") if offers else raw.get("url", "")
    return {
        "date": (raw.get("datetime") or "")[:10],
        "headliner": artist_name,
        "lineup_raw": raw.get("lineup") or [artist_name],
        "venue": venue.get("name", ""),
        "city": city,
        "url": raw.get("url", ""),
        "ticket_url": ticket_url,
        "price": None,       # Bandsintown rarely gives price without a paid tier
        "status": "unknown",
        "source": "bandsintown",
    }


def collect_events(artist_names, date_from, date_to, region_communes,
                    rate_limit_sleep=0.1):
    """
    Query Bandsintown for every artist in `artist_names` (already the
    combined "my artists" + top similar list). Returns
    (events, stats) where stats = {queried, unknown_artist, events_found,
    errors: [...]}
    """
    events = []
    stats = {"queried": 0, "unknown_artist": 0, "events_found": 0, "errors": []}

    if not _app_id():
        stats["errors"].append("missing_app_id")
        return events, stats

    for artist in artist_names:
        stats["queried"] += 1
        result = get_events_for_artist(artist, date_from, date_to)
        if not result.get("ok"):
            stats["errors"].append("%s: %s" % (artist, result.get("error")))
            continue
        if result.get("unknown_artist"):
            stats["unknown_artist"] += 1
            continue
        for raw_ev in result.get("events", []):
            norm = _normalise_event(raw_ev, artist, region_communes)
            if norm:
                events.append(norm)
                stats["events_found"] += 1
        time.sleep(rate_limit_sleep)

    return events, stats
