import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import numpy as np
import pandas as pd

VIOLET       = "#7C3AED"
VIOLET_LIGHT = "#A78BFA"
GREEN        = "#1DB954"
AMBER        = "#f59e0b"
DAYS = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]

def _insight(text):
    st.markdown(
        "<div class='insight'>" + text + "</div>",
        unsafe_allow_html=True
    )

def _section(text):
    st.markdown(
        "<div style='color:#A78BFA;font-size:.75em;font-weight:700;"
        "text-transform:uppercase;letter-spacing:.1em;margin:20px 0 10px;'>"
        + text + "</div>",
        unsafe_allow_html=True
    )

def render(df):
    st.title("Time Patterns")

    peak_h   = int(df.groupby("hour")["ms"].sum().idxmax())
    peak_d   = DAYS[int(df.groupby("dow")["ms"].sum().idxmax())]
    peak_d_h = round(df[df["dow"] == df.groupby("dow")["ms"].sum().idxmax()]["ms"].sum() / 3600000)
    total_h  = round(df["ms"].sum() / 3600000)

    # morning = 5-11, afternoon = 12-17, evening = 18-22, night = 23-4
    hour_ms = df.groupby("hour")["ms"].sum()
    morning   = sum(hour_ms.get(h, 0) for h in range(5, 12))
    afternoon = sum(hour_ms.get(h, 0) for h in range(12, 18))
    evening   = sum(hour_ms.get(h, 0) for h in range(18, 23))
    night     = sum(hour_ms.get(h, 0) for h in list(range(23, 24)) + list(range(0, 5)))
    slot_map  = {"Morning (5-11h)": morning, "Afternoon (12-17h)": afternoon,
                 "Evening (18-22h)": evening, "Night (23-4h)": night}
    dominant_slot = max(slot_map, key=slot_map.get)

    # ── Hero ─────────────────────────────────────────────────────────────────
    st.markdown(
        "<div style='background:linear-gradient(135deg,#0a0a1a,#12001a);"
        "border:1px solid #7C3AED;border-radius:16px;padding:28px;margin-bottom:24px;'>"
        "<div style='font-size:.75em;color:#555;text-transform:uppercase;"
        "letter-spacing:.1em;margin-bottom:10px;'>Your listening rhythm</div>"
        "<div style='display:grid;grid-template-columns:repeat(3,1fr);gap:16px;'>"

        "<div>"
        "<div style='font-size:2.2em;font-weight:900;color:#A78BFA;'>" + str(peak_h).zfill(2) + "h</div>"
        "<div style='color:#555;font-size:.8em;margin-top:2px;'>peak hour</div>"
        "</div>"

        "<div>"
        "<div style='font-size:2.2em;font-weight:900;color:#A78BFA;'>" + peak_d + "</div>"
        "<div style='color:#555;font-size:.8em;margin-top:2px;'>biggest day</div>"
        "</div>"

        "<div>"
        "<div style='font-size:2.2em;font-weight:900;color:#A78BFA;'>" + dominant_slot.split()[0] + "</div>"
        "<div style='color:#555;font-size:.8em;margin-top:2px;'>dominant slot</div>"
        "</div>"

        "</div>"
        "<div style='color:#666;font-size:.85em;margin-top:16px;line-height:1.8;'>"
        "You peak at <b style='color:#fff;'>" + str(peak_h).zfill(2) + "h</b>. "
        + peak_d + " is your biggest listening day. "
        "Most of your listening happens in the <b style='color:#fff;'>"
        + dominant_slot.lower() + "</b>."
        "</div>"
        "</div>",
        unsafe_allow_html=True
    )

    tab1, tab2, tab3, tab4 = st.tabs([
        "Patterns", "Evolution Over Time", "Seasons", "Binge Sessions"
    ])

    # ── Tab 1: base patterns ──────────────────────────────────────────────────
    with tab1:
        c1, c2 = st.columns(2)
        with c1:
            _section("By Hour of Day")
            hourly = df.groupby("hour")["ms"].sum().reindex(range(24), fill_value=0).reset_index()
            hourly.columns = ["hour", "ms"]
            hourly["hours"] = hourly["ms"] / 3600000
            fig = px.bar(hourly, x="hour", y="hours", color_discrete_sequence=[VIOLET])
            fig.update_layout(plot_bgcolor="#111", paper_bgcolor="#111", font_color="#888",
                              xaxis=dict(gridcolor="#222", tickmode="linear"),
                              yaxis=dict(gridcolor="#222"), margin=dict(l=0,r=0,t=10,b=0))
            st.plotly_chart(fig, use_container_width=True)

        with c2:
            _section("By Day of Week")
            dow = df.groupby("dow")["ms"].sum().reindex(range(7), fill_value=0).reset_index()
            dow.columns = ["dow", "ms"]
            dow["hours"] = dow["ms"] / 3600000
            dow["day"]   = DAYS
            fig2 = px.bar(dow, x="day", y="hours", color_discrete_sequence=[VIOLET_LIGHT])
            fig2.update_layout(plot_bgcolor="#111", paper_bgcolor="#111", font_color="#888",
                               xaxis=dict(gridcolor="#222"), yaxis=dict(gridcolor="#222"),
                               margin=dict(l=0,r=0,t=10,b=0))
            st.plotly_chart(fig2, use_container_width=True)

        _section("Heatmap — Hour x Day")
        hm = np.zeros((7, 24))
        for _, row in df.iterrows():
            hm[int(row["dow"]), int(row["hour"])] += row["ms"] / 3600000
        hm = np.round(hm, 1)
        fig3 = go.Figure(data=go.Heatmap(
            z=hm, x=[f"{h:02d}h" for h in range(24)], y=DAYS,
            colorscale=[[0, "#111"], [0.01, "#0a3d1f"], [1, VIOLET]],
            hoverongaps=False, showscale=True
        ))
        fig3.update_layout(plot_bgcolor="#111", paper_bgcolor="#111", font_color="#888",
                           margin=dict(l=0,r=0,t=10,b=0), height=280)
        st.plotly_chart(fig3, use_container_width=True)

        _section("Monthly Volume")
        monthly = df.groupby("ym")["ms"].sum().reset_index()
        monthly["hours"] = monthly["ms"] / 3600000
        fig4 = px.area(monthly, x="ym", y="hours", color_discrete_sequence=[VIOLET])
        fig4.update_layout(plot_bgcolor="#111", paper_bgcolor="#111", font_color="#888",
                           xaxis=dict(gridcolor="#222", tickangle=45),
                           yaxis=dict(gridcolor="#222"), margin=dict(l=0,r=0,t=10,b=0))
        st.plotly_chart(fig4, use_container_width=True)

    # ── Tab 2: evolution over time ────────────────────────────────────────────
    with tab2:
        st.markdown("### How your listening rhythm changed year by year")
        st.caption("Peak hour and dominant time slot per year.")

        years = sorted(df["year"].unique())
        year_rows = []
        for yr in years:
            sub      = df[df["year"] == yr]
            ph       = int(sub.groupby("hour")["ms"].sum().idxmax()) if len(sub) > 0 else 0
            pd_idx   = int(sub.groupby("dow")["ms"].sum().idxmax()) if len(sub) > 0 else 0
            h_ms     = sub.groupby("hour")["ms"].sum()
            m_slot   = max(slot_map.keys(), key=lambda s: sum(
                h_ms.get(h, 0) for h in (
                    range(5,12) if s.startswith("Morning") else
                    range(12,18) if s.startswith("Afternoon") else
                    range(18,23) if s.startswith("Evening") else
                    list(range(23,24)) + list(range(0,5))
                )
            ))
            year_rows.append({
                "year": yr,
                "peak_hour": ph,
                "peak_day":  DAYS[pd_idx],
                "slot":      m_slot.split()[0],
                "total_h":   round(sub["ms"].sum() / 3600000),
            })

        yr_df = pd.DataFrame(year_rows).sort_values("year", ascending=False)

        # peak hour line chart
        fig_ph = go.Figure()
        fig_ph.add_trace(go.Scatter(
            x=yr_df["year"][::-1], y=yr_df["peak_hour"][::-1],
            mode="lines+markers+text",
            text=[str(h).zfill(2) + "h" for h in yr_df["peak_hour"][::-1]],
            textposition="top center",
            line=dict(color=VIOLET_LIGHT, width=2),
            marker=dict(size=8),
            name="Peak hour"
        ))
        fig_ph.update_layout(
            plot_bgcolor="#111", paper_bgcolor="#111", font_color="#888",
            xaxis=dict(gridcolor="#1e1e1e", tickformat="d"),
            yaxis=dict(gridcolor="#1e1e1e", title="Hour", range=[0, 23],
                       ticktext=["00h","06h","12h","18h","23h"],
                       tickvals=[0,6,12,18,23]),
            margin=dict(l=0,r=0,t=20,b=0), height=300
        )
        st.plotly_chart(fig_ph, use_container_width=True)

        # table
        st.dataframe(
            yr_df.rename(columns={
                "year": "Year", "peak_hour": "Peak Hour",
                "peak_day": "Peak Day", "slot": "Dominant Slot", "total_h": "Total Hours"
            }),
            use_container_width=True, hide_index=True
        )

        # insight
        if len(yr_df) >= 2:
            first_h = yr_df["peak_hour"].iloc[-1]
            last_h  = yr_df["peak_hour"].iloc[0]
            if abs(last_h - first_h) >= 2:
                direction = "later" if last_h > first_h else "earlier"
                _insight(
                    "Your peak listening hour has shifted <b>" + str(abs(last_h - first_h))
                    + " hours " + direction + "</b> since "
                    + str(int(yr_df["year"].iloc[-1])) + "."
                )

    # ── Tab 3: seasons ────────────────────────────────────────────────────────
    with tab3:
        st.markdown("### Listening seasons")
        st.caption("Which months and seasons you listen most — across all years.")

        MONTH_NAMES = ["Jan","Feb","Mar","Apr","May","Jun",
                       "Jul","Aug","Sep","Oct","Nov","Dec"]
        monthly_avg = (
            df.groupby("month")["ms"].sum() / df["year"].nunique()
        ).reindex(range(1, 13), fill_value=0).reset_index()
        monthly_avg.columns = ["month", "ms"]
        monthly_avg["hours"] = (monthly_avg["ms"] / 3600000).round(1)
        monthly_avg["name"]  = [MONTH_NAMES[m-1] for m in monthly_avg["month"]]

        fig_s = px.bar(
            monthly_avg, x="name", y="hours",
            color_discrete_sequence=[VIOLET],
            labels={"hours": "Avg hours/year", "name": "Month"}
        )
        fig_s.update_layout(
            plot_bgcolor="#111", paper_bgcolor="#111", font_color="#888",
            xaxis=dict(gridcolor="#222"), yaxis=dict(gridcolor="#222"),
            margin=dict(l=0,r=0,t=10,b=0)
        )
        st.plotly_chart(fig_s, use_container_width=True)

        # season breakdown
        seasons = {
            "Winter (Dec-Feb)": [12, 1, 2],
            "Spring (Mar-May)": [3, 4, 5],
            "Summer (Jun-Aug)": [6, 7, 8],
            "Autumn (Sep-Nov)": [9, 10, 11],
        }
        season_h = {}
        for name, months in seasons.items():
            season_h[name] = round(
                df[df["month"].isin(months)]["ms"].sum() / 3600000 / df["year"].nunique(), 1
            )
        peak_season = max(season_h, key=season_h.get)

        c1, c2, c3, c4 = st.columns(4)
        for col, (name, hrs) in zip([c1, c2, c3, c4], season_h.items()):
            color = VIOLET_LIGHT if name == peak_season else "#555"
            with col:
                st.markdown(
                    "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
                    "border-radius:10px;padding:14px;text-align:center;'>"
                    "<div style='font-size:1.4em;font-weight:900;color:" + color + ";'>"
                    + str(hrs) + "h</div>"
                    "<div style='font-size:.72em;color:#555;margin-top:4px;'>"
                    + name + "</div>"
                    "</div>",
                    unsafe_allow_html=True
                )

        _insight(
            "Your peak season is <b>" + peak_season + "</b> — "
            + str(season_h[peak_season]) + "h on average per year."
        )

    # ── Tab 4: binge sessions ─────────────────────────────────────────────────
    with tab4:
        st.markdown("### Binge sessions")
        st.caption("Consecutive listening sessions over 2 hours. Detected from your history.")

        df_sorted = df.sort_values("ts").copy()
        df_sorted["gap"] = df_sorted["ts"].diff().dt.total_seconds().fillna(0)
        df_sorted["session_id"] = (df_sorted["gap"] > 1800).cumsum()

        sessions = df_sorted.groupby("session_id").agg(
            start=("ts", "min"),
            end=("ts", "max"),
            plays=("trackName", "count"),
            hours=("ms", lambda x: round(x.sum() / 3600000, 1)),
            artists=("artistName", "nunique"),
        ).reset_index(drop=True)

        binge = sessions[sessions["hours"] >= 2].sort_values("hours", ascending=False)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(
                "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
                "border-radius:10px;padding:14px;text-align:center;'>"
                "<div style='font-size:1.6em;font-weight:900;color:#A78BFA;'>"
                + str(len(binge)) + "</div>"
                "<div style='font-size:.72em;color:#555;margin-top:4px;'>binge sessions (2h+)</div>"
                "</div>", unsafe_allow_html=True
            )
        with c2:
            longest = round(binge["hours"].max(), 1) if not binge.empty else 0
            st.markdown(
                "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
                "border-radius:10px;padding:14px;text-align:center;'>"
                "<div style='font-size:1.6em;font-weight:900;color:#A78BFA;'>"
                + str(longest) + "h</div>"
                "<div style='font-size:.72em;color:#555;margin-top:4px;'>longest session</div>"
                "</div>", unsafe_allow_html=True
            )
        with c3:
            avg_b = round(binge["hours"].mean(), 1) if not binge.empty else 0
            st.markdown(
                "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
                "border-radius:10px;padding:14px;text-align:center;'>"
                "<div style='font-size:1.6em;font-weight:900;color:#A78BFA;'>"
                + str(avg_b) + "h</div>"
                "<div style='font-size:.72em;color:#555;margin-top:4px;'>avg binge length</div>"
                "</div>", unsafe_allow_html=True
            )

        if not binge.empty:
            st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
            _section("Top 20 longest sessions")
            top_binge = binge.head(20).copy()
            top_binge["date"] = top_binge["start"].dt.strftime("%d %b %Y")
            top_binge["time"] = top_binge["start"].dt.strftime("%Hh")

            cols = st.columns(2)
            for i, (_, row) in enumerate(top_binge.iterrows()):
                with cols[i % 2]:
                    st.markdown(
                        "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
                        "border-left:3px solid #7C3AED;border-radius:8px;"
                        "padding:12px;margin-bottom:8px;'>"
                        "<div style='display:flex;justify-content:space-between;'>"
                        "<span style='font-weight:700;color:#fff;'>" + str(row["date"]) + "</span>"
                        "<span style='color:#A78BFA;font-weight:900;'>" + str(row["hours"]) + "h</span>"
                        "</div>"
                        "<div style='color:#555;font-size:.78em;margin-top:4px;'>"
                        + str(int(row["plays"])) + " plays | "
                        + str(int(row["artists"])) + " artists | started at " + str(row["time"])
                        + "</div>"
                        "</div>",
                        unsafe_allow_html=True
                    )

            # binge sessions by year
            binge["year"] = binge["start"].dt.year
            binge_by_year = binge.groupby("year").agg(
                count=("hours", "count"),
                total_h=("hours", "sum")
            ).reset_index()

            _section("Binge sessions per year")
            fig_b = go.Figure()
            fig_b.add_trace(go.Bar(
                x=binge_by_year["year"], y=binge_by_year["count"],
                marker_color=VIOLET, name="Sessions"
            ))
            fig_b.update_layout(
                plot_bgcolor="#111", paper_bgcolor="#111", font_color="#888",
                xaxis=dict(gridcolor="#1e1e1e", tickformat="d"),
                yaxis=dict(gridcolor="#1e1e1e", title="Number of binge sessions"),
                margin=dict(l=0,r=0,t=10,b=0), height=260
            )
            st.plotly_chart(fig_b, use_container_width=True)

            peak_binge_year = binge_by_year.loc[binge_by_year["count"].idxmax(), "year"]
            _insight(
                "Your biggest binge year was <b>" + str(int(peak_binge_year)) + "</b> with "
                + str(int(binge_by_year.loc[binge_by_year["year"]==peak_binge_year, "count"].values[0]))
                + " sessions over 2 hours."
            )
