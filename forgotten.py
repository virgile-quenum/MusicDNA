import streamlit as st
import pandas as pd
import numpy as np

def render_forgotten(df):
    st.markdown("# 💀 Forgotten Gems")
    st.markdown("*Tracks you loved and stopped listening to — maybe worth revisiting.*")

    df["date"] = pd.to_datetime(df["ts"]).dt.date
    today = pd.Timestamp.now().date()

    # Per track: play count, first play, last play, avg listen ratio
    track_stats = df.groupby(["track_name", "artist_name"]).agg(
        play_count=("ms_played", "count"),
        total_ms=("ms_played", "sum"),
        first_play=("ts", "min"),
        last_play=("ts", "max"),
        avg_ratio=("listen_ratio", "mean"),
    ).reset_index()

    track_stats["first_play"] = pd.to_datetime(track_stats["first_play"])
    track_stats["last_play"]  = pd.to_datetime(track_stats["last_play"])
    track_stats["days_since_last"] = (pd.Timestamp.now() - track_stats["last_play"]).dt.days
    track_stats["active_months"] = (
        (track_stats["last_play"] - track_stats["first_play"]).dt.days / 30
    ).round(1)
    track_stats["love_score"] = (
        track_stats["play_count"] * track_stats["avg_ratio"].fillna(0.5)
    ).round(1)

    # Forgotten = loved (high plays + completion) + not heard in 365+ days
    forgotten = track_stats[
        (track_stats["play_count"] >= 5) &
        (track_stats["days_since_last"] >= 365) &
        (track_stats["avg_ratio"] >= 0.60)
    ].sort_values("love_score", ascending=False).head(50)

    if forgotten.empty:
        st.info("No forgotten gems detected yet — you either listen to everything regularly, or need more listening history.")
        return

    # ── Summary ──────────────────────────────────────────────────────────────
    c1, c2, c3 = st.columns(3)
    for col, val, label in [
        (c1, len(forgotten), "Forgotten tracks found"),
        (c2, f"{forgotten['days_since_last'].mean():.0f} days", "Avg. silence duration"),
        (c3, f"{forgotten['love_score'].mean():.1f}", "Avg. love score"),
    ]:
        with col:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-value'>{val}</div>
                <div class='metric-label'>{label}</div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # ── Top forgotten gems ────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>🏆 Top 20 — You Should Revisit These</div>", unsafe_allow_html=True)

    display = forgotten.head(20).copy()
    display["Last heard"] = display["last_play"].dt.strftime("%b %Y")
    display["Years ago"] = (display["days_since_last"] / 365).round(1)
    display["Hours listened"] = (display["total_ms"] / 3_600_000).round(2)

    st.dataframe(
        display[[
            "track_name", "artist_name", "play_count",
            "Hours listened", "Last heard", "Years ago", "love_score"
        ]].rename(columns={
            "track_name": "Track", "artist_name": "Artist",
            "play_count": "Plays", "love_score": "Love Score"
        }),
        use_container_width=True, hide_index=True
    )

    # ── Forgotten by era ─────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>📅 When Did You Abandon Them?</div>", unsafe_allow_html=True)

    forgotten["abandon_year"] = forgotten["last_play"].dt.year
    by_year = forgotten.groupby("abandon_year").size().reset_index(name="count")

    import plotly.express as px
    fig = px.bar(by_year, x="abandon_year", y="count", color_discrete_sequence=["#FF6B6B"])
    fig.update_layout(
        paper_bgcolor="#0d0d0d", plot_bgcolor="#1a1a1a", font_color="white",
        xaxis_title="Year last played", yaxis_title="Tracks abandoned",
        xaxis=dict(gridcolor="#333"), yaxis=dict(gridcolor="#333")
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Obsessions ───────────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>🔥 Past Obsessions (Intense + Short-Lived)</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='insight-box'>Tracks you played intensely over a short period then completely dropped.</div>
    """, unsafe_allow_html=True)

    obsessions = track_stats[
        (track_stats["play_count"] >= 10) &
        (track_stats["active_months"] <= 3) &
        (track_stats["days_since_last"] >= 180)
    ].sort_values("play_count", ascending=False).head(20)

    if not obsessions.empty:
        obsessions["Last heard"] = obsessions["last_play"].dt.strftime("%b %Y")
        st.dataframe(
            obsessions[[
                "track_name", "artist_name", "play_count", "active_months", "Last heard"
            ]].rename(columns={
                "track_name": "Track", "artist_name": "Artist",
                "play_count": "Total Plays", "active_months": "Active Months"
            }),
            use_container_width=True, hide_index=True
        )
    else:
        st.info("No strong short-lived obsessions detected.")
