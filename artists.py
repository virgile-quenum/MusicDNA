import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

VIOLET       = "#7C3AED"
VIOLET_LIGHT = "#A78BFA"
GREEN        = "#1DB954"
AMBER        = "#f59e0b"
RED          = "#f87171"

def _skip_color(rate):
    if rate < 10: return GREEN
    if rate < 25: return AMBER
    return RED

def _filter_period(df, period):
    yr_max = int(df['year'].max())
    if period == "Last 3 years":
        return df[df['year'] >= yr_max - 2]
    if period == "Last 5 years":
        return df[df['year'] >= yr_max - 4]
    return df  # All time

def render(df):
    st.title("Artists and Tracks")

    # ── Period filter — global ─────────────────────────────────────────────
    period = st.radio(
        "Period",
        ["All time", "Last 3 years", "Last 5 years"],
        horizontal=True,
        key="art_period"
    )
    df = _filter_period(df, period)

    cutoff_1y = df["ts"].max() - pd.DateOffset(years=1)

    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "Top Artists", "Top Tracks", "Your Eras", "Artist Deep Dive", "Track Graveyard"
    ])

    # ── Tab 1: Top Artists ────────────────────────────────────────────────────
    with tab1:
        n = st.slider("Number of artists", 10, 50, 20, key="art_n")

        has_skip = "skipped" in df.columns
        agg_dict = {
            "hours": ("ms", lambda x: round(x.sum()/3600000, 2)),
            "plays": ("ms", "count"),
        }
        if has_skip:
            agg_dict["skip_rate"] = ("skipped", lambda x: round(x.mean()*100, 1))

        artist_stats = (
            df.groupby("artistName").agg(**agg_dict)
            .sort_values("hours", ascending=False)
            .head(n).reset_index()
        )

        fig = go.Figure(go.Bar(
            x=artist_stats["hours"],
            y=artist_stats["artistName"],
            orientation="h",
            marker_color=VIOLET,
            text=[str(h) + "h" for h in artist_stats["hours"]],
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>%{x:.1f}h<extra></extra>"
        ))
        fig.update_layout(
            plot_bgcolor="#111", paper_bgcolor="#111", font_color="#aaa",
            yaxis=dict(autorange="reversed", gridcolor="#1a1a1a",
                       tickfont=dict(size=12, color="#ccc")),
            xaxis=dict(gridcolor="#1a1a1a", title="Hours"),
            margin=dict(l=180, r=80, t=10, b=20),
            height=max(400, n*26)
        )
        st.plotly_chart(fig, use_container_width=True)

        if has_skip:
            st.markdown(
                "<div style='color:#A78BFA;font-size:.75em;font-weight:700;"
                "text-transform:uppercase;letter-spacing:.1em;margin:16px 0 8px;'>"
                "Skip rates</div>",
                unsafe_allow_html=True
            )
            cols = st.columns(4)
            for i, row in artist_stats.iterrows():
                sr    = row.get("skip_rate", 0)
                color = _skip_color(sr)
                with cols[i % 4]:
                    st.markdown(
                        "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
                        "border-radius:8px;padding:8px 10px;margin-bottom:6px;'>"
                        "<div style='display:flex;justify-content:space-between;'>"
                        "<span style='font-size:.78em;color:#aaa;'>"
                        + str(row["artistName"])[:22] + "</span>"
                        "<span style='font-size:.78em;font-weight:700;color:" + color + ";'>"
                        + str(sr) + "%</span>"
                        "</div></div>",
                        unsafe_allow_html=True
                    )

    # ── Tab 2: Top Tracks ─────────────────────────────────────────────────────
    with tab2:
        col_f, col_n = st.columns([3, 1])
        with col_f:
            artists_list   = ["All artists"] + sorted(df["artistName"].unique().tolist())
            selected_artist = st.selectbox("Filter by artist", artists_list, key="trk_artist")
        with col_n:
            n2 = st.slider("Tracks", 10, 50, 20, key="trk_n")

        df_t = df if selected_artist == "All artists" else df[df["artistName"] == selected_artist]

        agg2 = {
            "plays":       ("ms", "count"),
            "hours":       ("ms", lambda x: round(x.sum()/3600000, 2)),
            "last_played": ("ts", "max"),
        }
        if "skipped" in df.columns:
            agg2["skip_rate"] = ("skipped", lambda x: round(x.mean()*100, 1))

        track_stats = (
            df_t.groupby(["trackName", "artistName"]).agg(**agg2)
            .sort_values("plays", ascending=False)
            .head(n2).reset_index()
        )
        track_stats["label"]  = (
            track_stats["trackName"].str[:36] + " — " + track_stats["artistName"].str[:18]
        )
        track_stats["silent"] = track_stats["last_played"] < cutoff_1y
        bar_colors = [RED if s else VIOLET_LIGHT for s in track_stats["silent"]]

        fig2 = go.Figure(go.Bar(
            x=track_stats["plays"],
            y=track_stats["label"],
            orientation="h",
            marker_color=bar_colors,
            text=[str(p) + "x" for p in track_stats["plays"]],
            textposition="outside",
            hovertemplate="<b>%{y}</b><br>%{x} plays<extra></extra>"
        ))
        fig2.update_layout(
            plot_bgcolor="#111", paper_bgcolor="#111", font_color="#aaa",
            yaxis=dict(autorange="reversed", gridcolor="#1a1a1a",
                       tickfont=dict(size=11, color="#ccc")),
            xaxis=dict(gridcolor="#1a1a1a", title="Plays"),
            margin=dict(l=300, r=80, t=10, b=20),
            height=max(400, n2*26)
        )
        st.plotly_chart(fig2, use_container_width=True)

        st.markdown(
            "<div style='color:#888;font-size:.78em;'>"
            "<span style='color:#f87171;'>Red</span> = not played in the last 12 months. "
            "<span style='color:#A78BFA;'>Purple</span> = still active."
            "</div>",
            unsafe_allow_html=True
        )

    # ── Tab 3: Eras ───────────────────────────────────────────────────────────
    with tab3:
        st.markdown("### Top 3 Artists Per Year")
        era_rows = []
        for yr, grp in df.groupby("year"):
            top3     = grp.groupby("artistName")["ms"].sum().sort_values(ascending=False).head(3)
            total_yr = grp["ms"].sum()
            for rank, (artist, ms) in enumerate(top3.items(), 1):
                era_rows.append({
                    "Year":      yr,
                    "Rank":      rank,
                    "Artist":    artist,
                    "Hours":     round(ms/3600000, 1),
                    "% of year": str(round(ms/total_yr*100)) + "%",
                })

        era_df = pd.DataFrame(era_rows)
        top1   = era_df[era_df["Rank"] == 1].sort_values("Year", ascending=False)

        fig3 = go.Figure(go.Bar(
            x=top1["Year"], y=top1["Hours"],
            text=top1["Artist"], textposition="inside",
            marker_color=VIOLET,
            hovertemplate="%{text}<br>%{y:.1f}h<extra></extra>"
        ))
        fig3.update_layout(
            plot_bgcolor="#111", paper_bgcolor="#111", font_color="#aaa",
            xaxis=dict(gridcolor="#1a1a1a", dtick=1),
            yaxis=dict(gridcolor="#1a1a1a"),
            margin=dict(l=0, r=0, t=10, b=0), height=380
        )
        st.plotly_chart(fig3, use_container_width=True)

        pivot = era_df.pivot_table(
            index="Year", columns="Rank", values="Artist", aggfunc="first"
        )
        pivot.columns = ["#1 Artist", "#2 Artist", "#3 Artist"]
        st.dataframe(pivot.sort_index(ascending=False), use_container_width=True)

    # ── Tab 4: Artist Deep Dive ───────────────────────────────────────────────
    with tab4:
        st.markdown("### Artist Deep Dive")
        artist_list = sorted(
            df.groupby("artistName")["ms"].count()
            .sort_values(ascending=False).head(200).index.tolist()
        )
        selected = st.selectbox("Select an artist", artist_list, key="deep_artist")

        sub = df[df["artistName"] == selected]
        if sub.empty:
            st.info("No data for this artist.")
        else:
            first_play    = sub["ts"].min()
            last_play     = sub["ts"].max()
            total_h       = round(sub["ms"].sum() / 3600000, 1)
            total_p       = len(sub)
            skip_r        = round(sub["skipped"].mean() * 100, 1) if "skipped" in sub.columns else None
            silent_months = int((df["ts"].max() - last_play).days / 30)

            c1, c2, c3, c4 = st.columns(4)
            for col, val, lbl, color in [
                (c1, str(total_p),                "Total plays",  VIOLET_LIGHT),
                (c2, str(total_h) + "h",           "Total hours",  VIOLET_LIGHT),
                (c3, first_play.strftime("%b %Y"), "First play",   GREEN),
                (c4, last_play.strftime("%b %Y"),  "Last play",
                 RED if silent_months > 12 else GREEN),
            ]:
                with col:
                    st.markdown(
                        "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
                        "border-radius:10px;padding:14px;text-align:center;'>"
                        "<div style='font-size:1.4em;font-weight:900;color:" + color + ";'>"
                        + val + "</div>"
                        "<div style='font-size:.72em;color:#888;margin-top:4px;'>" + lbl + "</div>"
                        "</div>",
                        unsafe_allow_html=True
                    )

            if silent_months > 12:
                st.markdown(
                    "<div style='background:#0f0505;border:1px solid #f8717133;"
                    "border-radius:8px;padding:10px 14px;margin:12px 0;"
                    "color:#f87171;font-size:.85em;'>"
                    "Silent for " + str(silent_months) + " months. This is a forgotten artist."
                    "</div>",
                    unsafe_allow_html=True
                )

            if skip_r is not None:
                sc = _skip_color(skip_r)
                st.markdown(
                    "<div style='color:#888;font-size:.82em;margin:8px 0;'>"
                    "Skip rate: <span style='color:" + sc + ";font-weight:700;'>"
                    + str(skip_r) + "%</span></div>",
                    unsafe_allow_html=True
                )

            st.markdown("#### Plays per year")
            yearly = sub.groupby("year")["ms"].count().reset_index()
            yearly.columns = ["year", "plays"]
            fig4 = go.Figure(go.Bar(
                x=yearly["year"], y=yearly["plays"],
                marker_color=VIOLET,
                hovertemplate="%{x}: %{y} plays<extra></extra>"
            ))
            fig4.update_layout(
                plot_bgcolor="#111", paper_bgcolor="#111", font_color="#aaa",
                xaxis=dict(gridcolor="#1a1a1a", dtick=1),
                yaxis=dict(gridcolor="#1a1a1a"),
                margin=dict(l=0, r=0, t=10, b=0), height=260
            )
            st.plotly_chart(fig4, use_container_width=True)

            st.markdown("#### Top tracks")
            top_tracks = (
                sub.groupby("trackName").agg(
                    plays=("ms", "count"),
                    hours=("ms", lambda x: round(x.sum()/3600000, 1)),
                    last=("ts", "max")
                ).sort_values("plays", ascending=False).head(15).reset_index()
            )
            top_tracks["silent"]   = top_tracks["last"] < cutoff_1y
            top_tracks["last_fmt"] = top_tracks["last"].dt.strftime("%b %Y")

            cols = st.columns(2)
            for i, row in top_tracks.iterrows():
                color = RED if row["silent"] else VIOLET_LIGHT
                with cols[i % 2]:
                    st.markdown(
                        "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
                        "border-left:3px solid " + color + ";border-radius:8px;"
                        "padding:10px 14px;margin-bottom:8px;'>"
                        "<div style='font-weight:700;color:#fff;font-size:.88em;'>"
                        + str(row["trackName"]) + "</div>"
                        "<div style='display:flex;gap:10px;margin-top:4px;flex-wrap:wrap;'>"
                        "<span style='color:" + color + ";font-weight:700;font-size:.78em;'>"
                        + str(int(row["plays"])) + " plays</span>"
                        "<span style='color:#888;font-size:.78em;'>" + str(row["hours"]) + "h</span>"
                        "<span style='color:#555;font-size:.78em;'>last: " + str(row["last_fmt"]) + "</span>"
                        "</div></div>",
                        unsafe_allow_html=True
                    )

    # ── Tab 5: Track Graveyard ────────────────────────────────────────────────
    with tab5:
        st.markdown("### Track Graveyard")
        st.caption("Tracks with 20+ plays all-time. Silent for the last 12 months.")

        track_all = df.groupby(["trackName", "artistName"]).agg(
            plays=("ms", "count"),
            hours=("ms", lambda x: round(x.sum()/3600000, 1)),
            last_played=("ts", "max"),
            first_played=("ts", "min"),
        ).reset_index()

        graveyard = (
            track_all[
                (track_all["plays"] >= 20) &
                (track_all["last_played"] < cutoff_1y)
            ]
            .sort_values("plays", ascending=False)
            .head(50)
        )

        if graveyard.empty:
            st.success("No graveyard tracks found.")
        else:
            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(
                    "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
                    "border-radius:10px;padding:14px;text-align:center;'>"
                    "<div style='font-size:1.6em;font-weight:900;color:#f87171;'>"
                    + str(len(graveyard)) + "</div>"
                    "<div style='font-size:.72em;color:#888;margin-top:4px;'>forgotten tracks</div>"
                    "</div>", unsafe_allow_html=True
                )
            with c2:
                st.markdown(
                    "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
                    "border-radius:10px;padding:14px;text-align:center;'>"
                    "<div style='font-size:1.6em;font-weight:900;color:#A78BFA;'>"
                    + str(int(graveyard["plays"].sum())) + "</div>"
                    "<div style='font-size:.72em;color:#888;margin-top:4px;'>total plays in their lifetime</div>"
                    "</div>", unsafe_allow_html=True
                )
            with c3:
                avg_silence = int((df["ts"].max() - graveyard["last_played"]).dt.days.mean() / 30)
                st.markdown(
                    "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
                    "border-radius:10px;padding:14px;text-align:center;'>"
                    "<div style='font-size:1.6em;font-weight:900;color:#555;'>"
                    + str(avg_silence) + "m</div>"
                    "<div style='font-size:.72em;color:#888;margin-top:4px;'>avg months of silence</div>"
                    "</div>", unsafe_allow_html=True
                )

            st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
            cols = st.columns(2)
            for i, (_, row) in enumerate(graveyard.iterrows()):
                last    = row["last_played"].strftime("%b %Y")
                silence = int((df["ts"].max() - row["last_played"]).days / 30)
                with cols[i % 2]:
                    st.markdown(
                        "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
                        "border-left:3px solid #f87171;border-radius:8px;"
                        "padding:12px 14px;margin-bottom:8px;'>"
                        "<div style='font-weight:700;color:#fff;font-size:.9em;'>"
                        + str(row["trackName"]) + "</div>"
                        "<div style='color:#888;font-size:.78em;margin-top:2px;'>"
                        + str(row["artistName"]) + "</div>"
                        "<div style='display:flex;gap:10px;margin-top:6px;flex-wrap:wrap;'>"
                        "<span style='color:#A78BFA;font-weight:700;font-size:.78em;'>"
                        + str(int(row["plays"])) + " plays</span>"
                        "<span style='color:#888;font-size:.78em;'>last: " + last + "</span>"
                        "<span style='color:#f87171;font-size:.78em;'>"
                        + str(silence) + " months ago</span>"
                        "</div></div>",
                        unsafe_allow_html=True
                    )
