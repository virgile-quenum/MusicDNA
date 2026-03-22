import streamlit as st
import pandas as pd
from collections import Counter
from spotify_auth import api_get, is_authenticated

VIOLET       = "#7C3AED"
VIOLET_LIGHT = "#A78BFA"
GREEN        = "#1DB954"
AMBER        = "#f59e0b"

def _card(content, border=VIOLET):
    st.markdown(
        "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
        "border-left:3px solid " + border + ";border-radius:8px;"
        "padding:14px;margin-bottom:10px;'>" + content + "</div>",
        unsafe_allow_html=True
    )

def _pill(label, color):
    return (
        "<span style='color:" + color + ";font-size:.72em;font-weight:700;"
        "background:" + color + "22;padding:2px 8px;border-radius:10px;"
        "margin-left:6px;'>" + label + "</span>"
    )

def _popularity_label(pop):
    if pop < 30:  return "Underground", GREEN
    if pop < 55:  return "Emerging",    AMBER
    return "Mainstream", "#888"

def _fetch_top_genres(tr_key):
    """Get top genres from top artists via Spotify API."""
    data = api_get("me/top/artists", {"time_range": tr_key, "limit": 20})
    if not data:
        return [], set()
    artists = data.get("items", [])
    known_names = set(a["name"].lower() for a in artists)
    all_genres = []
    for a in artists:
        all_genres.extend(a.get("genres", []))
    top_genres = [g for g, _ in Counter(all_genres).most_common(6)]
    return top_genres, known_names

def _search_artists_by_genre(genre, known_names, known_history, limit=8):
    """Search Spotify for artists in a genre not already in user history."""
    data = api_get("search", {
        "q": "genre:" + genre,
        "type": "artist",
        "limit": 20,
    })
    if not data:
        return []
    results = []
    for a in data.get("artists", {}).get("items", []):
        name = a.get("name", "")
        if name.lower() in known_names:
            continue
        if name.lower() in known_history:
            continue
        results.append({
            "name":       name,
            "popularity": a.get("popularity", 0),
            "genres":     a.get("genres", [])[:2],
            "url":        a.get("external_urls", {}).get("spotify", ""),
            "via_genre":  genre,
        })
        if len(results) >= limit:
            break
    return results

def render(dfm=None):
    st.title("Discovery")
    st.markdown("*Artists you should know - matched to your DNA.*")

    authenticated = is_authenticated()
    known_history = set(dfm["artistName"].str.lower()) if dfm is not None else set()

    tab1, tab2 = st.tabs(["New Discoveries", "Hidden Gems from Your History"])

    # ── Tab 1: genre-based discovery ─────────────────────────────────────────
    with tab1:
        st.markdown("### Artists from your top genres you have never heard")
        st.caption("Based on your most-listened genres - not the deprecated Spotify recommendations endpoint.")

        if not authenticated:
            st.warning("Connect Spotify to enable this feature.")
        else:
            time_range = st.selectbox(
                "Based on your top artists from",
                ["Last 6 months", "Last 4 weeks", "All time"],
                key="tr_discovery"
            )
            tr_map = {"Last 6 months": "medium_term",
                      "Last 4 weeks":  "short_term",
                      "All time":      "long_term"}
            tr_key = tr_map[time_range]

            with st.spinner("Loading your top genres..."):
                top_genres, known_names = _fetch_top_genres(tr_key)

            if not top_genres:
                st.error("Could not load your top genres.")
            else:
                st.markdown(
                    "<div style='margin-bottom:14px;'>"
                    "<span style='color:#555;font-size:.8em;'>Your top genres: </span>"
                    + " ".join(
                        "<span style='color:#A78BFA;font-size:.78em;background:#7C3AED22;"
                        "padding:2px 8px;border-radius:10px;margin-right:4px;'>" + g + "</span>"
                        for g in top_genres
                    )
                    + "</div>",
                    unsafe_allow_html=True
                )

                all_discoveries = []
                with st.spinner("Finding artists you have not heard yet..."):
                    for genre in top_genres[:4]:
                        results = _search_artists_by_genre(genre, known_names, known_history)
                        all_discoveries.extend(results)

                # deduplicate by name
                seen = set()
                unique = []
                for a in all_discoveries:
                    if a["name"].lower() not in seen:
                        seen.add(a["name"].lower())
                        unique.append(a)

                # sort by popularity ascending (underground first)
                unique.sort(key=lambda x: x["popularity"])

                if not unique:
                    st.info("No new artists found - your taste is already very broad.")
                else:
                    st.markdown(
                        "<b style='color:#fff;'>" + str(len(unique)) +
                        " artists you should know:</b>",
                        unsafe_allow_html=True
                    )
                    st.markdown("---")
                    cols = st.columns(2)
                    for i, a in enumerate(unique):
                        pop    = a["popularity"]
                        pl, pc = _popularity_label(pop)
                        genres = " · ".join(a["genres"]) if a["genres"] else ""
                        link   = (
                            "<a href='" + a["url"] + "' target='_blank' "
                            "style='color:" + VIOLET_LIGHT + ";font-size:.75em;'>Open in Spotify ↗</a>"
                        ) if a["url"] else ""
                        with cols[i % 2]:
                            _card(
                                "<div style='display:flex;justify-content:space-between;align-items:flex-start;'>"
                                "<div style='flex:1;'>"
                                "<div style='font-weight:800;color:#fff;font-size:.92em;'>"
                                + a["name"] + _pill(pl, pc) + "</div>"
                                "<div style='color:#555;font-size:.78em;margin-top:3px;'>Via genre: "
                                + a["via_genre"] + "</div>"
                                + ("<div style='color:#444;font-size:.75em;margin-top:2px;'>" + genres + "</div>" if genres else "") +
                                "</div>"
                                "<div style='margin-left:8px;'>" + link + "</div>"
                                "</div>"
                            )

    # ── Tab 2: hidden gems from history ───────────────────────────────────────
    with tab2:
        st.markdown("### Hidden Gems - Artists You Discovered But Never Committed To")
        st.caption("From your own listening history - no Spotify API needed.")

        if dfm is None or dfm.empty:
            st.warning("Upload your Extended History zip to enable this analysis.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                min_plays = st.slider("Max plays to count as uncommitted", 1, 20, 3, key="gem_min")
            with col2:
                top_n = st.slider("Number of gems to show", 10, 50, 20, key="gem_top")

            artist_plays = dfm.groupby("artistName").agg(
                plays=("trackName", "count"),
                hours=("ms", lambda x: x.sum() / 3600000),
                tracks=("trackName", "nunique"),
                last_played=("ts", "max")
            ).reset_index()

            gems = artist_plays[
                (artist_plays["plays"] >= 1) & (artist_plays["plays"] <= min_plays)
            ].sort_values("plays", ascending=False).head(top_n)

            if gems.empty:
                st.info("No hidden gems found with current filters.")
            else:
                st.markdown(
                    "<b style='color:#fff;'>" + str(len(gems)) +
                    " artists you discovered but never committed to:</b>",
                    unsafe_allow_html=True
                )
                st.markdown("---")
                cols = st.columns(2)
                for i, (_, row) in enumerate(gems.iterrows()):
                    last = row["last_played"].strftime("%b %Y") if pd.notna(row["last_played"]) else ""
                    with cols[i % 2]:
                        _card(
                            "<div style='font-weight:700;color:#fff;font-size:.9em;margin-bottom:4px;'>"
                            + str(row["artistName"]) + "</div>"
                            "<div style='color:#555;font-size:.78em;line-height:1.7;'>"
                            + str(int(row["plays"])) + " play" + ("s" if row["plays"] > 1 else "")
                            + " · " + str(int(row["tracks"])) + " track" + ("s" if row["tracks"] > 1 else "")
                            + (" · Last: " + last if last else "")
                            + "</div>",
                            border=AMBER
                        )

            # high skip rate section
            st.markdown("---")
            st.markdown("### Artists You Skipped Most")
            st.caption("High skip rate on few plays - you gave up too fast.")

            if "skipped" in dfm.columns:
                skip_stats = dfm.groupby("artistName").agg(
                    plays=("trackName", "count"),
                    skips=("skipped", "sum")
                ).reset_index()
                skip_stats = skip_stats[skip_stats["plays"] >= 3]
                skip_stats["skip_rate"] = skip_stats["skips"] / skip_stats["plays"]
                skip_stats = skip_stats[
                    (skip_stats["skip_rate"] > 0.5) & (skip_stats["plays"] < 20)
                ].sort_values("skip_rate", ascending=False).head(15)

                if not skip_stats.empty:
                    cols = st.columns(2)
                    for i, (_, row) in enumerate(skip_stats.iterrows()):
                        pct = int(row["skip_rate"] * 100)
                        with cols[i % 2]:
                            _card(
                                "<div style='font-weight:700;color:#fff;font-size:.9em;'>"
                                + str(row["artistName"]) + "</div>"
                                "<div style='color:#888;font-size:.78em;margin-top:4px;'>"
                                + str(pct) + "% skip rate · " + str(int(row["plays"])) + " plays"
                                "</div>",
                                border="#f87171"
                            )
                else:
                    st.info("No high-skip artists found.")
