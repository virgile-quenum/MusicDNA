import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

def render_cultural(df):
    st.markdown("# 🌍 Cultural Profile")
    st.markdown("*How you interact with music culture — beyond just what you listen to.*")

    scores = {}

    # ── Generational Drift Score ─────────────────────────────────────────────
    st.markdown("<div class='section-header'>👥 Generational Alignment</div>", unsafe_allow_html=True)

    if "release_year" in df.columns:
        ry = df["release_year"].dropna()
        dominant_era = ry.mode()[0] if not ry.empty else None
        era_pct = (ry.between(dominant_era - 3, dominant_era + 3).sum() / len(ry) * 100) if dominant_era else 0

        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-value'>{int(dominant_era) if dominant_era else "N/A"}</div>
                <div class='metric-label'>Dominant release year in your library</div>
            </div>""", unsafe_allow_html=True)
        with col2:
            st.markdown(f"""
            <div class='metric-card'>
                <div class='metric-value'>{era_pct:.0f}%</div>
                <div class='metric-label'>Plays from your dominant era ± 3 years</div>
            </div>""", unsafe_allow_html=True)

        decade_map = {
            1960: "60s", 1970: "70s", 1980: "80s", 1990: "90s",
            2000: "2000s", 2010: "2010s", 2020: "2020s"
        }
        df_ry = df[df["release_year"].notna()].copy()
        df_ry["decade"] = (df_ry["release_year"] // 10 * 10).map(decade_map).fillna("Other")
        decade_dist = df_ry.groupby("decade")["ms_played"].sum().reset_index()
        decade_dist["hours"] = decade_dist["ms_played"] / 3_600_000
        fig = px.pie(decade_dist, names="decade", values="hours",
                     color_discrete_sequence=px.colors.sequential.Greens_r)
        fig.update_layout(paper_bgcolor="#0d0d0d", font_color="white",
                          legend=dict(bgcolor="#1a1a1a"))
        st.plotly_chart(fig, use_container_width=True)

        scores["Generational Alignment"] = min(era_pct / 30 * 10, 10)

    # ── Timelessness Bias ────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>⏳ Timelessness Bias</div>", unsafe_allow_html=True)

    if "release_year" in df.columns and "popularity" in df.columns:
        timeless = df[
            (df["release_year"] <= pd.Timestamp.now().year - 10) &
            (df["popularity"] >= 60)
        ]
        timeless_pct = len(timeless) / len(df) * 100

        st.markdown(f"""
        <div class='insight-box'>
        <strong>{timeless_pct:.1f}%</strong> of your listens are tracks released 10+ years ago
        that are still widely streamed today — your Timelessness Bias score.
        </div>""", unsafe_allow_html=True)

        scores["Timelessness Bias"] = min(timeless_pct / 40 * 10, 10)

    # ── Endurance Preference ─────────────────────────────────────────────────
    st.markdown("<div class='section-header'>🔥 Hype vs. Endurance Preference</div>", unsafe_allow_html=True)

    if "popularity" in df.columns and "release_year" in df.columns:
        df_pop = df.dropna(subset=["popularity", "release_year"])
        # Proxy: low popularity at release (old tracks, lower current pop) = endurance fans
        # Simpler: % of listens that are NOT top-40 mainstream (popularity < 60)
        non_hype = (df_pop["popularity"] < 65).mean() * 100
        st.markdown(f"""
        <div class='insight-box'>
        <strong>{non_hype:.1f}%</strong> of your listening is on tracks outside the mainstream
        popularity range — suggesting a <strong>{"slow-burn endurance" if non_hype > 50 else "hype-driven"}</strong> listener profile.
        </div>""", unsafe_allow_html=True)
        scores["Endurance Preference"] = min(non_hype / 70 * 10, 10)

    # ── Curiosity Score ──────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>🧭 Musical Curiosity Score</div>", unsafe_allow_html=True)

    df_sorted = df.sort_values("ts")
    first_seen = df_sorted.groupby("artist_name")["ym"].min().reset_index()
    new_per_month = first_seen.groupby("first_ym").size()
    avg_new = new_per_month.mean()
    total_artists = df["artist_name"].nunique()
    total_months = df["ym"].nunique()
    exploration_rate = total_artists / total_months

    curiosity = min((exploration_rate / 10) * 10, 10)
    scores["Curiosity"] = round(curiosity, 1)

    st.markdown(f"""
    <div class='metric-card' style='max-width:300px;'>
        <div class='metric-value'>{curiosity:.1f}/10</div>
        <div class='metric-label'>Musical Curiosity Score<br>
        <span style='font-size:0.8em;color:#888'>~{exploration_rate:.1f} new artists per month on average</span></div>
    </div>""", unsafe_allow_html=True)

    # ── Cultural Identity Summary ─────────────────────────────────────────────
    st.markdown("<div class='section-header'>🌟 Your Cultural Identity Summary</div>", unsafe_allow_html=True)

    if scores:
        categories = list(scores.keys())
        values = [scores[k] for k in categories]

        fig2 = go.Figure()
        fig2.add_trace(go.Scatterpolar(
            r=values + [values[0]],
            theta=categories + [categories[0]],
            fill="toself", fillcolor="rgba(29,185,84,0.2)",
            line=dict(color="#1DB954", width=2)
        ))
        fig2.update_layout(
            polar=dict(
                radialaxis=dict(visible=True, range=[0, 10], color="#aaa"),
                angularaxis=dict(color="#aaa"),
                bgcolor="#1a1a1a"
            ),
            paper_bgcolor="#0d0d0d", font_color="white",
            showlegend=False, height=400
        )
        st.plotly_chart(fig2, use_container_width=True)
