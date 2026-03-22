import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from collections import Counter
from spotify_auth import api_get, is_authenticated

VIOLET       = "#7C3AED"
VIOLET_LIGHT = "#A78BFA"
GREEN        = "#1DB954"
AMBER        = "#f59e0b"
RED          = "#f87171"

GENRE_COLORS = [
    VIOLET_LIGHT, GREEN, AMBER, RED, "#60a5fa",
    "#34d399", "#f472b6", "#fb923c", "#a3e635", "#38bdf8",
]

def _fetch_artist_genres(artist_names):
    """Search Spotify for each artist name and return their genres."""
    genre_map = {}
    for name in artist_names:
        if not name or name in genre_map:
            continue
        data = api_get("search", {"q": name, "type": "artist", "limit": 1})
        if not data:
            continue
        items = data.get("artists", {}).get("items", [])
        if items:
            genres = items[0].get("genres", [])
            genre_map[name] = genres[:3]  # top 3 genres per artist
    return genre_map

def _normalize_genre(genre):
    """Collapse sub-genres into broader families."""
    g = genre.lower()
    if any(k in g for k in ["afro", "afrobeat", "afropop", "afrotrap"]):
        return "Afrobeats"
    if any(k in g for k in ["hip hop", "hip-hop", "rap", "trap", "drill"]):
        return "Hip-Hop / Rap"
    if any(k in g for k in ["r&b", "rnb", "soul", "funk"]):
        return "R&B / Soul"
    if any(k in g for k in ["jazz"]):
        return "Jazz"
    if any(k in g for k in ["reggae", "dancehall", "reggaeton", "kompa", "zouk", "soca"]):
        return "Caribbean / Reggae"
    if any(k in g for k in ["pop"]):
        return "Pop"
    if any(k in g for k in ["rock", "indie", "alternative", "punk", "metal"]):
        return "Rock / Indie"
    if any(k in g for k in ["electronic", "dance", "house", "techno", "edm", "club"]):
        return "Electronic / Dance"
    if any(k in g for k in ["classical", "orchestra", "piano", "opera"]):
        return "Classical"
    if any(k in g for k in ["world", "latin", "bossa", "samba", "cumbia", "salsa", "bachata"]):
        return "World / Latin"
    if any(k in g for k in ["blues", "country", "folk"]):
        return "Blues / Country / Folk"
    if any(k in g for k in ["children", "kids", "nursery", "lullaby"]):
        return "Children's"
    return "Other"

def _yearly_genre_profile(dfm, genre_map):
    """Build per-year genre distribution from history + genre_map."""
    rows = []
    for year, grp in dfm.groupby("year"):
        top_artists = (
            grp.groupby("artistName")["ms"]
            .sum()
            .sort_values(ascending=False)
            .head(20)
            .index.tolist()
        )
        genre_counts = Counter()
        for artist in top_artists:
            raw_genres = genre_map.get(artist, [])
            for g in raw_genres:
                normalized = _normalize_genre(g)
                if normalized != "Other" and normalized != "Children's":
                    genre_counts[normalized] += 1
        if genre_counts:
            total = sum(genre_counts.values())
            for genre, count in genre_counts.most_common(5):
                rows.append({
                    "year":  year,
                    "genre": genre,
                    "pct":   round(count / total * 100, 1),
                })
    return pd.DataFrame(rows)

def render(dfm):
    st.markdown(
        "<span style='color:" + VIOLET_LIGHT + ";font-size:.75em;font-weight:700;"
        "text-transform:uppercase;letter-spacing:.1em;'>Full DNA — File + Spotify</span>",
        unsafe_allow_html=True
    )
    st.title("Genre Profile")
    st.caption("How your musical genres evolved year by year — built from your top artists per year.")

    if not is_authenticated():
        st.warning("Connect Spotify to unlock this analysis.")
        return
    if dfm is None or dfm.empty:
        st.warning("Upload your Extended History zip to enable this analysis.")
        return

    # get top artists across all years (limit API calls)
    top_artists_all = (
        dfm.groupby("artistName")["ms"]
        .sum()
        .sort_values(ascending=False)
        .head(80)
        .index.tolist()
    )

    with st.spinner("Fetching genre data from Spotify (" + str(len(top_artists_all)) + " artists)..."):
        genre_map = _fetch_artist_genres(top_artists_all)

    if not genre_map:
        st.warning("Could not load genre data from Spotify.")
        return

    yearly_df = _yearly_genre_profile(dfm, genre_map)

    if yearly_df.empty:
        st.info("Not enough genre data to build a profile.")
        return

    tab1, tab2, tab3 = st.tabs(["Evolution Over Time", "Your Genre DNA", "Dominant Genre Per Year"])

    # ── Tab 1: stacked area chart ─────────────────────────────────────────────
    with tab1:
        st.markdown("### Genre evolution — year by year")
        st.caption("% share of each genre among your top 20 artists per year.")

        genres_all = yearly_df["genre"].unique().tolist()
        pivot = yearly_df.pivot_table(
            index="year", columns="genre", values="pct", aggfunc="sum"
        ).fillna(0).reset_index()

        fig = go.Figure()
        for i, genre in enumerate(genres_all):
            if genre not in pivot.columns:
                continue
            color = GENRE_COLORS[i % len(GENRE_COLORS)]
            fig.add_trace(go.Scatter(
                x=pivot["year"],
                y=pivot[genre],
                mode="lines+markers",
                name=genre,
                line=dict(color=color, width=2),
                marker=dict(size=5),
                stackgroup="one",
                fillcolor=color.replace("#", "") and color + "55",
            ))

        fig.update_layout(
            paper_bgcolor="#050505",
            plot_bgcolor="#0f0f0f",
            font=dict(color="#888", size=12),
            legend=dict(bgcolor="#0f0f0f", bordercolor="#1e1e1e", borderwidth=1,
                        orientation="h", yanchor="bottom", y=1.02),
            xaxis=dict(gridcolor="#1e1e1e", tickformat="d"),
            yaxis=dict(gridcolor="#1e1e1e", title="Share (%)"),
            margin=dict(l=0, r=0, t=40, b=0),
            height=420,
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Tab 2: all-time genre DNA ─────────────────────────────────────────────
    with tab2:
        st.markdown("### Your all-time genre DNA")
        st.caption("Weighted by listening hours — not just play count.")

        # build all-time genre hours
        genre_hours = Counter()
        for artist, genres in genre_map.items():
            artist_hours = dfm[dfm["artistName"] == artist]["ms"].sum() / 3600000
            for g in genres:
                normalized = _normalize_genre(g)
                if normalized not in ("Other", "Children's"):
                    genre_hours[normalized] += artist_hours

        if not genre_hours:
            st.info("Not enough data.")
        else:
            total_h = sum(genre_hours.values())
            top_genres = genre_hours.most_common(10)

            bars_html = ""
            for i, (genre, hours) in enumerate(top_genres):
                pct   = int(hours / total_h * 100)
                color = GENRE_COLORS[i % len(GENRE_COLORS)]
                bars_html += (
                    "<div style='margin-bottom:12px;'>"
                    "<div style='display:flex;justify-content:space-between;margin-bottom:3px;'>"
                    "<span style='font-size:.85em;color:#ccc;font-weight:500;'>" + genre + "</span>"
                    "<span style='font-size:.85em;color:" + color + ";font-weight:700;'>"
                    + str(int(hours)) + "h (" + str(pct) + "%)</span>"
                    "</div>"
                    "<div style='background:#1e1e1e;border-radius:4px;height:8px;'>"
                    "<div style='background:" + color + ";width:" + str(pct) + "%;"
                    "height:8px;border-radius:4px;'></div>"
                    "</div>"
                    "</div>"
                )

            st.markdown(
                "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
                "border-radius:12px;padding:20px;'>" + bars_html + "</div>",
                unsafe_allow_html=True
            )

            # taste summary
            dominant = top_genres[0][0] if top_genres else "—"
            second   = top_genres[1][0] if len(top_genres) > 1 else "—"
            st.markdown(
                "<div style='background:#0f0f0f;border:1px solid " + VIOLET + "44;"
                "border-radius:12px;padding:16px;margin-top:16px;'>"
                "<div style='color:#555;font-size:.82em;line-height:1.8;'>"
                "Your listening is dominated by <b style='color:#fff;'>" + dominant + "</b> "
                "and <b style='color:#fff;'>" + second + "</b>. "
                "That's not a playlist — that's a personality."
                "</div>"
                "</div>",
                unsafe_allow_html=True
            )

    # ── Tab 3: dominant genre per year ────────────────────────────────────────
    with tab3:
        st.markdown("### #1 genre per year")

        top_per_year = (
            yearly_df.sort_values("pct", ascending=False)
            .groupby("year")
            .first()
            .reset_index()
            .sort_values("year", ascending=False)
        )

        for _, row in top_per_year.iterrows():
            idx   = list(genres_all).index(row["genre"]) if row["genre"] in genres_all else 0
            color = GENRE_COLORS[idx % len(GENRE_COLORS)]
            st.markdown(
                "<div style='display:flex;align-items:center;gap:16px;"
                "padding:10px 16px;border:1px solid #1e1e1e;"
                "border-radius:8px;margin-bottom:6px;background:#0f0f0f;'>"
                "<span style='font-size:.85em;color:#555;min-width:36px;'>"
                + str(int(row["year"])) + "</span>"
                "<span style='font-weight:700;color:#fff;flex:1;'>" + row["genre"] + "</span>"
                "<span style='color:" + color + ";font-size:.8em;font-weight:700;"
                "background:" + color + "22;padding:2px 10px;border-radius:10px;'>"
                + str(row["pct"]) + "%</span>"
                "</div>",
                unsafe_allow_html=True
            )
