import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px

def render(dfm, dfd, kids_on):
    st.title("🏠 Overview")
    my_h   = dfm['ms'].sum()/3600000
    my_art = dfm['artistName'].nunique()
    my_trk = dfm['trackName'].nunique()
    my_sk  = dfm['skipped'].mean()*100
    dau_h  = dfd['ms'].sum()/3600000 if not dfd.empty else 0
    yr_min = int(dfm['year'].min()) if not dfm.empty else 2013
    yr_max = int(dfm['year'].max()) if not dfm.empty else 2026

    c1,c2,c3,c4,c5 = st.columns(5)
    for col, val, lbl in [
        (c1, f"{my_h:,.0f}h",  f"Your hours ({yr_min}–{yr_max})"),
        (c2, f"{my_art:,}",    "Unique artists"),
        (c3, f"{my_trk:,}",    "Unique tracks"),
        (c4, f"{my_sk:.1f}%",  "Skip rate"),
        (c5, f"{dau_h:.0f}h",  "Daughters content"),
    ]:
        with col:
            st.markdown(f"<div class='metric-card'><div class='metric-val'>{val}</div><div class='metric-lbl'>{lbl}</div></div>", unsafe_allow_html=True)

    st.markdown("---")
    col1, col2 = st.columns(2)

    with col1:
        st.markdown("## Listening by Year")
        yearly = dfm.groupby('year')['ms'].sum().reset_index()
        yearly['hours'] = yearly['ms']/3600000
        if kids_on and not dfd.empty:
            yk = dfd.groupby('year')['ms'].sum().reset_index()
            yk['hours'] = yk['ms']/3600000
            fig = go.Figure()
            fig.add_bar(x=yearly['year'], y=yearly['hours'], name='Your music', marker_color='#7C3AED')
            fig.add_bar(x=yk['year'], y=yk['hours'], name='Daughters', marker_color='#e74c3c')
            fig.update_layout(barmode='stack')
        else:
            fig = px.bar(yearly, x='year', y='hours', color_discrete_sequence=['#7C3AED'])
        fig.update_layout(plot_bgcolor='#111', paper_bgcolor='#111', font_color='#888',
                          showlegend=kids_on, xaxis=dict(gridcolor='#222'),
                          yaxis=dict(gridcolor='#222'), margin=dict(l=0,r=0,t=10,b=0))
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.markdown("## Artist Discovery by Year")
        df_sorted = dfm.sort_values('ts')
        first_year = df_sorted.groupby('artistName')['year'].min()
        npm = first_year.groupby(first_year).size()
        npm = npm.reset_index(name='new_artists')
        npm.columns = ['year','new_artists']
        fig2 = px.bar(npm, x='year', y='new_artists', color_discrete_sequence=['#A78BFA'])
        fig2.update_layout(plot_bgcolor='#111', paper_bgcolor='#111', font_color='#888',
                           xaxis=dict(gridcolor='#222'), yaxis=dict(gridcolor='#222'),
                           margin=dict(l=0,r=0,t=10,b=0))
        st.plotly_chart(fig2, use_container_width=True)

    st.markdown("## Your Musical Eras")
    era_data = []
    for yr, grp in dfm.groupby('year'):
        top_a = grp.groupby('artistName')['ms'].sum().idxmax()
        era_data.append({'Year': yr, 'Top Artist': top_a,
                         'Hours': round(grp['ms'].sum()/3600000,0),
                         'Artists': grp['artistName'].nunique(),
                         'Skip %': f"{grp['skipped'].mean()*100:.0f}%"})
    st.dataframe(pd.DataFrame(era_data).set_index('Year'), use_container_width=True)

    st.markdown(f"""
    <div class='insight'>🎧 <b>{my_h:,.0f}h</b> across {yr_max-yr_min+1} years — roughly <b>{my_h/(yr_max-yr_min+1)/365*60:.0f} min/day</b> on average.</div>
    <div class='insight'>🌍 <b>{my_art:,} unique artists</b> and <b>{my_trk:,} unique tracks</b>.</div>
    <div class='insight'>⏭️ <b>{my_sk:.1f}% skip rate</b> — committed listener. Industry average ~25%.</div>
    """, unsafe_allow_html=True)
    if dau_h > 0:
        pct = dau_h/(my_h+dau_h)*100
        st.markdown(f"<div class='insight'>👶 <b>{dau_h:.0f}h ({pct:.0f}%)</b> was daughters content.</div>", unsafe_allow_html=True)
