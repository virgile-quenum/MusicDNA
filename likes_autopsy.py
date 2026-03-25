import streamlit as st
import pandas as pd
import plotly.graph_objects as go

VIOLET       = "#7C3AED"
VIOLET_LIGHT = "#A78BFA"
GREEN        = "#1DB954"
AMBER        = "#f59e0b"
RED          = "#f87171"

def _confidence(liked_count, plays, total_plays):
    likes_signal = min(liked_count / 10, 1.0)
    plays_signal = min(plays / 50, 1.0) if total_plays > 0 else 0
    volume_bonus = min(total_plays / 500, 0.2)
    return round((likes_signal * 0.5 + plays_signal * 0.5 + volume_bonus), 3)

def render(dfm, lib, dfd=None):
    st.title("💔 Likes Autopsy")
    st.markdown("*What you **think** you love vs. what you **actually** play.*")

    if isinstance(lib, dict):
        liked = lib.get("tracks", [])
    elif isinstance(lib, list):
        liked = lib
    else:
        liked = []

    if not liked:
        st.warning("No likes data — upload your standard export zip alongside the Extended History.")
        return

    liked_df = pd.DataFrame(liked)
    if "track" not in liked_df.columns and "trackName" in liked_df.columns:
        liked_df = liked_df.rename(columns={"trackName": "track", "artistName": "artist"})
    if "artist" not in liked_df.columns:
        liked_df["artist"] = ""
    if "track" not in liked_df.columns:
        liked_df["track"] = ""

    liked_df["artist"] = liked_df["artist"].str.lower().str.strip()
    liked_df["track"]  = liked_df["track"].str.lower().str.strip()

    # ── Combine dfm + dfd for ghost artist detection ──────────────────────
    df_all = dfm.copy()
    if dfd is not None and not dfd.empty:
        df_all = pd.concat([dfm, dfd], ignore_index=True)

    played_tracks  = set(df_all["trackName"].str.lower().str.strip())
    total_plays    = len(dfm)

    liked_catalogue = liked_df.groupby("artist").size().reset_index(name="liked_count")

    played_artists = dfm.groupby("artistName").agg(
        plays=("ms", "count"),
        hours=("ms", lambda x: round(x.sum() / 3600000, 2))
    ).reset_index()
    played_artists["artistName"] = played_artists["artistName"].str.lower().str.strip()

    # played_all for ghost detection (includes dfd)
    played_artists_all = df_all.groupby("artistName").agg(
        plays_all=("ms", "count")
    ).reset_index()
    played_artists_all["artistName"] = played_artists_all["artistName"].str.lower().str.strip()

    merged = liked_catalogue.merge(
        played_artists.rename(columns={"artistName": "artist"}),
        on="artist", how="outer"
    ).fillna(0)
    merged["liked_count"] = merged["liked_count"].astype(int)
    merged["plays"]       = merged["plays"].astype(int)
    merged["hours"]       = merged["hours"].round(2)

    # merge plays_all for ghost detection
    merged = merged.merge(
        played_artists_all.rename(columns={"artistName": "artist", "plays_all": "plays_all"}),
        on="artist", how="left"
    ).fillna(0)
    merged["plays_all"] = merged["plays_all"].astype(int)

    artist_total_liked = liked_df.groupby("artist").size().to_dict()

    def pct_liked_played(row):
        artist = row["artist"]
        total  = artist_total_liked.get(artist, 0)
        if total == 0: return 0
        liked_tracks_artist = set(
            liked_df[liked_df["artist"] == artist]["track"]
        )
        played_count = sum(1 for t in liked_tracks_artist if t in played_tracks)
        return round(played_count / total * 100)

    merged["pct_liked_played"] = merged.apply(pct_liked_played, axis=1)
    merged["_confidence"] = merged.apply(
        lambda r: _confidence(r["liked_count"], r["plays"], total_plays), axis=1
    )

    # ── Classification with playlist cross-check ──────────────────────────
    # Visceral = plays heavily + not liked + not in any playlist
    # (playlist check done at display time via playlists param if available)
    def classify(row):
        if row["liked_count"] >= 3 and row["plays"] >= 20: return "Active"
        if row["liked_count"] >= 3 and row["plays"] < 5:   return "Admired"
        if row["liked_count"] < 2  and row["plays"] >= 15: return "Visceral"
        return "Neutral"

    merged["profile"] = merged.apply(classify, axis=1)

    never_played = sum(
        1 for t in liked
        if str(t.get("track", t.get("trackName", ""))).lower().strip() not in played_tracks
    )
    total_liked = len(liked)

    n_admired  = len(merged[(merged["liked_count"] >= 3) & (merged["pct_liked_played"] < 30)])
    # Ghost: liked > 0 but plays_all == 0 (checks dfm + dfd)
    n_ghost    = len(merged[(merged["liked_count"] > 0) & (merged["plays_all"] == 0)])
    n_visceral = len(merged[(merged["liked_count"] == 0) & (merged["plays"] >= 15)])

    # ── Header metrics ────────────────────────────────────────────────────
    c1, c2, c3, c4 = st.columns(4)
    for col, val, lbl in [
        (c1, str(total_liked),
         "Tracks liked"),
        (c2, str(never_played) + " (" + str(int(never_played / max(total_liked, 1) * 100)) + "%)",
         "Liked tracks never played"),
        (c3, str(n_admired),
         "Saved, barely played"),
        (c4, str(n_ghost),
         "Artists saved, zero plays"),
    ]:
        with col:
            st.markdown(
                "<div class='metric-card'>"
                "<div class='metric-val'>" + val + "</div>"
                "<div class='metric-lbl'>" + lbl + "</div>"
                "</div>",
                unsafe_allow_html=True
            )

    st.markdown("---")
    tab1, tab2, tab3 = st.tabs(["The Identity Gap", "Most Liked Artists", "Ghost Artists"])

    # ── Tab 1: Identity Gap ───────────────────────────────────────────────
    with tab1:
        st.markdown("### The Gap — Who You Think You Are vs. Who You Are")
        st.caption(
            "Left: artists you liked heavily but barely play. "
            "Right: artists you play constantly but never saved. "
            "Sorted by confidence."
        )

        admired = (
            merged[(merged["liked_count"] >= 3) & (merged["pct_liked_played"] < 30)]
            .sort_values("_confidence", ascending=False).head(30)
        )
        visceral = (
            merged[(merged["liked_count"] == 0) & (merged["plays"] >= 15)]
            .sort_values("plays", ascending=False).head(30)
        )

        col1, col2 = st.columns(2)

        with col1:
            st.markdown(
                "<div style='color:#A78BFA;font-size:.78em;font-weight:700;"
                "text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px;'>"
                "Saved but barely play</div>"
                "<div style='color:#888;font-size:.78em;margin-bottom:12px;'>"
                "Liked a lot — listened rarely. Cultural identity, not daily taste.</div>",
                unsafe_allow_html=True
            )
            if admired.empty:
                st.info("None detected.")
            else:
                admired_plot = admired.copy()
                admired_plot["label"] = [
                    str(c) + " saved / " + str(p) + "% played"
                    for c, p in zip(admired_plot["liked_count"], admired_plot["pct_liked_played"])
                ]
                fig = go.Figure(go.Bar(
                    x=admired_plot["pct_liked_played"],
                    y=admired_plot["artist"],
                    orientation="h",
                    marker_color="#9B59B6",
                    text=admired_plot["label"],
                    textposition="inside",
                    insidetextanchor="start",
                ))
                fig.update_layout(
                    plot_bgcolor="#111", paper_bgcolor="#111", font_color="#aaa",
                    yaxis=dict(autorange="reversed", tickfont=dict(size=11, color="#ccc")),
                    xaxis=dict(gridcolor="#1a1a1a", title="% of saved tracks actually played",
                               range=[0, 130]),
                    margin=dict(l=150, r=20, t=10, b=20),
                    height=max(300, len(admired_plot) * 28)
                )
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown(
                "<div style='color:#f87171;font-size:.78em;font-weight:700;"
                "text-transform:uppercase;letter-spacing:.08em;margin-bottom:6px;'>"
                "Play constantly, never saved</div>"
                "<div style='color:#888;font-size:.78em;margin-bottom:12px;'>"
                "Listened constantly — never liked. Visceral, unfiltered, real.</div>",
                unsafe_allow_html=True
            )
            if visceral.empty:
                st.info("None detected.")
            else:
                visceral_plot = visceral.copy()
                visceral_plot["label"] = [
                    str(p) + " plays — never saved"
                    for p in visceral_plot["plays"]
                ]
                fig2 = go.Figure(go.Bar(
                    x=visceral_plot["plays"],
                    y=visceral_plot["artist"],
                    orientation="h",
                    marker_color=VIOLET,
                    text=visceral_plot["label"],
                    textposition="outside",
                ))
                fig2.update_layout(
                    plot_bgcolor="#111", paper_bgcolor="#111", font_color="#aaa",
                    yaxis=dict(autorange="reversed", tickfont=dict(size=11, color="#ccc")),
                    xaxis=dict(gridcolor="#1a1a1a", title="Total plays",
                               range=[0, visceral_plot["plays"].max() * 1.5]),
                    margin=dict(l=150, r=20, t=10, b=20),
                    height=max(300, len(visceral_plot) * 28)
                )
                st.plotly_chart(fig2, use_container_width=True)

        st.markdown(
            "<div class='insight'>Your likes reflect cultural identity — artists you respect "
            "and want associated with your taste. Your plays reveal what you actually need "
            "musically, day to day, unfiltered. The overlap is smaller than most people think.</div>",
            unsafe_allow_html=True
        )

    # ── Tab 2: Most Liked Artists ─────────────────────────────────────────
    with tab2:
        st.markdown("### Most Liked Artists")
        top = liked_catalogue.sort_values("liked_count", ascending=False).head(50)
        top = top.merge(
            merged[["artist", "plays", "pct_liked_played"]], on="artist", how="left"
        ).fillna(0)
        top["plays"]           = top["plays"].astype(int)
        top["pct_liked_played"] = top["pct_liked_played"].astype(int)

        fig3 = go.Figure()
        fig3.add_trace(go.Bar(
            x=top["liked_count"], y=top["artist"], orientation="h",
            name="Saved", marker_color=VIOLET_LIGHT,
            text=[str(c) + " saved" for c in top["liked_count"]],
            textposition="outside",
        ))
        fig3.update_layout(
            plot_bgcolor="#111", paper_bgcolor="#111", font_color="#aaa",
            yaxis=dict(autorange="reversed", tickfont=dict(size=12, color="#ccc")),
            xaxis=dict(gridcolor="#1a1a1a", title="Tracks saved"),
            margin=dict(l=160, r=80, t=10, b=20),
            height=max(500, len(top) * 28)
        )
        st.plotly_chart(fig3, use_container_width=True)

        st.dataframe(
            top[["artist","liked_count","plays","pct_liked_played"]].rename(columns={
                "artist":           "Artist",
                "liked_count":      "Saved",
                "plays":            "Plays in history",
                "pct_liked_played": "% saved tracks played",
            }).reset_index(drop=True),
            use_container_width=True, height=400
        )

    # ── Tab 3: Ghost Artists ──────────────────────────────────────────────
    with tab3:
        # Ghost = liked > 0 AND plays_all == 0 (cross dfm + dfd)
        ghost = (
            merged[(merged["liked_count"] > 0) & (merged["plays_all"] == 0)]
            .sort_values("liked_count", ascending=False)
        ).head(50)

        st.markdown("### " + str(len(ghost)) + " Ghost Artists — Saved, Zero Plays")
        st.caption(
            "You saved their music at some point. "
            "You never came back — not even once, in any context. "
            "Checked against your full history including children's content."
        )

        if ghost.empty:
            st.success("None — you actually listen to what you save.")
        else:
            cols = st.columns(2)
            for i, (_, row) in enumerate(ghost.iterrows()):
                with cols[i % 2]:
                    st.markdown(
                        "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
                        "border-left:3px solid #555;border-radius:8px;"
                        "padding:10px 14px;margin-bottom:8px;'>"
                        "<div style='font-weight:700;color:#ccc;font-size:.88em;'>"
                        + str(row["artist"]).title() + "</div>"
                        "<div style='color:#555;font-size:.75em;margin-top:3px;'>"
                        + str(int(row["liked_count"])) + " tracks saved · 0 plays"
                        "</div></div>",
                        unsafe_allow_html=True
                    )
