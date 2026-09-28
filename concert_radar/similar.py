"""
concert_radar/similar.py — Phase 2: artists similar to the ones the user
actually listens to, so the radar can also surface "close to your taste"
shows and not just gigs by artists already in their library.

Reuses lastfm.py's underlying Last.fm call (not its st.session_state cache,
which only lives for one Streamlit session) and layers a 30-day on-disk
cache on top, per spec, via concert_radar.cache.
"""

import lastfm
from concert_radar import cache
from concert_radar.profile import normalise_name

TOP_SEED_COUNT   = 30
SIMILAR_PER_SEED = 20


def _fetch_similar_raw(artist_name):
    """Bypasses lastfm.py's session-state cache; talks to Last.fm directly
    via its shared `_call` helper so results can be cached to disk instead."""
    data = lastfm._call("artist.getsimilar", {
        "artist": artist_name, "autocorrect": 1, "limit": SIMILAR_PER_SEED,
    })
    similar = []
    if data and "similarartists" in data:
        for a in data["similarartists"].get("artist", []):
            similar.append({
                "name":  a.get("name", ""),
                "match": float(a.get("match", 0)),
                "url":   a.get("url", ""),
            })
    return similar


def get_similar_cached(artist_name):
    """30-day disk-cached Last.fm similar-artists lookup."""
    key = "lastfm_similar:" + normalise_name(artist_name)
    return cache.cached(key, cache.TTL_LASTFM_SIMILAR, lambda: _fetch_similar_raw(artist_name))


def build_similar_artists(my_artists_df, known_hours_threshold=0.5,
                           top_seed_count=TOP_SEED_COUNT):
    """
    my_artists_df: output of profile.build_artist_profile (needs columns
    artist, affinity_score, total_hours), already filtered to eligible rows
    if you want only real "my artists" as seeds.

    Returns a DataFrame: similar_artist, parent_artist, lastfm_match,
    parent_affinity, similar_score — one row per (parent, similar) pair,
    deduped by keeping the highest-scoring parent for each similar artist,
    and excluding similar artists the user already listens to for
    `known_hours_threshold` hours or more.
    """
    import pandas as pd

    if my_artists_df is None or my_artists_df.empty:
        return pd.DataFrame(columns=[
            "similar_artist", "parent_artist", "lastfm_match",
            "parent_affinity", "similar_score",
        ])

    known_hours = dict(zip(
        my_artists_df["artist"].apply(normalise_name),
        my_artists_df["total_hours"],
    ))

    seeds = my_artists_df.sort_values("affinity_score", ascending=False).head(top_seed_count)

    rows = []
    for _, seed in seeds.iterrows():
        parent = seed["artist"]
        parent_affinity = seed["affinity_score"]
        for s in get_similar_cached(parent) or []:
            norm = normalise_name(s["name"])
            if not norm:
                continue
            if known_hours.get(norm, 0.0) >= known_hours_threshold:
                continue  # already a known artist to the user — not a discovery
            rows.append({
                "similar_artist":   s["name"],
                "parent_artist":    parent,
                "lastfm_match":     s["match"],
                "parent_affinity":  parent_affinity,
                "similar_score":    s["match"] * parent_affinity,
            })

    if not rows:
        return pd.DataFrame(columns=[
            "similar_artist", "parent_artist", "lastfm_match",
            "parent_affinity", "similar_score",
        ])

    df = pd.DataFrame(rows)
    # one row per similar artist: keep the highest-scoring parent link
    df = df.sort_values("similar_score", ascending=False)
    df = df.drop_duplicates(subset="similar_artist", keep="first").reset_index(drop=True)
    return df
