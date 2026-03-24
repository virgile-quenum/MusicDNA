import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

VIOLET_LIGHT = "#A78BFA"
VIOLET = "#7C3AED"

BENCH = {
    'hours_per_year':    400,
    'unique_artists':    500,
    'unique_tracks':     3000,
    'skip_rate':         25,
    'new_artists_year':  50,
}

def percentile_label(val, bench, higher_is_better=True):
    ratio = val / bench if bench > 0 else 1
    if higher_is_better:
        if ratio >= 3:   return "Top 1%", "#1DB954"
        if ratio >= 2:   return "Top 5%", "#A78BFA"
        if ratio >= 1.2: return "Above avg", "#A78BFA"
        if ratio >= 0.8: return "Average", "#888"
        return "Below avg", "#f59e0b"
    else:
        if ratio <= 0.5:  return "Top 5%", "#1DB954"
        if ratio <= 0.75: return "Above avg", "#A78BFA"
        if ratio <= 1.0:  return "Average", "#888"
        return "Below avg", "#f59e0b"

def render(dfm, dfd, kids_on, lib=None, playlists=None):
    st.title("🏠 Your Musical Profile")

    import score
    score.render(dfm, dfd, lib, playlists)

    my_h    = dfm['ms'].sum() / 3600000
    my_art  = dfm['artistName'].nunique()
    my_trk  = dfm['trackName'].nunique()
    skip    = dfm['skipped'].mean() * 100
    dau_h   = dfd['ms'].sum() / 3600000 if dfd is not None and not dfd.empty else 0
    yr_min  = int(dfm['year'].min())
    yr_max  = int(dfm['year'].max())
    n_years = yr_max - yr_min + 1

    total_h = my_h + dau_h
    dau_pct = (dau_h / total_h * 100) if total_h > 0 else 0

    top_artist   = dfm.groupby('artistName')['ms'].sum().idxmax()
    sat_h        = dfm[dfm['dow'] == 5]['ms'].sum() / 3600000
    peak_h       = int(dfm.groupby('hour')['ms'].sum().idxmax())
    new_per_year = dfm.sort_values('ts').groupby('artistName')['year'].min()
    avg_new      = int(new_per_year.groupby(new_per_year).size().mean())
    h_per_year   = my_h / n_years

    st.markdown(
        "<div style='background:linear-gradient(135deg,#0a0a1a,#12001a);"
        "border:1px solid " + VIOLET + ";border-radius:16px;"
        "padding:32px;margin-bottom:24px;'>"
        "<div style='font-size:.75em;color:#555;text-transform:uppercase;"
        "letter-spacing:.1em;margin-bottom:8px;'>Your Music DNA</div>"
        "<div style='font-size:1.6em;font-weight:900;color:#fff;line-height:1.4;'>"
        + str(n_years) + " years of listening.<br>"
        "<span style='color:" + VIOLET_LIGHT + ";'>" + str(int(my_h)) + " hours.</span> "
        + str(my_art) + " artists. " + str(my_trk) + " tracks."
        "</div>"
        "<div style='color:#777;margin-top:16px;font-size:.9em;line-height:1.8;'>"
        "Your #1 artist all-time is <b style='color:#fff;'>" + str(top_artist) + "</b>. "
        "You discover ~<b style='color:#fff;'>" + str(avg_new) + "</b> new artists per year. "
        "Saturday is your biggest listening day (<b style='color:#fff;'>" + str(int(sat_h)) + "h</b> total). "
        "You peak at <b style='color:#fff;'>" + str(peak_h).zfill(2) + "h</b>."
        "</div>"
        "</div>",
        unsafe_allow_html=True
    )

    c1, c2, c3, c4, c5 = st.columns(5)

    def metric_card(col, val_str, lbl, tip, bench_val, user_val, higher_is_better=True, bench_label=""):
        pct_lbl, pct_color = percentile_label(user_val, bench_val, higher_is_better)
        with col:
            st.markdown(
                "<div class='metric-card'>"
                "<div class='metric-val'>" + val_str + "</div>"
                "<div class='metric-lbl'>" + lbl + "</div>"
                "<div style='margin-top:6px;'>"
                "<span style='background:" + pct_color + "22;color:" + pct_color + ";"
                "font-size:.7em;font-weight:700;padding:2px 8px;border-radius:10px;'>"
                + pct_lbl + "</span>"
                "<span style='color:#444;font-size:.68em;margin-left:6px;'>vs avg " + bench_label + "</span>"
                "</div>"
                "</div>",
                unsafe_allow_html=True
            )
            st.caption(tip)

    metric_card(c1, str(int(my_h)) + "h",
                "Listening time (" + str(yr_min) + "–" + str(yr_max) + ")",
                str(int(h_per_year)) + "h/year. Avg active user: ~400h/year. " + str(int(my_h / n_years / 365 * 60)) + " min/day.",
                BENCH['hours_per_year'], h_per_year, True, "400h/yr")

    metric_card(c2, str(my_art), "Unique artists",
                "Avg listener: ~500 artists lifetime. Top 1% starts at ~5,000. You're at " + str(my_art) + ".",
                BENCH['unique_artists'], my_art, True, "500")

    metric_card(c3, str(my_trk), "Unique tracks",
                "Avg listener: ~3,000 tracks lifetime. Ratio " + str(round(my_trk/my_art, 1)) + " tracks/artist — lower = wider, less deep.",
                BENCH['unique_tracks'], my_trk, True, "3,000")

    metric_card(c4, str(int(skip)) + "%", "Skip rate",
                "Industry avg: ~25%. Lower = more intentional. You skip " + ("less" if skip < 25 else "more") + " than average.",
                BENCH['skip_rate'], skip, False, "25%")

    with c5:
        dau_color = "#f87171" if dau_pct > 15 else "#888"
        st.markdown(
            "<div class='metric-card'>"
            "<div class='metric-val'>" + str(int(dau_h)) + "h</div>"
            "<div class='metric-lbl'>Children's content</div>"
            "<div style='margin-top:6px;'>"
            "<span style='background:" + dau_color + "22;color:" + dau_color + ";"
            "font-size:.7em;font-weight:700;padding:2px 8px;border-radius:10px;'>"
            + str(round(dau_pct, 1)) + "% of total</span>"
            "</div>"
            "</div>",
            unsafe_allow_html=True
        )
        st.caption(
            str(round(dau_pct, 1)) + "% of your total listening is children's content. "
            + ("Significant parental footprint — see Parent Mode." if dau_pct > 10 else "Minor presence.")
        )

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("## Listening by Year")
        yearly = dfm.groupby('year')['ms'].sum().reset_index()
        yearly['hours'] = yearly['ms'] / 3600000
        fig = px.bar(yearly, x='year', y='hours',
                     color_discrete_sequence=[VIOLET],
                     labels={'hours': 'Hours', 'year': 'Year'})
        fig.add_hline(y=BENCH['hours_per_year'], line_dash="dot",
                      line_color="#555",
                      annotation_text="avg user 400h",
                      annotation_font_color="#555")
        fig.update_layout(
            plot_bgcolor='#111', paper_bgcolor='#111',
            font_color='#888',
            xaxis=dict(gridcolor='#1a1a1a', dtick=1),
            yaxis=dict(gridcolor='#1a1a1a'),
            margin=dict(l=0, r=0, t=10, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("## Your Eras — What Each Year Meant")
        sorted_years = sorted(dfm['year'].unique())
        prev_top     = None
        prev_hours   = None
        era_rows     = []
        first_seen_all = dfm.sort_values('ts').groupby('artistName')['year'].min()

        for yr in sorted_years:
            grp        = dfm[dfm['year'] == yr]
            top        = grp.groupby('artistName')['ms'].sum()
            top_artist_yr = top.idxmax()
            hours      = round(grp['ms'].sum() / 3600000, 0)
            top_hours  = top.max() / 3600000
            concentration = top_hours / hours * 100 if hours > 0 else 0
            skip_yr    = grp['skipped'].mean() * 100
            new_this_year = int((first_seen_all == yr).sum())

            parts = []
            if prev_hours and hours > prev_hours * 1.4:
                parts.append("Listening exploded")
            elif prev_hours and hours < prev_hours * 0.6:
                parts.append("You pulled back")
            elif hours > 700:
                parts.append("One of your biggest years")
            elif hours < 200:
                parts.append("A quiet year")

            if prev_top and top_artist_yr == prev_top:
                parts.append(top_artist_yr + " again — this was becoming something serious")
            elif concentration > 30:
                parts.append(top_artist_yr + " dominated (" + str(int(concentration)) + "% of the year)")
            else:
                parts.append(top_artist_yr + " led")

            if new_this_year > 300:
                parts.append(str(new_this_year) + " new artists discovered")
            elif new_this_year < 50:
                parts.append("focused, less exploratory")

            if skip_yr > 35:
                parts.append("restless year")
            elif skip_yr < 10:
                parts.append("very intentional")

            narrative = ". ".join(parts[:2]) + "."
            era_rows.append({
                'year': yr, 'artist': top_artist_yr,
                'hours': int(hours), 'narrative': narrative,
            })
            prev_top   = top_artist_yr
            prev_hours = hours

        for row in sorted(era_rows, key=lambda x: -x['year']):
            st.markdown(
                "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
                "border-left:3px solid " + VIOLET + ";border-radius:8px;"
                "padding:12px 16px;margin-bottom:8px;'>"
                "<div style='display:flex;justify-content:space-between;align-items:center;'>"
                "<div style='font-size:1.1em;font-weight:900;color:#fff;'>"
                + str(row['year']) + "</div>"
                "<div style='color:#555;font-size:.75em;'>" + str(row['hours']) + "h</div>"
                "</div>"
                "<div style='font-weight:700;color:" + VIOLET_LIGHT + ";font-size:.88em;margin-top:3px;'>"
                + str(row['artist']) + "</div>"
                "<div style='color:#555;font-size:.78em;margin-top:4px;font-style:italic;'>"
                + str(row['narrative']) + "</div>"
                "</div>",
                unsafe_allow_html=True
            )

    st.markdown("---")

    if dfd is not None and not dfd.empty and dau_h > 0:
        st.markdown("## Children's Content — Share Over Time")
        dfm_ym = dfm.groupby('ym')['ms'].sum().reset_index()
        dfm_ym.columns = ['ym', 'music_ms']
        dfd_ym = dfd.groupby('ym')['ms'].sum().reset_index()
        dfd_ym.columns = ['ym', 'kids_ms']
        merged = dfm_ym.merge(dfd_ym, on='ym', how='outer').fillna(0)
        merged['total']    = merged['music_ms'] + merged['kids_ms']
        merged['kids_pct'] = merged['kids_ms'] / merged['total'] * 100
        merged['ym_dt']    = pd.to_datetime(merged['ym'])
        merged = merged.sort_values('ym_dt')

        fig2 = go.Figure()
        fig2.add_trace(go.Scatter(
            x=merged['ym_dt'], y=merged['kids_pct'],
            fill='tozeroy', line=dict(color='#f87171', width=1.5),
            fillcolor='rgba(248,113,113,0.15)',
            name="Children's %"
        ))
        fig2.update_layout(
            plot_bgcolor='#111', paper_bgcolor='#111',
            font_color='#888', height=220,
            xaxis=dict(gridcolor='#1a1a1a'),
            yaxis=dict(gridcolor='#1a1a1a', ticksuffix='%', range=[0, 100]),
            margin=dict(l=0, r=0, t=10, b=0),
            showlegend=False
        )
        st.plotly_chart(fig2, use_container_width=True)
        st.caption(
            "Children's content as % of total monthly listening. "
            "Peak = " + str(round(merged['kids_pct'].max(), 1)) + "% in " +
            str(merged.loc[merged['kids_pct'].idxmax(), 'ym']) + ". "
            "Current = " + str(round(merged['kids_pct'].iloc[-1], 1)) + "%."
        )
        st.markdown("---")

    st.markdown("## What's Inside This App")
    sections = [
        ("🎤", "Artists & Tracks",  "Top artists and tracks all-time, with yearly evolution.", False),
        ("🕐", "Time Patterns",     "Hour by hour, day by day. Your listening heatmap across 12+ years.", False),
        ("👶", "Parent Mode",       "How parenthood rewrote your Spotify. The exact month it happened — in data.", False),
        ("💔", "Likes Autopsy",     "What you saved vs. what you actually play. Identity vs. reality.", True),
        ("📋", "Playlist Autopsy",  "Which playlists you use vs. which are archives you built and forgot.", True),
        ("😳", "Hall of Shame",     "Tracks you play constantly — never liked, never saved. Without mercy.", False),
        ("⭐", "Celebrity Twin",    "Which public figures share your musical taste based on your actual data.", False),
        ("🔮", "Musical Horoscope", "Your musical sign, curse, gift and prediction — from 12 years of behaviour.", False),
    ]
    cols = st.columns(2)
    for i, (icon, title, desc, needs_std) in enumerate(sections):
        with cols[i % 2]:
            border = "#f59e0b" if needs_std else VIOLET
            extra  = (" <span style='color:#f59e0b;font-size:.74em;'>⚠ needs standard export</span>"
                      if needs_std else "")
            st.markdown(
                "<div style='background:#0f0f0f;border:1px solid " + border + "22;"
                "border-left:3px solid " + border + ";border-radius:8px;"
                "padding:14px;margin-bottom:10px;'>"
                "<div style='font-weight:700;margin-bottom:5px;'>"
                + icon + " " + title + extra + "</div>"
                "<div style='color:#666;font-size:.82em;line-height:1.5;'>" + desc + "</div>"
                "</div>",
                unsafe_allow_html=True
            )
