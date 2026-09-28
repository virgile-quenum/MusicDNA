"""
concert_radar/pipeline.py — wires profile.py + similar.py + sources/* +
matching.py together into the three MVP tabs Streamlit renders.

This is the one entry point page.py calls; everything else in this package
is a building block it composes.
"""

import datetime

import pandas as pd

import lastfm
from concert_radar import profile as profile_mod
from concert_radar import similar as similar_mod
from concert_radar import matching
from concert_radar import region as region_mod
from concert_radar.sources import bandsintown, songkick


def _genre_fits(performer_name, other_names):
    """Best-effort genre check for the homonym-risk rule: do this performer's
    Last.fm tags overlap with the rest of the line-up's? Permissive by
    design — if we don't have tags for either side, we don't block a match
    on it; this only helps catch a clean genre MISMATCH like the Noname/
    electro-night trap, not a definitive genre judgement."""
    if not lastfm.is_available():
        return True
    try:
        perf_tags = set(lastfm.get_artist_info(performer_name).get("tags", []))
    except Exception:
        return True
    if not perf_tags or not other_names:
        return True
    for other in other_names:
        try:
            other_tags = set(lastfm.get_artist_info(other).get("tags", []))
        except Exception:
            continue
        if other_tags and perf_tags & other_tags:
            return True
    # Have tags on both sides, zero overlap anywhere → likely mismatch
    any_other_has_tags = False
    for other in other_names:
        try:
            if lastfm.get_artist_info(other).get("tags"):
                any_other_has_tags = True
                break
        except Exception:
            continue
    return not any_other_has_tags


def run_pipeline(dfm, region_name="Île-de-France", months_ahead=4,
                  top_rank_limit=profile_mod.DEFAULT_TOP_RANK_LIMIT,
                  min_hours=profile_mod.DEFAULT_MIN_HOURS,
                  top_similar_count=100, use_songkick=None):
    """
    Returns a dict:
      {
        "my_artists": DataFrame,      # tab 1
        "close_to_taste": DataFrame,  # tab 2
        "to_verify": DataFrame,       # tab 3
        "kpis": {events_collected, sources_used, sources_failed, matches_per_tab},
        "artist_profile": DataFrame,  # full affinity table, for debugging/export
      }
    """
    today = datetime.date.today()
    date_from = today.isoformat()
    date_to = (today + datetime.timedelta(days=30 * months_ahead)).isoformat()

    # ── Phase 1: listener profile ────────────────────────────────────────
    artist_profile = profile_mod.build_artist_profile(
        dfm, top_rank_limit=top_rank_limit, min_hours=min_hours
    )
    my_artists_profile = artist_profile[artist_profile["eligible"]].reset_index(drop=True)

    # ── Phase 2: similar artists ──────────────────────────────────────────
    similar_df = similar_mod.build_similar_artists(my_artists_profile)
    similar_names = similar_df["similar_artist"].head(top_similar_count).tolist()

    # ── Phase 3: event collection ──────────────────────────────────────────
    region_communes = region_mod.load_region_communes()
    query_artists = my_artists_profile["artist"].tolist() + similar_names

    bit_events, bit_stats = bandsintown.collect_events(
        query_artists, date_from, date_to, region_communes
    )

    sk_enabled = songkick.is_enabled() if use_songkick is None else use_songkick
    sk_events, sk_stats = ([], {"enabled": False}) if not sk_enabled else songkick.collect_events(
        date_from=date_from, date_to=date_to
    )

    sources_used = []
    sources_failed = []
    if bit_stats.get("errors") and not bit_stats.get("events_found"):
        sources_failed.append({"source": "bandsintown", "errors": bit_stats["errors"]})
    else:
        sources_used.append("bandsintown")
    if sk_stats.get("enabled"):
        if sk_stats.get("errors"):
            sources_failed.append({"source": "songkick", "errors": sk_stats["errors"]})
        else:
            sources_used.append("songkick")

    # ── Matching ─────────────────────────────────────────────────────────
    aliases = matching.load_aliases()
    my_hours = dict(zip(
        my_artists_profile["artist"].apply(matching.normalise_name),
        my_artists_profile["total_hours"],
    ))
    my_norm = set(my_hours.keys())
    similar_lookup = {
        matching.normalise_name(row["similar_artist"]): row
        for _, row in similar_df.iterrows()
    }

    raw_events = list(bit_events)  # already one-performer-per-event (Bandsintown query artist)

    # Songkick events carry a free-text multi-performer lineup; expand + match each
    for ev in sk_events:
        performers = matching.split_lineup(ev.get("lineup_raw", ""))
        for i, performer in enumerate(performers):
            row = dict(ev)
            row["headliner"] = performer
            row["is_headliner"] = (i == 0)
            row["lineup_raw_full"] = ev.get("lineup_raw", "")
            raw_events.append(row)

    my_rows, similar_rows, review_rows = [], [], []

    for ev in raw_events:
        performer_raw = ev.get("headliner", "")
        norm = matching.resolve_alias(performer_raw, aliases)
        performers_others = [p for p in matching.split_lineup(ev.get("lineup_raw_full", performer_raw))
                              if matching.normalise_name(p) != norm]

        is_my_artist = norm in my_norm
        is_similar = (not is_my_artist) and norm in similar_lookup

        if not is_my_artist and not is_similar:
            continue  # not a match to anything we care about

        genre_fits = _genre_fits(performer_raw, performers_others)
        user_hours = my_hours.get(norm, 0.0)

        confidence, reasons = matching.classify_match(
            performer_raw=performer_raw,
            event_title=ev.get("lineup_raw_full", performer_raw),
            venue_name=ev.get("venue", ""),
            genre_fits=genre_fits,
            sources_count=len(ev.get("sources", [ev.get("source")])),
            lineup_consistent=True,  # single-source consistency is source-specific; conservative default
            user_hours=user_hours,
            is_headliner=ev.get("is_headliner", True),
        )

        row = {
            "date": ev.get("date"),
            "artist": performer_raw,
            "venue": ev.get("venue"),
            "city": ev.get("city"),
            "price": ev.get("price") or "n.c.",
            "status": ev.get("status", "unknown"),
            "ticket_url": ev.get("ticket_url") or ev.get("url", ""),
            "my_hours": round(user_hours, 1),
            "sources": ", ".join(ev.get("sources", [ev.get("source", "")])),
        }

        if confidence == "review":
            row["reason"] = ", ".join(reasons)
            review_rows.append(row)
        elif is_my_artist:
            my_rows.append(row)
        else:
            row["close_to"] = similar_lookup[norm]["parent_artist"]
            similar_rows.append(row)

    def _to_df(rows, extra_cols=None):
        cols = ["date", "artist", "venue", "city", "price", "status",
                "ticket_url", "my_hours", "sources"] + (extra_cols or [])
        if not rows:
            return pd.DataFrame(columns=cols)
        df = pd.DataFrame(rows)
        return df[[c for c in cols if c in df.columns]]

    my_df       = _to_df(matching.dedupe_events(my_rows))
    similar_df_ = _to_df(matching.dedupe_events(similar_rows), extra_cols=["close_to"])
    review_df   = _to_df(matching.dedupe_events(review_rows), extra_cols=["reason"])

    # residency grouping on the affinity-sorted "my artists" tab
    my_grouped = matching.group_residencies(my_df.to_dict("records")) if not my_df.empty else []
    my_df = pd.DataFrame(my_grouped) if my_grouped else my_df

    # sort my_artists by affinity (spec: not by date)
    if not my_df.empty:
        affinity_by_artist = dict(zip(
            my_artists_profile["artist"].apply(matching.normalise_name),
            my_artists_profile["affinity_score"],
        ))
        my_df["_affinity"] = my_df["artist"].apply(
            lambda a: affinity_by_artist.get(matching.normalise_name(a), 0)
        )
        my_df = my_df.sort_values("_affinity", ascending=False).drop(columns="_affinity")

    kpis = {
        "events_collected": len(bit_events) + len(sk_events),
        "sources_used": sources_used,
        "sources_failed": sources_failed,
        "matches_per_tab": {
            "my_artists": len(my_df), "close_to_taste": len(similar_df_), "to_verify": len(review_df),
        },
    }

    return {
        "my_artists": my_df,
        "close_to_taste": similar_df_,
        "to_verify": review_df,
        "kpis": kpis,
        "artist_profile": artist_profile,
    }
