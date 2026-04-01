"""
lastfm.py — Last.fm API integration for MusicDNA
Provides artist enrichment, popularity scoring, catalogue coverage and similar artists.
All results cached in st.session_state to avoid redundant API calls.
"""

import os
import time
import requests
import streamlit as st
import pandas as pd

LASTFM_BASE = "https://ws.audioscrobbler.com/2.0/"

# ── Base call ─────────────────────────────────────────────────────────────────

def _get_key():
    key = os.environ.get("LASTFM_API_KEY", "")
    if not key:
        return None
    return key

def _call(method, params, retries=2):
    key = _get_key()
    if not key:
        return None
    params.update({
        "method":  method,
        "api_key": key,
        "format":  "json",
    })
    for attempt in range(retries):
        try:
            r = requests.get(LASTFM_BASE, params=params, timeout=8)
            if r.status_code == 200:
                data = r.json()
                if "error" not in data:
                    return data
            time.sleep(0.3)
        except Exception:
            time.sleep(0.5)
    return None

def is_available():
    """Check if Last.fm API key is configured."""
    return bool(_get_key())

# ── Artist info ───────────────────────────────────────────────────────────────

def get_artist_info(artist_name):
    """
    Returns listeners, playcount, tags for an artist.
    Cached in session state.
    """
    cache_key = "lfm_art_" + artist_name.lower().strip()[:50]
    if cache_key in st.session_state:
        return st.session_state[cache_key]

    data = _call("artist.getinfo", {"artist": artist_name, "autocorrect": 1})
    result = {"name": artist_name, "listeners": 0, "playcount": 0, "tags": []}

    if data and "artist" in data:
        a     = data["artist"]
        stats = a.get("stats", {})
        tags  = a.get("tags", {}).get("tag", [])
        result = {
            "name":      a.get("name", artist_name),
            "listeners": int(stats.get("listeners", 0)),
            "playcount": int(stats.get("playcount", 0)),
            "tags":      [t["name"].lower() for t in tags[:5]] if tags else [],
            "url":       a.get("url", ""),
        }

    st.session_state[cache_key] = result
    return result

def get_artist_top_tracks(artist_name, limit=50):
    """
    Returns top tracks for an artist — used for catalogue coverage calculation.
    Cached in session state.
    """
    cache_key = "lfm_toptracks_" + artist_name.lower().strip()[:50]
    if cache_key in st.session_state:
        return st.session_state[cache_key]

    data = _call("artist.gettoptracks", {
        "artist":     artist_name,
        "autocorrect": 1,
        "limit":      limit,
    })
    tracks = []
    if data and "toptracks" in data:
        for t in data["toptracks"].get("track", []):
            tracks.append({
                "name":      t.get("name", ""),
                "playcount": int(t.get("playcount", 0)),
                "listeners": int(t.get("listeners", 0)),
            })

    st.session_state[cache_key] = tracks
    return tracks

def get_similar_artists(artist_name, limit=10):
    """
    Returns similar artists — used for The Gap recommendations.
    Cached in session state.
    """
    cache_key = "lfm_similar_" + artist_name.lower().strip()[:50]
    if cache_key in st.session_state:
        return st.session_state[cache_key]

    data = _call("artist.getsimilar", {
        "artist":     artist_name,
        "autocorrect": 1,
        "limit":      limit,
    })
    similar = []
    if data and "similarartists" in data:
        for a in data["similarartists"].get("artist", []):
            similar.append({
                "name":  a.get("name", ""),
                "match": float(a.get("match", 0)),
                "url":   a.get("url", ""),
            })

    st.session_state[cache_key] = similar
    return similar

# ── Batch enrichment ──────────────────────────────────────────────────────────

def enrich_artists(artist_list, progress=True):
    """
    Fetch Last.fm info for a list of artists.
    Returns dict: artist_name -> info dict.
    Shows a progress bar if progress=True.
    Rate limited to avoid hitting Last.fm limits.
    """
    results = {}
    already_cached = [a for a in artist_list
                      if "lfm_art_" + a.lower().strip()[:50] in st.session_state]
    to_fetch = [a for a in artist_list
                if "lfm_art_" + a.lower().strip()[:50] not in st.session_state]

    # Load cached
    for a in already_cached:
        results[a] = st.session_state["lfm_art_" + a.lower().strip()[:50]]

    if not to_fetch:
        return results

    if progress and to_fetch:
        bar = st.progress(0, text="Enriching artists via Last.fm...")

    for i, artist in enumerate(to_fetch):
        results[artist] = get_artist_info(artist)
        time.sleep(0.15)  # ~6 req/sec — well within Last.fm limits
        if progress and to_fetch:
            bar.progress((i + 1) / len(to_fetch),
                         text=f"Last.fm — {artist[:30]}...")

    if progress and to_fetch:
        bar.empty()

    return results

# ── Popularity scoring ────────────────────────────────────────────────────────

def popularity_score(listeners):
    """
    Convert Last.fm listener count to a 0-100 score.
    Benchmarks based on Last.fm distribution:
    - <10K   → niche / underground
    - 10K-100K → emerging
    - 100K-1M  → known
    - 1M-5M    → mainstream
    - 5M+      → global mainstream
    """
    if listeners <= 0:       return 0
    if listeners < 10_000:   return int(listeners / 10_000 * 20)        # 0-20
    if listeners < 100_000:  return 20 + int((listeners - 10_000) / 90_000 * 20)  # 20-40
    if listeners < 1_000_000: return 40 + int((listeners - 100_000) / 900_000 * 30) # 40-70
    if listeners < 5_000_000: return 70 + int((listeners - 1_000_000) / 4_000_000 * 20) # 70-90
    return min(90 + int((listeners - 5_000_000) / 5_000_000 * 10), 100) # 90-100

def popularity_label(score):
    """Returns (label, color) for a popularity score 0-100."""
    if score < 20:  return "Underground",  "#1DB954"
    if score < 40:  return "Emerging",     "#60a5fa"
    if score < 60:  return "Known",        "#A78BFA"
    if score < 80:  return "Mainstream",   "#f59e0b"
    return "Global",      "#f87171"

# ── Catalogue coverage ────────────────────────────────────────────────────────

def catalogue_coverage(artist_name, user_tracks_played):
    """
    Calculate what % of an artist's known catalogue the user has heard.
    user_tracks_played = set of track names (lowercase) the user has played.

    Returns dict with coverage_pct, tracks_known, tracks_total.
    """
    top_tracks = get_artist_top_tracks(artist_name, limit=50)
    if not top_tracks:
        return {"coverage_pct": 0, "tracks_known": 0, "tracks_total": 0}

    known = sum(
        1 for t in top_tracks
        if t["name"].lower().strip() in user_tracks_played
    )
    total = len(top_tracks)
    return {
        "coverage_pct": round(known / total * 100) if total > 0 else 0,
        "tracks_known": known,
        "tracks_total": total,
    }

# ── Mainstream proximity score ────────────────────────────────────────────────

def compute_mainstream_score(dfm, top_n=30):
    """
    Compute weighted mainstream proximity score for a user.
    Uses top N artists by hours, weighted by listening hours.

    Returns dict with:
    - mainstream_score: 0-100
    - avg_listeners: average Last.fm listeners across top artists
    - artist_breakdown: list of (artist, hours, listeners, pop_score)
    """
    if not is_available():
        return {"mainstream_score": 50, "avg_listeners": 0, "artist_breakdown": []}

    # Top N artists by hours
    artist_hours = (
        dfm.groupby("artistName")["ms"].sum() / 3600000
    ).nlargest(top_n)

    artist_list  = artist_hours.index.tolist()
    enriched     = enrich_artists(artist_list, progress=False)

    total_hours  = 0
    weighted_sum = 0
    breakdown    = []

    for artist, hours in artist_hours.items():
        info      = enriched.get(artist, {})
        listeners = info.get("listeners", 0)
        pop       = popularity_score(listeners)
        weighted_sum += pop * hours
        total_hours  += hours
        breakdown.append({
            "artist":    artist,
            "hours":     round(hours, 1),
            "listeners": listeners,
            "pop_score": pop,
        })

    mainstream_score = round(weighted_sum / total_hours) if total_hours > 0 else 50
    avg_listeners    = int(sum(b["listeners"] for b in breakdown) / max(len(breakdown), 1))

    return {
        "mainstream_score": mainstream_score,
        "avg_listeners":    avg_listeners,
        "artist_breakdown": sorted(breakdown, key=lambda x: -x["hours"]),
    }

# ── The Gap — must-listen recommendations ─────────────────────────────────────

def get_the_gap(dfm, top_seed_artists=5, limit_per_seed=8):
    """
    Find artists similar to user's top artists that they've never listened to.
    Uses Last.fm similar artists.

    Returns list of dicts: name, listeners, pop_score, via (seed artist), url.
    """
    if not is_available():
        return []

    # Top seed artists by hours (excluding kids)
    kids_kw = ['bébé','baby','lullaby','titounis','mancebo','bernardo','celesti',
               'mclaughlin','moons','kiboomers','teddy','wonderland','comptines',
               'petit ours','ainsi font','percussioney','batukem','tukada',
               'música para bebés','alain royer','miracle tones']
    def is_kids(n): return any(k in n.lower() for k in kids_kw)

    df_c = dfm[~dfm["artistName"].apply(is_kids)]
    known_artists = set(df_c["artistName"].str.lower().str.strip())

    top_seeds = (
        df_c.groupby("artistName")["ms"].sum()
        .nlargest(top_seed_artists).index.tolist()
    )

    seen     = set()
    results  = []

    for seed in top_seeds:
        similar = get_similar_artists(seed, limit=limit_per_seed)
        for s in similar:
            name_lower = s["name"].lower().strip()
            if name_lower in known_artists: continue
            if name_lower in seen:          continue
            seen.add(name_lower)

            info = get_artist_info(s["name"])
            pop  = popularity_score(info.get("listeners", 0))
            results.append({
                "name":      s["name"],
                "listeners": info.get("listeners", 0),
                "pop_score": pop,
                "tags":      info.get("tags", []),
                "via":       seed,
                "url":       info.get("url", s.get("url", "")),
            })
        time.sleep(0.1)

    return sorted(results, key=lambda x: -x["listeners"])

# ── Depth score with catalogue coverage ───────────────────────────────────────

def compute_depth_with_coverage(dfm, top_n=10):
    """
    Compute a proper depth score using Last.fm catalogue coverage.
    For top N artists: what % of their known tracks has the user played?

    Returns dict with:
    - depth_score: 0-20
    - coverage_details: list per artist
    """
    if not is_available():
        return {"depth_score": None, "coverage_details": []}

    kids_kw = ['bébé','baby','lullaby','titounis','mancebo','bernardo','celesti',
               'mclaughlin','moons','kiboomers','teddy','wonderland','comptines',
               'petit ours','ainsi font','percussioney','batukem','tukada',
               'música para bebés','alain royer','miracle tones']
    def is_kids(n): return any(k in n.lower() for k in kids_kw)
    df_c = dfm[~dfm["artistName"].apply(is_kids)]

    top_artists = (
        df_c.groupby("artistName")["ms"].sum()
        .nlargest(top_n).index.tolist()
    )

    user_tracks_played = set(df_c["trackName"].str.lower().str.strip())
    details    = []
    coverages  = []

    for artist in top_artists:
        cov = catalogue_coverage(artist, user_tracks_played)
        details.append({
            "artist":       artist,
            "coverage_pct": cov["coverage_pct"],
            "tracks_known": cov["tracks_known"],
            "tracks_total": cov["tracks_total"],
        })
        coverages.append(cov["coverage_pct"])
        time.sleep(0.1)

    avg_coverage = sum(coverages) / max(len(coverages), 1)
    # Benchmark: 30% coverage = good, 60%+ = exceptional
    depth_score  = round(min(avg_coverage / 60, 1.0) * 20)

    return {
        "depth_score":      depth_score,
        "avg_coverage_pct": round(avg_coverage, 1),
        "coverage_details": sorted(details, key=lambda x: -x["coverage_pct"]),
    }
