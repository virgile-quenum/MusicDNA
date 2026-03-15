import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import numpy as np

FEATURES = ["danceability", "energy", "valence", "acousticness",
            "instrumentalness", "speechiness"]

def render_dna(df):
    st.markdown("# 🧬 Your Musical DNA")

    feat_df = df[df["completed"] == True][FEATURES + ["artist_name", "track_name", "ms_played", "genres"]].dropna(subset=FEATURES)
    if feat_df.empty:
        st.warning("Not enough enriched data yet. Run pipeline.py first.")
        return

    # ── Radar chart ─────────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>🔬 Your Audio Fingerprint</div>", unsafe_allow_html=True)
    means = feat_df[FEATURES].mean()

    fig = go.Figure()
    fig.add_trace(go.Scatterpolar(
        r=means.values.tolist() + [means.values[0]],
        theta=FEATURES + [FEATURES[0]],
        fill="toself",
        fillcolor="rgba(29,185,84,0.2)",
        line=dict(color="#1DB954", width=2),
        name="Your DNA"
    ))
    fig.update_layout(
        polar=dict(
            radialaxis=dict(visible=True, range=[0, 1], color="#aaaaaa"),
            angularaxis=dict(color="#aaaaaa"),
            bgcolor="#1a1a1a"
        ),
        paper_bgcolor="#0d0d0d", font_color="white",
        showlegend=False, height=400
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Feature breakdown ────────────────────────────────────────────────────
    col1, col2, col3 = st.columns(3)
    feature_descriptions = {
        "danceability":     ("💃", "Danceability",     "How suitable for dancing"),
        "energy":           ("⚡", "Energy",           "Intensity and activity level"),
        "valence":          ("😊", "Valence",          "Musical positiveness"),
        "acousticness":     ("🎸", "Acousticness",     "Acoustic vs electronic"),
        "instrumentalness": ("🎹", "Instrumentalness", "Vocals vs instrumental"),
        "speechiness":      ("🎤", "Speechiness",      "Spoken word presence"),
    }
    for i, (feat, (icon, label, desc)) in enumerate(feature_descriptions.items()):
        val = means[feat]
        col = [col1, col2, col3][i % 3]
        with col:
            st.markdown(f"""
            <div class='metric-card'>
                <div style='font-size:1.5em;'>{icon}</div>
                <div class='metric-value'>{val:.2f}</div>
                <div class='metric-label'>{label}<br><span style='font-size:0.8em;color:#888'>{desc}</span></div>
            </div>""", unsafe_allow_html=True)

    # ── Insight text ─────────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>💬 DNA Insights</div>", unsafe_allow_html=True)
    insights = []
    if means["energy"] > 0.65:
        insights.append("⚡ You lean toward high-energy music — driving, intense, powerful.")
    elif means["energy"] < 0.40:
        insights.append("🌙 You favor calm, low-energy music — relaxed and introspective.")

    if means["valence"] > 0.60:
        insights.append("😊 Your library skews positive and upbeat in emotional tone.")
    elif means["valence"] < 0.40:
        insights.append("🌧 You gravitate toward darker, more complex emotional music.")

    if means["acousticness"] > 0.50:
        insights.append("🎸 Strong acoustic preference — you value raw, organic sound.")
    if means["instrumentalness"] > 0.30:
        insights.append("🎹 Notable instrumental content — you listen beyond lyrics.")
    if means["danceability"] > 0.70:
        insights.append("💃 Highly danceable taste — rhythm and groove are core to your DNA.")

    for ins in insights:
        st.markdown(f"<div class='insight-box'>{ins}</div>", unsafe_allow_html=True)

    # ── Top genres ───────────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>🎼 Your Top Genres</div>", unsafe_allow_html=True)
    if "genres" in df.columns:
        genre_series = df[df["genres"].notna()]["genres"].str.split(", ").explode()
        top_genres = genre_series.value_counts().head(15).reset_index()
        top_genres.columns = ["Genre", "Count"]
        fig2 = px.bar(top_genres, x="Count", y="Genre", orientation="h",
                      color_discrete_sequence=["#1DB954"])
        fig2.update_layout(paper_bgcolor="#0d0d0d", plot_bgcolor="#0d0d0d",
                           font_color="white", yaxis={"categoryorder": "total ascending"})
        st.plotly_chart(fig2, use_container_width=True)

    # ── Artist alignment ─────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>🎤 Artists Most Aligned With Your DNA</div>", unsafe_allow_html=True)
    centroid = means.values
    artist_feat = feat_df.groupby("artist_name")[FEATURES].mean()
    artist_feat = artist_feat.dropna()

    from numpy.linalg import norm
    def cosine_sim(a, b):
        if norm(a) == 0 or norm(b) == 0:
            return 0
        return np.dot(a, b) / (norm(a) * norm(b))

    artist_feat["alignment"] = artist_feat.apply(
        lambda row: cosine_sim(centroid, row.values), axis=1
    )

    play_counts = df.groupby("artist_name")["ms_played"].sum()
    artist_feat = artist_feat.join(play_counts.rename("total_ms"))
    # Only artists you've listened to substantially
    top_aligned = (
        artist_feat[artist_feat["total_ms"] > 600_000]
        .sort_values("alignment", ascending=False)
        .head(10)
        .reset_index()
    )
    top_aligned["Alignment %"] = (top_aligned["alignment"] * 100).round(1)
    top_aligned["Hours"] = (top_aligned["total_ms"] / 3_600_000).round(1)

    st.dataframe(
        top_aligned[["artist_name", "Alignment %", "Hours"]].rename(columns={"artist_name": "Artist"}),
        use_container_width=True, hide_index=True
    )
