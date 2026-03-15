"""outliers.py"""
import streamlit as st
import pandas as pd
import numpy as np

FEATURES = ["danceability", "energy", "valence", "acousticness", "instrumentalness"]

def render_outliers(df):
    st.markdown("# 🎭 Outliers & Anomalies")
    st.markdown("*Tracks you love that break your own pattern — your guilty pleasures.*")

    feat_df = df.dropna(subset=FEATURES)
    if feat_df.empty:
        st.warning("Run pipeline.py first to enrich your data.")
        return

    centroid = feat_df[FEATURES].mean().values

    from numpy.linalg import norm
    def cosine_dist(row):
        v = row[FEATURES].values
        if norm(v) == 0 or norm(centroid) == 0:
            return 1.0
        return 1 - np.dot(v, centroid) / (norm(v) * norm(centroid))

    feat_df = feat_df.copy()
    feat_df["distance"] = feat_df.apply(cosine_dist, axis=1)

    # Loved but distant from DNA
    track_stats = feat_df.groupby(["track_name", "artist_name"]).agg(
        play_count=("ms_played", "count"),
        avg_ratio=("listen_ratio", "mean"),
        avg_distance=("distance", "mean"),
        energy=("energy", "mean"),
        valence=("valence", "mean"),
        genres=("genres", "first"),
    ).reset_index()

    outliers = track_stats[
        (track_stats["play_count"] >= 5) &
        (track_stats["avg_ratio"] >= 0.65) &
        (track_stats["avg_distance"] >= 0.25)
    ].sort_values("avg_distance", ascending=False).head(20)

    if outliers.empty:
        st.info("No strong outliers detected — your taste is quite consistent!")
        return

    st.markdown(f"""
    <div class='insight-box'>
    Found <strong>{len(outliers)} tracks</strong> that you listen to deeply but sit far from your usual musical DNA.
    These are your wildcards.
    </div>""", unsafe_allow_html=True)

    display = outliers.copy()
    display["Outlier Score"] = (display["avg_distance"] * 100).round(1)
    display["Avg. Completion"] = (display["avg_ratio"] * 100).round(1)

    st.dataframe(
        display[[
            "track_name", "artist_name", "play_count",
            "Avg. Completion", "Outlier Score", "genres"
        ]].rename(columns={
            "track_name": "Track", "artist_name": "Artist",
            "play_count": "Plays", "genres": "Genre"
        }),
        use_container_width=True, hide_index=True
    )
