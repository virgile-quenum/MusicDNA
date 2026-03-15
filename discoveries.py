"""discoveries.py"""
import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px

def render_discoveries(df):
    st.markdown("# 🔭 Early Discoveries")
    st.markdown("*Tracks you found before they became widely popular.*")

    if "popularity" not in df.columns or "release_year" not in df.columns:
        st.warning("Popularity data not available. Run pipeline.py first.")
        return

    df_d = df.dropna(subset=["popularity", "release_year"]).copy()
    df_d["ts"] = pd.to_datetime(df_d["ts"])
    df_d["days_after_release"] = (
        df_d["ts"].dt.year * 365 - df_d["release_year"] * 365
    ).clip(lower=0)

    # Early discovery = first heard within 90 days of release, now popular
    first_heard = df_d.groupby(["track_name", "artist_name"]).agg(
        first_play=("ts", "min"),
        release_year=("release_year", "first"),
        current_popularity=("popularity", "mean"),
        play_count=("ms_played", "count"),
    ).reset_index()

    first_heard["first_play"] = pd.to_datetime(first_heard["first_play"])
    first_heard["approx_days_after"] = (
        (first_heard["first_play"].dt.year - first_heard["release_year"]) * 365 +
        first_heard["first_play"].dt.dayofyear
    ).clip(lower=0)

    early_adopter = first_heard[
        (first_heard["approx_days_after"] <= 120) &
        (first_heard["current_popularity"] >= 65)
    ].sort_values("current_popularity", ascending=False).head(30)

    if early_adopter.empty:
        st.info("No strong early-discovery signals found. This analysis improves with more historical data.")
        return

    st.markdown(f"""
    <div class='insight-box'>
    ⚠️ <em>Note: Spotify only provides current popularity, not historical. This is a proxy —
    tracks you heard early + are now popular. Not ground truth, but a solid signal.</em>
    </div>""", unsafe_allow_html=True)

    st.markdown(f"""
    <div class='metric-card' style='max-width:280px;'>
        <div class='metric-value'>{len(early_adopter)}</div>
        <div class='metric-label'>Potential early discoveries detected</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("<div class='section-header'>🏆 Your Early Discoveries</div>", unsafe_allow_html=True)
    display = early_adopter.copy()
    display["First Heard"] = display["first_play"].dt.strftime("%b %Y")
    display["Current Popularity"] = display["current_popularity"].round(0).astype(int)

    st.dataframe(
        display[[
            "track_name", "artist_name", "First Heard",
            "release_year", "Current Popularity", "play_count"
        ]].rename(columns={
            "track_name": "Track", "artist_name": "Artist",
            "release_year": "Release Year", "play_count": "Your Plays"
        }),
        use_container_width=True, hide_index=True
    )

    # ── Discovery timing distribution ────────────────────────────────────────
    st.markdown("<div class='section-header'>⏱️ When Do You Typically Discover Music?</div>", unsafe_allow_html=True)

    timing_bins = pd.cut(
        first_heard["approx_days_after"].clip(0, 1825),
        bins=[0, 30, 90, 180, 365, 730, 1825],
        labels=["Within 1 month", "1–3 months", "3–6 months",
                "6–12 months", "1–2 years", "2+ years after release"]
    )
    timing_dist = timing_bins.value_counts().sort_index().reset_index()
    timing_dist.columns = ["When discovered", "Tracks"]

    fig = px.bar(timing_dist, x="When discovered", y="Tracks",
                 color_discrete_sequence=["#1DB954"])
    fig.update_layout(paper_bgcolor="#0d0d0d", plot_bgcolor="#1a1a1a",
                      font_color="white", xaxis=dict(gridcolor="#333"),
                      yaxis=dict(gridcolor="#333"))
    st.plotly_chart(fig, use_container_width=True)
