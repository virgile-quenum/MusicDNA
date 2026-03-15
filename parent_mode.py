import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from filters import is_daughters

def render(dfm, dfd, all_records):
    st.title("👶 Parent Mode")
    st.markdown("*How parenthood rewrote your Spotify account.*")

    if dfd.empty:
        st.info("No daughters content detected in your data.")
        return

    # ── Parent Score ──────────────────────────────────────────────────────
    all_df = pd.concat([dfm, dfd])
    monthly_total = all_df.groupby('ym')['ms'].sum()
    monthly_kids  = dfd.groupby('ym')['ms'].sum()
    parent_score  = (monthly_kids / monthly_total * 100).fillna(0).round(1).reset_index()
    parent_score.columns = ['ym','pct']

    st.markdown("## Parent Score — % of Listening That Was Daughters Content")
    fig = go.Figure()
    fig.add_scatter(x=parent_score['ym'], y=parent_score['pct'],
                    fill='tozeroy', line_color='#e74c3c',
                    fillcolor='rgba(231,76,60,0.15)', name='Kids %')
    fig.add_hline(y=10, line_dash='dot', line_color='#f39c12',
                  annotation_text='10% threshold', annotation_position='top left')
    fig.update_layout(plot_bgcolor='#111',paper_bgcolor='#111',font_color='#888',
                      xaxis=dict(gridcolor='#222',tickangle=45),
                      yaxis=dict(gridcolor='#222',title='% of monthly listening'),
                      margin=dict(l=0,r=0,t=20,b=0), height=350)
    st.plotly_chart(fig, use_container_width=True)

    # ── Key moments ──────────────────────────────────────────────────────
    peak_month = parent_score.loc[parent_score['pct'].idxmax()]
    first_kids = dfd.sort_values('ts').iloc[0]
    above_10   = parent_score[parent_score['pct'] > 10]
    total_kids_h = dfd['ms'].sum()/3600000
    total_all_h  = all_df['ms'].sum()/3600000

    c1,c2,c3,c4 = st.columns(4)
    for col,val,lbl in [
        (c1, first_kids['ts'].strftime('%b %Y'), "First kids content"),
        (c2, f"{peak_month['pct']:.0f}%",        f"Peak month ({peak_month['ym']})"),
        (c3, f"{len(above_10)}",                  "Months >10% kids"),
        (c4, f"{total_kids_h/total_all_h*100:.0f}%", "Overall kids share"),
    ]:
        with col:
            st.markdown(f"<div class='metric-card'><div class='metric-val'>{val}</div>"
                        f"<div class='metric-lbl'>{lbl}</div></div>", unsafe_allow_html=True)

    # ── Daughters musical evolution ───────────────────────────────────────
    st.markdown("---")
    st.markdown("## The Musical Evolution of Your Daughters")
    eras = [
        ('🍼 Lullaby Era', 2020, 2021, "Newborn / infant — music on loop at 3am"),
        ('🧒 Childhood Era', 2022, 2023, "Growing up — nursery rhymes, stories"),
        ('🎵 Their Own Taste', 2024, 2026, "They have opinions now"),
    ]
    cols = st.columns(3)
    for col, (era_name, y1, y2, desc) in zip(cols, eras):
        era_df = dfd[(dfd['year'] >= y1) & (dfd['year'] <= y2)]
        with col:
            st.markdown(f"**{era_name}**")
            st.caption(desc)
            if era_df.empty:
                st.caption("No data")
            else:
                top = era_df.groupby('artistName')['ms'].sum().sort_values(ascending=False).head(5)
                hrs = era_df['ms'].sum()/3600000
                st.caption(f"{hrs:.0f}h total")
                for artist, ms in top.items():
                    st.markdown(f"- {artist} *(${ms/3600000:.0f}h)*")

    # ── Narrative ────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown(f"""
    <div class='insight'>📅 <b>First kids content detected: {first_kids['ts'].strftime('%B %Y')}</b>
    — Track: <i>{first_kids['trackName']}</i></div>
    <div class='insight'>📈 Peak was <b>{peak_month['ym']}</b> at <b>{peak_month['pct']:.0f}%</b>
    of your total listening. That's the newborn phase.</div>
    <div class='insight'>🎵 Spotify captured a life event your feed didn't announce.
    <b>{total_kids_h:.0f}h</b> of your account was theirs.</div>
    """, unsafe_allow_html=True)

    share_txt = (f"Between {above_10['ym'].iloc[0]} and {above_10['ym'].iloc[-1]}, "
                 f"{total_kids_h/total_all_h*100:.0f}% of my Spotify was for my daughters. "
                 f"Spotify knew I became a parent before I posted it anywhere. 👶🎵")
    st.markdown("---")
    st.markdown("**📤 Shareable stat:**")
    st.code(share_txt)
