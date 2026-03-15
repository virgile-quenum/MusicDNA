import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

def render_behavior(df):
    st.markdown("# ⏩ Skip & Listening Behavior")

    # ── Skip overview ────────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>📊 Skip Overview</div>", unsafe_allow_html=True)

    skip_rate = df["skipped"].mean() * 100 if "skipped" in df.columns else 0
    avg_before_skip = df[df["skipped"] == True]["ms_played"].mean() / 1000 if "skipped" in df.columns else 0
    completed_rate = df["completed"].mean() * 100 if "completed" in df.columns else 0

    c1, c2, c3 = st.columns(3)
    for col, val, label in [
        (c1, f"{skip_rate:.1f}%", "Overall skip rate"),
        (c2, f"{avg_before_skip:.0f}s", "Avg. seconds before skip"),
        (c3, f"{completed_rate:.1f}%", "Tracks completed (>80%)"),
    ]:
        with col:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-value'>{val}</div>
                <div class='metric-label'>{label}</div>
            </div>""", unsafe_allow_html=True)

    # ── What you skip ────────────────────────────────────────────────────────
    if "skipped" in df.columns:
        st.markdown("<div class='section-header'>🎵 Audio Profile: Skipped vs Completed</div>", unsafe_allow_html=True)

        FEATURES = ["danceability", "energy", "valence", "acousticness", "instrumentalness"]
        feat_df = df.dropna(subset=FEATURES)
        skipped_means   = feat_df[feat_df["skipped"] == True][FEATURES].mean()
        completed_means = feat_df[feat_df["completed"] == True][FEATURES].mean()

        fig = go.Figure()
        fig.add_trace(go.Scatterpolar(
            r=skipped_means.values.tolist() + [skipped_means.values[0]],
            theta=FEATURES + [FEATURES[0]],
            fill="toself", fillcolor="rgba(255,107,107,0.2)",
            line=dict(color="#FF6B6B", width=2), name="Skipped"
        ))
        fig.add_trace(go.Scatterpolar(
            r=completed_means.values.tolist() + [completed_means.values[0]],
            theta=FEATURES + [FEATURES[0]],
            fill="toself", fillcolor="rgba(29,185,84,0.2)",
            line=dict(color="#1DB954", width=2), name="Completed"
        ))
        fig.update_layout(
            polar=dict(radialaxis=dict(visible=True, range=[0, 1], color="#aaa"),
                       bgcolor="#1a1a1a"),
            paper_bgcolor="#0d0d0d", font_color="white",
            legend=dict(bgcolor="#1a1a1a"), height=400
        )
        st.plotly_chart(fig, use_container_width=True)

    # ── Listening by hour ────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>🕐 When Do You Listen?</div>", unsafe_allow_html=True)

    hourly = df.groupby("hour")["ms_played"].sum().reset_index()
    hourly["hours"] = hourly["ms_played"] / 3_600_000
    fig2 = px.bar(hourly, x="hour", y="hours", color_discrete_sequence=["#1DB954"])
    fig2.update_layout(paper_bgcolor="#0d0d0d", plot_bgcolor="#1a1a1a",
                       font_color="white", xaxis_title="Hour of day",
                       yaxis_title="Hours listened", xaxis=dict(gridcolor="#333"),
                       yaxis=dict(gridcolor="#333"))
    st.plotly_chart(fig2, use_container_width=True)

    # ── Mood by hour ─────────────────────────────────────────────────────────
    if "mood" in df.columns:
        st.markdown("<div class='section-header'>🎭 Mood Profile by Hour</div>", unsafe_allow_html=True)
        mood_hour = df.groupby(["hour", "mood"]).size().reset_index(name="count")
        mood_colors = {"Euphoric": "#1DB954", "Tense": "#FF6B6B",
                       "Peaceful": "#4ECDC4", "Melancholic": "#9B59B6"}
        fig3 = px.bar(mood_hour, x="hour", y="count", color="mood",
                      barmode="stack", color_discrete_map=mood_colors)
        fig3.update_layout(paper_bgcolor="#0d0d0d", plot_bgcolor="#1a1a1a",
                           font_color="white", legend=dict(bgcolor="#1a1a1a"),
                           xaxis=dict(gridcolor="#333"), yaxis=dict(gridcolor="#333"))
        st.plotly_chart(fig3, use_container_width=True)

    # ── Day of week ──────────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>📅 Listening by Day of Week</div>", unsafe_allow_html=True)
    days = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    daily = df.groupby("dow")["ms_played"].sum().reset_index()
    daily["day"] = daily["dow"].map(dict(enumerate(days)))
    daily["hours"] = daily["ms_played"] / 3_600_000
    fig4 = px.bar(daily, x="day", y="hours", color_discrete_sequence=["#1DB954"],
                  category_orders={"day": days})
    fig4.update_layout(paper_bgcolor="#0d0d0d", plot_bgcolor="#1a1a1a",
                       font_color="white", xaxis=dict(gridcolor="#333"),
                       yaxis=dict(gridcolor="#333"))
    st.plotly_chart(fig4, use_container_width=True)

    # ── Most skipped tracks ──────────────────────────────────────────────────
    if "skipped" in df.columns:
        st.markdown("<div class='section-header'>⏭️ Your Most Skipped Tracks</div>", unsafe_allow_html=True)
        track_stats = df.groupby(["track_name", "artist_name"]).agg(
            plays=("ms_played", "count"),
            skips=("skipped", "sum")
        ).reset_index()
        track_stats["skip_rate"] = (track_stats["skips"] / track_stats["plays"] * 100).round(1)
        most_skipped = track_stats[track_stats["plays"] >= 5].sort_values("skip_rate", ascending=False).head(15)
        st.dataframe(most_skipped.rename(columns={
            "track_name": "Track", "artist_name": "Artist",
            "plays": "Total Plays", "skips": "Skips", "skip_rate": "Skip Rate %"
        }), use_container_width=True, hide_index=True)
