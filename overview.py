import streamlit as st
import pandas as pd
import plotly.express as px

VIOLET_LIGHT = "#A78BFA"
VIOLET = "#7C3AED"

def render(dfm, dfd, kids_on):
    st.title("🏠 Your Musical Profile")

    my_h   = dfm['ms'].sum() / 3600000
    my_art = dfm['artistName'].nunique()
    my_trk = dfm['trackName'].nunique()
    skip   = dfm['skipped'].mean() * 100
    dau_h  = dfd['ms'].sum() / 3600000 if dfd is not None and not dfd.empty else 0
    yr_min = int(dfm['year'].min())
    yr_max = int(dfm['year'].max())

    top_artist  = dfm.groupby('artistName')['ms'].sum().idxmax()
    sat_h       = dfm[dfm['dow'] == 5]['ms'].sum() / 3600000
    peak_h      = int(dfm.groupby('hour')['ms'].sum().idxmax())
    new_per_year = dfm.sort_values('ts').groupby('artistName')['year'].min()
    avg_new     = int(new_per_year.groupby(new_per_year).size().mean())

    st.markdown(
        "<div style='background:linear-gradient(135deg,#0a0a1a,#12001a);"
        "border:1px solid " + VIOLET + ";border-radius:16px;"
        "padding:32px;margin-bottom:24px;'>"
        "<div style='font-size:.75em;color:#555;text-transform:uppercase;"
        "letter-spacing:.1em;margin-bottom:8px;'>Your Music DNA</div>"
        "<div style='font-size:1.6em;font-weight:900;color:#fff;line-height:1.4;'>"
        + str(yr_max - yr_min + 1) + " years of listening.<br>"
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
    metrics = [
        (c1, str(int(my_h)) + "h",
         "Listening time (" + str(yr_min) + "–" + str(yr_max) + ")",
         "~" + str(int(my_h / (yr_max - yr_min + 1) / 365 * 60)) + " min/day on average across " + str(yr_max - yr_min + 1) + " years."),
        (c2, str(my_art),
         "Unique artists",
         "Top 1% globally is ~5,000+. Breadth of taste — how wide you go."),
        (c3, str(my_trk),
         "Unique tracks",
         "Tracks vs. artists ratio shows if you go deep or wide per artist."),
        (c4, str(int(skip)) + "%",
         "Skip rate",
         "% of plays stopped early. Industry avg ~25%. Lower = more intentional."),
        (c5, str(int(dau_h)) + "h",
         "Children's content",
         "Children's content detected and filtered out. Toggle sidebar to include."),
    ]
    for col, val, lbl, tip in metrics:
        with col:
            st.markdown(
                "<div class='metric-card'>"
                "<div class='metric-val'>" + val + "</div>"
                "<div class='metric-lbl'>" + lbl + "</div>"
                "</div>",
                unsafe_allow_html=True
            )
            st.caption(tip)

    st.markdown("---")

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("## Listening by Year")
        yearly = dfm.groupby('year')['ms'].sum().reset_index()
        yearly['hours'] = yearly['ms'] / 3600000
        fig = px.bar(yearly, x='year', y='hours',
                     color_discrete_sequence=[VIOLET],
                     labels={'hours': 'Hours', 'year': 'Year'})
        fig.update_layout(
            plot_bgcolor='#111', paper_bgcolor='#111',
            font_color='#888',
            xaxis=dict(gridcolor='#1a1a1a', dtick=1),
            yaxis=dict(gridcolor='#1a1a1a'),
            margin=dict(l=0, r=0, t=10, b=0)
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("## Your Eras — #1 Artist Per Year")
        era_rows = []
        for yr, grp in dfm.groupby('year'):
            top = grp.groupby('artistName')['ms'].sum()
            era_rows.append({
                'Year':      yr,
                'Artist':    top.idxmax(),
                'Hours':     round(top.max() / 3600000, 1),
                'Total hrs': round(grp['ms'].sum() / 3600000, 0),
                'Artists':   grp['artistName'].nunique()
            })
        era_df = (
            pd.DataFrame(era_rows)
            .sort_values('Year', ascending=False)  # antéchronologique
            .set_index('Year')
        )
        st.dataframe(era_df, use_container_width=True)

    st.markdown("---")
    st.markdown("## What's Inside This App")
    sections = [
        ("🎤", "Artists & Tracks",
         "Top artists and tracks all-time, with yearly evolution.", False),
        ("🕐", "Time Patterns",
         "Hour by hour, day by day. Your listening heatmap across 12+ years.", False),
        ("👶", "Parent Mode",
         "How parenthood rewrote your Spotify. The exact month your child arrived — in data.", False),
        ("💔", "Likes Autopsy",
         "What you saved vs. what you actually play. Identity vs. reality.", True),
        ("📋", "Playlist Autopsy",
         "Which playlists you use vs. which are archives you built and forgot.", True),
        ("😳", "Hall of Shame",
         "Tracks you play constantly — never liked, never saved. Without mercy.", False),
        ("⭐", "Celebrity Twin",
         "Which public figures share your musical taste based on your actual data.", False),
        ("🔮", "Musical Horoscope",
         "Your musical sign, curse, gift and prediction — from 12 years of behaviour.", False),
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
