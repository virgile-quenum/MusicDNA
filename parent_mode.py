import streamlit as st
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime
from collections import Counter
from filters import detect_child_cultures, is_kids_content

def render(dfm, dfd, all_records):
    st.title("👶 Parent Mode")
    st.markdown("*How parenthood rewrote your Spotify account.*")

    if dfd is None or dfd.empty:
        st.info("No children's content detected in your data.")
        return

    # ── Parent Score ──────────────────────────────────────────────────────────
    all_df = pd.concat([dfm, dfd])
    monthly_total = all_df.groupby('ym')['ms'].sum()
    monthly_kids  = dfd.groupby('ym')['ms'].sum()
    parent_score  = (monthly_kids / monthly_total * 100).fillna(0).round(1).reset_index()
    parent_score.columns = ['ym', 'pct']

    st.markdown(
        "<div style='color:#A78BFA;font-size:.75em;font-weight:700;"
        "text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px;'>"
        "Parent Score — % of listening that was children's content</div>",
        unsafe_allow_html=True
    )

    fig = go.Figure()
    fig.add_scatter(x=parent_score['ym'], y=parent_score['pct'],
                    fill='tozeroy', line_color='#e74c3c',
                    fillcolor='rgba(231,76,60,0.15)', name="Children's %")
    fig.add_hline(y=10, line_dash='dot', line_color='#f39c12',
                  annotation_text='10% threshold', annotation_position='top left')
    fig.update_layout(
        plot_bgcolor='#111', paper_bgcolor='#111', font_color='#888',
        xaxis=dict(gridcolor='#222', tickangle=45),
        yaxis=dict(gridcolor='#222', title='% of monthly listening'),
        margin=dict(l=0, r=0, t=20, b=0), height=350
    )
    st.plotly_chart(fig, use_container_width=True)

    # ── Key moments ───────────────────────────────────────────────────────────
    peak_month   = parent_score.loc[parent_score['pct'].idxmax()]
    first_kids   = dfd.sort_values('ts').iloc[0]
    above_10     = parent_score[parent_score['pct'] > 10]
    total_kids_h = dfd['ms'].sum() / 3600000
    total_all_h  = all_df['ms'].sum() / 3600000

    c1, c2, c3, c4 = st.columns(4)
    for col, val, lbl in [
        (c1, first_kids['ts'].strftime('%b %Y'),          "First children's content"),
        (c2, str(int(peak_month['pct'])) + "%",            "Peak month (" + str(peak_month['ym']) + ")"),
        (c3, str(len(above_10)),                           "Months >10% children"),
        (c4, str(int(total_kids_h / total_all_h * 100)) + "%", "Overall children's share"),
    ]:
        with col:
            st.markdown(
                "<div class='metric-card'><div class='metric-val'>" + val + "</div>"
                "<div class='metric-lbl'>" + lbl + "</div></div>",
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

    first_date = first_kids['ts']
    now        = pd.Timestamp(datetime.now())
    age_years  = (now - first_date).days / 365.25
    age_est    = int(age_years)
    age_range  = str(age_est) + "–" + str(age_est + 1) + " years old"

    cultures = detect_child_cultures(dfd)
    dominant_culture  = list(cultures.keys())[0]   if cultures else "Unknown"
    secondary_culture = list(cultures.keys())[1]   if len(cultures) > 1 else None

    # language inference
    lang_map = {
        "French":                "French",
        "Brazilian / Portuguese":"Portuguese",
        "Indian / Bollywood":    "Hindi",
        "English":               "English",
        "African / Afrobeats":   "French / local",
    }
    dominant_lang  = lang_map.get(dominant_culture, "Unknown")
    secondary_lang = lang_map.get(secondary_culture, None) if secondary_culture else None

    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown(
            "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
            "border-radius:10px;padding:16px;'>"
            "<div style='color:#555;font-size:.72em;text-transform:uppercase;"
            "letter-spacing:.06em;margin-bottom:6px;'>Estimated age</div>"
            "<div style='font-size:1.4em;font-weight:900;color:#A78BFA;'>"
            + age_range + "</div>"
            "<div style='color:#444;font-size:.72em;margin-top:4px;'>"
            "Based on first children's content detected</div>"
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
            "<div style='color:#555;font-size:.72em;text-transform:uppercase;"
            "letter-spacing:.06em;margin-bottom:6px;'>Primary language(s)</div>"
            "<div style='font-size:1.4em;font-weight:900;color:#A78BFA;'>"
            + lang_str + "</div>"
            "<div style='color:#444;font-size:.72em;margin-top:4px;'>"
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
            "<div style='color:#555;font-size:.72em;text-transform:uppercase;"
            "letter-spacing:.06em;margin-bottom:6px;'>Cultural influences</div>"
            "<div style='font-size:1.4em;font-weight:900;color:#A78BFA;'>"
            + culture_str + "</div>"
            "<div style='color:#444;font-size:.72em;margin-top:4px;'>"
            + ("Strong secondary culture detected" if secondary_culture else "Single dominant culture") +
            "</div>"
            "</div>",
            unsafe_allow_html=True
        )

    if cultures:
        st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
        culture_items = ""
        for cult, hrs in list(cultures.items())[:5]:
            culture_items += (
                "<div style='display:flex;justify-content:space-between;"
                "padding:6px 0;border-bottom:1px solid #1a1a1a;'>"
                "<span style='color:#888;font-size:.85em;'>" + cult + "</span>"
                "<span style='color:#A78BFA;font-size:.85em;font-weight:700;'>"
                + str(hrs) + "h</span>"
                "</div>"
            )
        st.markdown(
            "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
            "border-radius:10px;padding:16px;'>"
            "<div style='color:#555;font-size:.72em;text-transform:uppercase;"
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
        ('🍼 Lullaby Era',     2020, 2021, "Newborn / infant — music on loop at 3am"),
        ('🧒 Childhood Era',   2022, 2023, "Growing up — nursery rhymes, stories"),
        ('🎵 Their Own Taste', 2024, 2026, "They have opinions now"),
    ]
    cols = st.columns(3)
    for col, (era_name, y1, y2, desc) in zip(cols, eras):
        era_df = dfd[(dfd['year'] >= y1) & (dfd['year'] <= y2)]
        with col:
            st.markdown(
                "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
                "border-radius:10px;padding:14px;'>"
                "<div style='font-weight:800;color:#fff;margin-bottom:4px;'>"
                + era_name + "</div>"
                "<div style='color:#555;font-size:.78em;margin-bottom:8px;'>" + desc + "</div>",
                unsafe_allow_html=True
            )
            if era_df.empty:
                st.markdown(
                    "<div style='color:#333;font-size:.78em;'>No data for this period.</div>"
                    "</div>",
                    unsafe_allow_html=True
                )
            else:
                top  = era_df.groupby('artistName')['ms'].sum().sort_values(ascending=False).head(5)
                hrs  = era_df['ms'].sum() / 3600000
                items = ""
                for artist, ms in top.items():
                    items += (
                        "<div style='color:#888;font-size:.78em;padding:3px 0;'>"
                        "· " + str(artist) +
                        " <span style='color:#555;'>(" + str(round(ms/3600000, 1)) + "h)</span>"
                        "</div>"
                    )
                st.markdown(
                    "<div style='color:#555;font-size:.72em;margin-bottom:6px;'>"
                    + str(round(hrs)) + "h total</div>"
                    + items + "</div>",
                    unsafe_allow_html=True
                )

    # ── Manual exclusion hint ─────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
        "border-radius:10px;padding:14px;'>"
        "<div style='color:#555;font-size:.78em;line-height:1.7;'>"
        "<b style='color:#888;'>Note:</b> Some adult tracks played by your child "
        "(Bollywood, world music) may not be automatically detected as children's content "
        "because they don't match typical kids keywords. "
        "Use the <b style='color:#ccc;'>Include children's content</b> toggle in the sidebar "
        "to see the full unfiltered picture."
        "</div>"
        "</div>",
        unsafe_allow_html=True
    )

    # ── Narrative ─────────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(
        "<div class='insight'>📅 <b>First children's content detected: "
        + first_kids['ts'].strftime('%B %Y') + "</b>"
        " — Track: <i>" + str(first_kids['trackName']) + "</i></div>"
        "<div class='insight'>📈 Peak was <b>" + str(peak_month['ym']) + "</b> at <b>"
        + str(int(peak_month['pct'])) + "%</b> of your total listening.</div>"
        "<div class='insight'>🎵 Spotify captured a life event your feed didn't announce. "
        "<b>" + str(round(total_kids_h)) + "h</b> of your account was theirs.</div>",
        unsafe_allow_html=True
    )

    if not above_10.empty:
        share_txt = (
            "Between " + str(above_10['ym'].iloc[0]) + " and " + str(above_10['ym'].iloc[-1]) +
            ", " + str(int(total_kids_h / total_all_h * 100)) +
            "% of my Spotify was for my child. "
            "Spotify knew I became a parent before I posted it anywhere. 👶🎵"
        )
        st.markdown("---")
        st.markdown("**📤 Shareable stat:**")
        st.code(share_txt)
