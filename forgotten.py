import streamlit as st
import pandas as pd
import plotly.graph_objects as go

VIOLET       = "#7C3AED"
VIOLET_LIGHT = "#A78BFA"
GREEN        = "#1DB954"
AMBER        = "#f59e0b"
RED          = "#f87171"

def _card(content, border=VIOLET):
    st.markdown(
        "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
        "border-left:3px solid " + border + ";border-radius:8px;"
        "padding:14px;margin-bottom:10px;'>" + content + "</div>",
        unsafe_allow_html=True
    )

def _insight(text):
    st.markdown(
        "<div class='insight'>" + text + "</div>",
        unsafe_allow_html=True
    )

def render(dfm):
    st.title("Forgotten")
    st.markdown("*What you used to love. What you should revisit.*")

    if dfm is None or dfm.empty:
        st.warning("Upload your Extended History zip to enable this analysis.")
        return

    cutoff_1y  = dfm["ts"].max() - pd.DateOffset(years=1)
    cutoff_2y  = dfm["ts"].max() - pd.DateOffset(years=2)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Forgotten Hits",
        "Obsessions",
        "Never Skipped",
        "Lost Artists",
        "Time Capsules",
    ])

    # ── Tab 1: Forgotten Hits ─────────────────────────────────────────────────
    with tab1:
        st.markdown("### Tracks you used to play — silent for 12+ months")
        st.caption("Minimum 20 plays all-time. Nothing in the last 12 months.")

        track_stats = dfm.groupby(["trackName", "artistName"]).agg(
            plays       =("ms", "count"),
            last_played =("ts", "max"),
            first_played=("ts", "min"),
            skips       =("skipped", "sum") if "skipped" in dfm.columns else ("ms", lambda x: 0),
        ).reset_index()

        forgotten = track_stats[
            (track_stats["plays"] >= 20) &
            (track_stats["last_played"] < cutoff_1y)
        ].sort_values("plays", ascending=False).head(40)

        if forgotten.empty:
            st.info("No forgotten hits found.")
        else:
            st.markdown("<b style='color:#fff;'>" + str(len(forgotten)) + " tracks:</b>", unsafe_allow_html=True)
            cols = st.columns(2)
            for i, (_, row) in enumerate(forgotten.iterrows()):
                last = row["last_played"].strftime("%b %Y")
                silence = int((dfm["ts"].max() - row["last_played"]).days / 30)
                with cols[i % 2]:
                    _card(
                        "<div style='font-weight:700;color:#fff;font-size:.9em;'>"
                        + str(row["trackName"]) + "</div>"
                        "<div style='color:#555;font-size:.78em;margin-top:3px;'>"
                        + str(row["artistName"]) + "</div>"
                        "<div style='display:flex;gap:12px;margin-top:6px;flex-wrap:wrap;'>"
                        "<span style='color:#A78BFA;font-weight:700;font-size:.78em;'>"
                        + str(int(row["plays"])) + " plays</span>"
                        "<span style='color:#555;font-size:.78em;'>last: " + last + "</span>"
                        "<span style='color:#f87171;font-size:.78em;'>"
                        + str(silence) + " months of silence</span>"
                        "</div>",
                        border=VIOLET_LIGHT
                    )

    # ── Tab 2: Obsessions ─────────────────────────────────────────────────────
    with tab2:
        st.markdown("### Past obsessions — intense bursts, then nothing")
        st.caption("10+ plays concentrated in under 90 days, then dropped. Sorted by intensity.")

        track_ts = dfm.copy()
        track_ts["key"] = track_ts["trackName"] + "|||" + track_ts["artistName"]

        obsessions = []
        for key, grp in track_ts.groupby("key"):
            if len(grp) < 10:
                continue
            grp_s = grp.sort_values("ts")
            first = grp_s["ts"].iloc[0]
            last  = grp_s["ts"].iloc[-1]
            span_days = (last - first).days
            if span_days == 0:
                continue
            # find peak window: max plays in any 90-day window
            peak_plays = 0
            peak_start = None
            for idx, row_ts in grp_s.iterrows():
                window_end   = row_ts["ts"] + pd.DateOffset(days=90)
                window_plays = ((grp_s["ts"] >= row_ts["ts"]) & (grp_s["ts"] <= window_end)).sum()
                if window_plays > peak_plays:
                    peak_plays  = window_plays
                    peak_start  = row_ts["ts"]
            if peak_plays < 10:
                continue
            # must be silent for last 12 months
            if last >= cutoff_1y:
                continue
            parts = key.split("|||")
            track_name  = parts[0]
            artist_name = parts[1] if len(parts) > 1 else ""
            obsessions.append({
                "track":       track_name,
                "artist":      artist_name,
                "total_plays": len(grp),
                "peak_plays":  int(peak_plays),
                "peak_start":  peak_start,
                "last_played": last,
                "span_days":   span_days,
            })

        obsessions = sorted(obsessions, key=lambda x: -x["peak_plays"])[:30]

        if not obsessions:
            st.info("No past obsessions detected.")
        else:
            st.markdown("<b style='color:#fff;'>" + str(len(obsessions)) + " obsessions:</b>", unsafe_allow_html=True)
            cols = st.columns(2)
            for i, o in enumerate(obsessions):
                peak_label = o["peak_start"].strftime("%b %Y") if o["peak_start"] else "unknown"
                last_label = o["last_played"].strftime("%b %Y")
                with cols[i % 2]:
                    _card(
                        "<div style='font-weight:700;color:#fff;font-size:.9em;'>"
                        + str(o["track"]) + "</div>"
                        "<div style='color:#555;font-size:.78em;margin-top:3px;'>"
                        + str(o["artist"]) + "</div>"
                        "<div style='display:flex;gap:12px;margin-top:6px;flex-wrap:wrap;'>"
                        "<span style='color:#f59e0b;font-weight:700;font-size:.78em;'>"
                        + str(o["peak_plays"]) + "x in 90 days</span>"
                        "<span style='color:#555;font-size:.78em;'>peak: " + peak_label + "</span>"
                        "<span style='color:#444;font-size:.78em;'>last: " + last_label + "</span>"
                        "</div>",
                        border=AMBER
                    )

    # ── Tab 3: Never Skipped ──────────────────────────────────────────────────
    with tab3:
        st.markdown("### Tracks you never skipped — but stopped playing")
        st.caption("0% skip rate on 5+ plays. Silent for the last 12 months. These deserve a comeback.")

        if "skipped" not in dfm.columns:
            st.info("Skip data not available — requires Extended History export.")
        else:
            skip_stats = dfm.groupby(["trackName", "artistName"]).agg(
                plays      =("ms", "count"),
                skips      =("skipped", "sum"),
                last_played=("ts", "max"),
            ).reset_index()

            never_skipped = skip_stats[
                (skip_stats["plays"] >= 5) &
                (skip_stats["skips"] == 0) &
                (skip_stats["last_played"] < cutoff_1y)
            ].sort_values("plays", ascending=False).head(40)

            if never_skipped.empty:
                st.info("No never-skipped forgotten tracks found.")
            else:
                st.markdown("<b style='color:#fff;'>" + str(len(never_skipped)) + " tracks:</b>", unsafe_allow_html=True)
                cols = st.columns(2)
                for i, (_, row) in enumerate(never_skipped.iterrows()):
                    last = row["last_played"].strftime("%b %Y")
                    silence = int((dfm["ts"].max() - row["last_played"]).days / 30)
                    with cols[i % 2]:
                        _card(
                            "<div style='font-weight:700;color:#fff;font-size:.9em;'>"
                            + str(row["trackName"]) + "</div>"
                            "<div style='color:#555;font-size:.78em;margin-top:3px;'>"
                            + str(row["artistName"]) + "</div>"
                            "<div style='display:flex;gap:12px;margin-top:6px;flex-wrap:wrap;'>"
                            "<span style='color:" + GREEN + ";font-weight:700;font-size:.78em;'>0% skip</span>"
                            "<span style='color:#A78BFA;font-size:.78em;'>"
                            + str(int(row["plays"])) + " plays</span>"
                            "<span style='color:#555;font-size:.78em;'>last: " + last + "</span>"
                            "<span style='color:#444;font-size:.78em;'>"
                            + str(silence) + " months ago</span>"
                            "</div>",
                            border=GREEN
                        )

    # ── Tab 4: Lost Artists ───────────────────────────────────────────────────
    with tab4:
        st.markdown("### Artists you walked away from")
        st.caption("50+ plays all-time. Nothing in the last 12 months. When did it stop?")

        artist_stats = dfm.groupby("artistName").agg(
            plays       =("ms", "count"),
            last_played =("ts", "max"),
            first_played=("ts", "min"),
            hours       =("ms", lambda x: round(x.sum() / 3600000, 1)),
        ).reset_index()

        lost = artist_stats[
            (artist_stats["plays"] >= 50) &
            (artist_stats["last_played"] < cutoff_1y)
        ].sort_values("plays", ascending=False).head(30)

        if lost.empty:
            st.info("No lost artists found.")
        else:
            st.markdown("<b style='color:#fff;'>" + str(len(lost)) + " artists:</b>", unsafe_allow_html=True)

            # timeline chart
            fig = go.Figure()
            for _, row in lost.head(15).iterrows():
                fig.add_trace(go.Scatter(
                    x=[row["first_played"], row["last_played"]],
                    y=[row["artistName"], row["artistName"]],
                    mode="lines+markers",
                    line=dict(color=VIOLET, width=3),
                    marker=dict(size=8, color=[GREEN, RED]),
                    showlegend=False,
                    hovertemplate=str(row["artistName"]) + "<br>"
                        + str(int(row["plays"])) + " plays<br>"
                        + str(row["hours"]) + "h<extra></extra>"
                ))
            fig.update_layout(
                plot_bgcolor="#111", paper_bgcolor="#111", font_color="#888",
                xaxis=dict(gridcolor="#1e1e1e"),
                yaxis=dict(tickfont=dict(size=11, color="#ccc")),
                margin=dict(l=150, r=20, t=10, b=20),
                height=max(300, len(lost.head(15)) * 32)
            )
            st.plotly_chart(fig, use_container_width=True)

            cols = st.columns(2)
            for i, (_, row) in enumerate(lost.iterrows()):
                first = row["first_played"].strftime("%b %Y")
                last  = row["last_played"].strftime("%b %Y")
                silence = int((dfm["ts"].max() - row["last_played"]).days / 30)
                with cols[i % 2]:
                    _card(
                        "<div style='font-weight:700;color:#fff;font-size:.92em;'>"
                        + str(row["artistName"]) + "</div>"
                        "<div style='display:flex;gap:12px;margin-top:6px;flex-wrap:wrap;'>"
                        "<span style='color:#A78BFA;font-weight:700;font-size:.78em;'>"
                        + str(int(row["plays"])) + " plays</span>"
                        "<span style='color:#555;font-size:.78em;'>"
                        + str(row["hours"]) + "h total</span>"
                        "<span style='color:#555;font-size:.78em;'>"
                        + first + " → " + last + "</span>"
                        "<span style='color:#f87171;font-size:.78em;'>"
                        + str(silence) + " months of silence</span>"
                        "</div>",
                        border=RED
                    )

    # ── Tab 5: Time Capsules ──────────────────────────────────────────────────
    with tab5:
        st.markdown("### Time capsule tracks — only existed in one window of your life")
        st.caption("Played only within a 6-month window. Never before, never after. A snapshot of who you were.")

        track_ts2 = dfm.copy()
        track_ts2["key"] = track_ts2["trackName"] + "|||" + track_ts2["artistName"]

        capsules = []
        for key, grp in track_ts2.groupby("key"):
            if len(grp) < 5:
                continue
            first = grp["ts"].min()
            last  = grp["ts"].max()
            span  = (last - first).days
            if span > 180:
                continue
            if last >= cutoff_1y:
                continue
            parts = key.split("|||")
            capsules.append({
                "track":   parts[0],
                "artist":  parts[1] if len(parts) > 1 else "",
                "plays":   len(grp),
                "first":   first,
                "last":    last,
                "span":    span,
            })

        capsules = sorted(capsules, key=lambda x: -x["plays"])[:40]

        if not capsules:
            st.info("No time capsule tracks found.")
        else:
            st.markdown("<b style='color:#fff;'>" + str(len(capsules)) + " tracks:</b>", unsafe_allow_html=True)
            cols = st.columns(2)
            for i, c in enumerate(capsules):
                period = c["first"].strftime("%b %Y") + " → " + c["last"].strftime("%b %Y")
                with cols[i % 2]:
                    _card(
                        "<div style='font-weight:700;color:#fff;font-size:.9em;'>"
                        + str(c["track"]) + "</div>"
                        "<div style='color:#555;font-size:.78em;margin-top:3px;'>"
                        + str(c["artist"]) + "</div>"
                        "<div style='display:flex;gap:12px;margin-top:6px;flex-wrap:wrap;'>"
                        "<span style='color:#60a5fa;font-weight:700;font-size:.78em;'>"
                        + str(c["plays"]) + " plays</span>"
                        "<span style='color:#555;font-size:.78em;'>" + period + "</span>"
                        "<span style='color:#444;font-size:.78em;'>"
                        + str(c["span"]) + " days window</span>"
                        "</div>",
                        border="#60a5fa"
                    )
