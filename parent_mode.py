import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from filters import detect_child_cultures

VIOLET       = "#7C3AED"
VIOLET_LIGHT = "#A78BFA"
GREEN        = "#1DB954"
AMBER        = "#f59e0b"
RED          = "#f87171"

def render(dfm, dfd, all_records):
    st.title("👶 Parent Mode")
    st.markdown("*How parenthood rewrote your Spotify account.*")

    if dfd is None or dfd.empty:
        st.info("No children's content detected in your data.")
        return

    all_df        = pd.concat([dfm, dfd])
    monthly_total = all_df.groupby('ym')['ms'].sum()
    monthly_kids  = dfd.groupby('ym')['ms'].sum()
    parent_score  = (monthly_kids / monthly_total * 100).fillna(0).round(1).reset_index()
    parent_score.columns = ['ym', 'pct']

    # ── Graph ─────────────────────────────────────────────────────────────────
    st.markdown(
        "<div style='color:#A78BFA;font-size:.75em;font-weight:700;"
        "text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px;'>"
        "Children's content as % of total monthly listening</div>",
        unsafe_allow_html=True
    )

    fig = go.Figure()
    fig.add_scatter(
        x=parent_score['ym'], y=parent_score['pct'],
        fill='tozeroy', line_color='#e74c3c',
        fillcolor='rgba(231,76,60,0.15)', name="Children's %"
    )
    fig.add_hline(
        y=10, line_dash='dot', line_color='#f39c12',
        annotation_text='10% threshold', annotation_position='top left',
        annotation_font_color='#888'
    )
    fig.update_layout(
        plot_bgcolor='#111', paper_bgcolor='#111', font_color='#888',
        xaxis=dict(gridcolor='#222', tickangle=45),
        yaxis=dict(gridcolor='#222', title='% of monthly listening', ticksuffix='%'),
        margin=dict(l=0, r=0, t=20, b=0), height=350
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Key metrics ───────────────────────────────────────────────────────────
    peak_month   = parent_score.loc[parent_score['pct'].idxmax()]
    first_kids   = dfd.sort_values('ts').iloc[0]
    above_10     = parent_score[parent_score['pct'] > 10]
    total_kids_h = dfd['ms'].sum() / 3600000
    total_all_h  = all_df['ms'].sum() / 3600000
    overall_pct  = int(total_kids_h / total_all_h * 100)

    c1, c2, c3, c4 = st.columns(4)
    for col, val, lbl in [
        (c1, first_kids['ts'].strftime('%b %Y'),
             "First time you played it"),
        (c2, str(int(peak_month['pct'])) + "%",
             "Peak month (" + str(peak_month['ym']) + ")"),
        (c3, str(len(above_10)),
             "Months above 10% children"),
        (c4, str(overall_pct) + "%",
             "Overall children's share of all listening"),
    ]:
        with col:
            st.markdown(
                "<div class='metric-card'>"
                "<div class='metric-val'>" + val + "</div>"
                "<div class='metric-lbl'>" + lbl + "</div>"
                "</div>",
                unsafe_allow_html=True
            )

    # ── Child profile ─────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        "<div style='color:#A78BFA;font-size:.75em;font-weight:700;"
        "text-transform:uppercase;letter-spacing:.1em;margin-bottom:12px;'>"
        "Child Profile — estimated from listening data</div>",
        unsafe_allow_html=True
    )

    significant = parent_score[parent_score['pct'] >= 5]
    if not significant.empty:
        first_significant_ym = significant.iloc[0]['ym']
        first_date = pd.Timestamp(first_significant_ym + "-01")
    else:
        first_date = first_kids['ts']

    now       = pd.Timestamp(datetime.now())
    age_years = (now - first_date).days / 365.25
    age_est   = int(age_years)
    age_range = str(age_est) + "–" + str(age_est + 1) + " years old"

    cultures = detect_child_cultures(dfd)
    dominant_culture  = list(cultures.keys())[0] if cultures else "Unknown"
    secondary_culture = list(cultures.keys())[1] if len(cultures) > 1 else None

    lang_map = {
        "French":                 "French",
        "Brazilian / Portuguese": "Portuguese",
        "Indian / Bollywood":     "Hindi",
        "English":                "English",
        "African / Afrobeats":    "French / local",
    }
    dominant_lang  = lang_map.get(dominant_culture, "Unknown")
    secondary_lang = lang_map.get(secondary_culture, None) if secondary_culture else None

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
            "border-radius:10px;padding:16px;'>"
            "<div style='color:#888;font-size:.72em;text-transform:uppercase;"
            "letter-spacing:.06em;margin-bottom:6px;'>Estimated age</div>"
            "<div style='font-size:1.4em;font-weight:900;color:#A78BFA;'>"
            + age_range + "</div>"
            "<div style='color:#555;font-size:.72em;margin-top:4px;'>"
            "Based on first children's content detected in your account</div>"
            "</div>",
            unsafe_allow_html=True
        )
    with c2:
        lang_str = dominant_lang
        if secondary_lang and secondary_lang != dominant_lang:
            lang_str += " + " + secondary_lang
        st.markdown(
            "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
            "border-radius:10px;padding:16px;'>"
            "<div style='color:#888;font-size:.72em;text-transform:uppercase;"
            "letter-spacing:.06em;margin-bottom:6px;'>Primary language(s)</div>"
            "<div style='font-size:1.4em;font-weight:900;color:#A78BFA;'>"
            + lang_str + "</div>"
            "<div style='color:#555;font-size:.72em;margin-top:4px;'>"
            "Inferred from most-played children's artists</div>"
            "</div>",
            unsafe_allow_html=True
        )
    with c3:
        culture_str = dominant_culture
        if secondary_culture:
            culture_str += " + " + secondary_culture
        st.markdown(
            "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
            "border-radius:10px;padding:16px;'>"
            "<div style='color:#888;font-size:.72em;text-transform:uppercase;"
            "letter-spacing:.06em;margin-bottom:6px;'>Cultural influences</div>"
            "<div style='font-size:1.4em;font-weight:900;color:#A78BFA;'>"
            + culture_str + "</div>"
            "<div style='color:#555;font-size:.72em;margin-top:4px;'>"
            + ("Strong secondary culture detected" if secondary_culture else "Single dominant culture") +
            "</div></div>",
            unsafe_allow_html=True
        )

    if cultures:
        st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
        culture_items = ""
        for cult, hrs in list(cultures.items())[:5]:
            culture_items += (
                "<div style='display:flex;justify-content:space-between;"
                "padding:6px 0;border-bottom:1px solid #1a1a1a;'>"
                "<span style='color:#aaa;font-size:.85em;'>" + cult + "</span>"
                "<span style='color:#A78BFA;font-size:.85em;font-weight:700;'>"
                + str(hrs) + "h</span>"
                "</div>"
            )
        st.markdown(
            "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
            "border-radius:10px;padding:16px;'>"
            "<div style='color:#888;font-size:.72em;text-transform:uppercase;"
            "letter-spacing:.06em;margin-bottom:10px;'>Hours by culture</div>"
            + culture_items + "</div>",
            unsafe_allow_html=True
        )

    # ── Child musical evolution ───────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        "<div style='color:#A78BFA;font-size:.75em;font-weight:700;"
        "text-transform:uppercase;letter-spacing:.1em;margin-bottom:12px;'>"
        "The musical evolution of your child</div>",
        unsafe_allow_html=True
    )

    eras = [
        ('🍼 Lullaby Era',      2020, 2021, "Newborn / infant — music on loop at 3am"),
        ('🧒 Childhood Era',    2022, 2023, "Growing up — nursery rhymes, stories"),
        ('🎵 Their Own Taste',  2024, 2026, "They have opinions now"),
    ]
    cols = st.columns(3)
    for col, (era_name, y1, y2, desc) in zip(cols, eras):
        era_df = dfd[(dfd['year'] >= y1) & (dfd['year'] <= y2)]
        with col:
            if era_df.empty:
                st.markdown(
                    "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
                    "border-radius:10px;padding:14px;'>"
                    "<div style='font-weight:800;color:#fff;margin-bottom:4px;'>"
                    + era_name + "</div>"
                    "<div style='color:#555;font-size:.78em;margin-bottom:8px;'>" + desc + "</div>"
                    "<div style='color:#333;font-size:.78em;'>No data for this period.</div>"
                    "</div>",
                    unsafe_allow_html=True
                )
            else:
                top = era_df.groupby('artistName')['ms'].sum().sort_values(ascending=False).head(5)
                hrs = era_df['ms'].sum() / 3600000
                items = ""
                for artist, ms in top.items():
                    items += (
                        "<div style='color:#aaa;font-size:.78em;padding:3px 0;'>"
                        "· " + str(artist) +
                        " <span style='color:#555;'>(" + str(round(ms/3600000, 1)) + "h)</span>"
                        "</div>"
                    )
                st.markdown(
                    "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
                    "border-radius:10px;padding:14px;'>"
                    "<div style='font-weight:800;color:#fff;margin-bottom:4px;'>"
                    + era_name + "</div>"
                    "<div style='color:#888;font-size:.78em;margin-bottom:8px;'>" + desc + "</div>"
                    "<div style='color:#555;font-size:.72em;margin-bottom:6px;'>"
                    + str(round(hrs)) + "h total</div>"
                    + items + "</div>",
                    unsafe_allow_html=True
                )

    # ── Note ──────────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
        "border-radius:10px;padding:14px;'>"
        "<div style='color:#888;font-size:.78em;line-height:1.7;'>"
        "<b style='color:#aaa;'>Note:</b> Some tracks played by your child "
        "(Bollywood, world music) may not be automatically detected as children's content "
        "because they don't match typical kids keywords. "
        "Use the <b style='color:#ccc;'>Include children's content</b> toggle in the sidebar "
        "to see the full unfiltered picture."
        "</div></div>",
        unsafe_allow_html=True
    )

    # ── Narrative ─────────────────────────────────────────────────────────────
    st.markdown("---")

    first_track = str(first_kids['trackName'])
    first_month = first_kids['ts'].strftime('%B %Y')

    st.markdown(
        "<div class='insight'>"
        "📅 <b>First time you played it: " + first_month + "</b>"
        " — <i>" + first_track + "</i>. "
        "That is when the data changed."
        "</div>"
        "<div class='insight'>"
        "📈 Peak was <b>" + str(peak_month['ym']) + "</b> — "
        "<b>" + str(int(peak_month['pct'])) + "%</b> of your total listening that month."
        "</div>"
        "<div class='insight'>"
        "🎵 <b>" + str(round(total_kids_h)) + "h</b> of your Spotify account belonged to them. "
        "Spotify captured a life event your feed never announced."
        "</div>",
        unsafe_allow_html=True
    )

    if not above_10.empty:
        share_txt = (
            "Between " + str(above_10['ym'].iloc[0]) + " and " + str(above_10['ym'].iloc[-1]) +
            ", " + str(overall_pct) +
            "% of my Spotify was for my child. "
            "Spotify knew I became a parent before I posted it anywhere. 👶🎵"
        )
        st.markdown("---")
        st.markdown("**📤 Shareable stat:**")
        st.code(share_txt)
