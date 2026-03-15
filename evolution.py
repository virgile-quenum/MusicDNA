import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import numpy as np

FEATURES = ["danceability", "energy", "valence", "acousticness", "instrumentalness"]

def render_evolution(df):
    st.markdown("# 📅 Taste Evolution")
    st.markdown("*How your music has changed since you joined Spotify*")

    feat_df = df.dropna(subset=["energy", "valence"])
    if feat_df.empty:
        st.warning("Run pipeline.py to enrich your data first.")
        return

    # ── Feature timeline ──────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>📈 Audio Feature Trends Over Time</div>", unsafe_allow_html=True)

    monthly = feat_df.groupby("ym")[FEATURES].mean().reset_index()
    monthly["ym_dt"] = pd.to_datetime(monthly["ym"])

    fig = go.Figure()
    colors = {"energy": "#1DB954", "valence": "#FF6B6B", "danceability": "#4ECDC4",
              "acousticness": "#FFE66D", "instrumentalness": "#A8DADC"}
    for feat in FEATURES:
        fig.add_trace(go.Scatter(
            x=monthly["ym_dt"], y=monthly[feat],
            name=feat.capitalize(), mode="lines",
            line=dict(color=colors.get(feat, "#ffffff"), width=2)
        ))
    fig.update_layout(
        paper_bgcolor="#0d0d0d", plot_bgcolor="#1a1a1a", font_color="white",
        legend=dict(bgcolor="#1a1a1a", bordercolor="#333"),
        xaxis=dict(gridcolor="#333"), yaxis=dict(gridcolor="#333", range=[0, 1]),
        height=400
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Mood quadrant evolution ───────────────────────────────────────────────
    st.markdown("<div class='section-header'>🎭 Mood Quadrant Over Time</div>", unsafe_allow_html=True)

    mood_monthly = feat_df.groupby(["ym", "mood"]).size().reset_index(name="count")
    mood_total = mood_monthly.groupby("ym")["count"].sum().reset_index(name="total")
    mood_monthly = mood_monthly.merge(mood_total, on="ym")
    mood_monthly["pct"] = (mood_monthly["count"] / mood_monthly["total"] * 100).round(1)
    mood_monthly["ym_dt"] = pd.to_datetime(mood_monthly["ym"])

    mood_colors = {"Euphoric": "#1DB954", "Tense": "#FF6B6B",
                   "Peaceful": "#4ECDC4", "Melancholic": "#9B59B6"}
    fig2 = px.area(mood_monthly, x="ym_dt", y="pct", color="mood",
                   color_discrete_map=mood_colors)
    fig2.update_layout(
        paper_bgcolor="#0d0d0d", plot_bgcolor="#1a1a1a", font_color="white",
        legend=dict(bgcolor="#1a1a1a"), xaxis=dict(gridcolor="#333"),
        yaxis=dict(gridcolor="#333", title="% of listens"), height=380
    )
    st.plotly_chart(fig2, use_container_width=True)

    # ── Genre evolution ───────────────────────────────────────────────────────
    if "genres" in df.columns:
        st.markdown("<div class='section-header'>🎼 Genre Share Over Time</div>", unsafe_allow_html=True)

        genre_df = df[df["genres"].notna()].copy()
        genre_df["primary_genre"] = genre_df["genres"].str.split(", ").str[0]
        top_genres = genre_df["primary_genre"].value_counts().head(8).index.tolist()
        genre_df["genre_label"] = genre_df["primary_genre"].where(
            genre_df["primary_genre"].isin(top_genres), "Other"
        )

        genre_monthly = genre_df.groupby(["ym", "genre_label"]).size().reset_index(name="count")
        genre_total = genre_monthly.groupby("ym")["count"].sum().reset_index(name="total")
        genre_monthly = genre_monthly.merge(genre_total, on="ym")
        genre_monthly["pct"] = (genre_monthly["count"] / genre_monthly["total"] * 100).round(1)
        genre_monthly["ym_dt"] = pd.to_datetime(genre_monthly["ym"])

        fig3 = px.area(genre_monthly, x="ym_dt", y="pct", color="genre_label")
        fig3.update_layout(
            paper_bgcolor="#0d0d0d", plot_bgcolor="#1a1a1a", font_color="white",
            legend=dict(bgcolor="#1a1a1a"), xaxis=dict(gridcolor="#333"),
            yaxis=dict(gridcolor="#333", title="% of listens"), height=380
        )
        st.plotly_chart(fig3, use_container_width=True)

    # ── Discovery rate ────────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>🔭 New Artists Discovered Per Month</div>", unsafe_allow_html=True)

    df_sorted = df.sort_values("ts")
    first_seen = df_sorted.groupby("artist_name")["ym"].min().reset_index()
    first_seen.columns = ["artist_name", "first_ym"]
    new_per_month = first_seen.groupby("first_ym").size().reset_index(name="new_artists")
    new_per_month["ym_dt"] = pd.to_datetime(new_per_month["first_ym"])

    fig4 = px.bar(new_per_month, x="ym_dt", y="new_artists",
                  color_discrete_sequence=["#1DB954"])
    fig4.update_layout(
        paper_bgcolor="#0d0d0d", plot_bgcolor="#1a1a1a", font_color="white",
        xaxis=dict(gridcolor="#333"), yaxis=dict(gridcolor="#333"), height=300
    )
    st.plotly_chart(fig4, use_container_width=True)

    avg_new = new_per_month["new_artists"].mean()
    st.markdown(
        f"<div class='insight-box'>📊 On average, you discovered <strong>{avg_new:.0f} new artists per month</strong> across your full Spotify history.</div>",
        unsafe_allow_html=True
    )

    # ── Musical era phases ────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>🔮 Your Musical Eras</div>", unsafe_allow_html=True)
    st.markdown("""
    <div class='insight-box'>
    Musical eras are detected by identifying months where your energy and valence shifted significantly.
    Each era represents a distinct phase of your listening identity.
    </div>""", unsafe_allow_html=True)

    yearly_means = feat_df.groupby("year")[["energy", "valence", "acousticness", "danceability"]].mean().round(2)
    yearly_means = yearly_means.reset_index()
    yearly_means.columns = ["Year", "Energy", "Valence", "Acousticness", "Danceability"]
    st.dataframe(yearly_means, use_container_width=True, hide_index=True)
