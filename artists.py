import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

def render(df):
    st.title("🎤 Artists & Tracks")
    tab1, tab2, tab3 = st.tabs(["Top Artists", "Top Tracks", "Evolution"])

    with tab1:
        n = st.slider("Number of artists", 10, 50, 20)
        artist_stats = df.groupby('artistName').agg(
            hours=('ms', lambda x: round(x.sum()/3600000,2)),
            plays=('ms','count'),
            skips=('skipped','mean')
        ).sort_values('hours', ascending=False).head(n).reset_index()

        fig = px.bar(artist_stats, x='hours', y='artistName', orientation='h',
                     color='hours', color_continuous_scale=['#0a3d1f','#7C3AED'],
                     hover_data=['plays'])
        fig.update_layout(plot_bgcolor='#111',paper_bgcolor='#111',font_color='#888',
                          yaxis=dict(autorange='reversed', gridcolor='#222'),
                          xaxis=dict(gridcolor='#222'), coloraxis_showscale=False,
                          margin=dict(l=0,r=0,t=10,b=0), height=max(400, n*22))
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        n2 = st.slider("Number of tracks", 10, 50, 20)
        track_stats = df.groupby(['trackName','artistName']).agg(
            plays=('ms','count'),
            hours=('ms', lambda x: round(x.sum()/3600000,2)),
            skip_rate=('skipped', lambda x: round(x.mean()*100,1))
        ).sort_values('plays', ascending=False).head(n2).reset_index()
        track_stats['label'] = track_stats['trackName'].str[:45] + ' — ' + track_stats['artistName'].str[:20]

        fig2 = px.bar(track_stats, x='plays', y='label', orientation='h',
                      color='plays', color_continuous_scale=['#0a1a3d','#A78BFA'],
                      hover_data=['hours','skip_rate'])
        fig2.update_layout(plot_bgcolor='#111',paper_bgcolor='#111',font_color='#888',
                           yaxis=dict(autorange='reversed',gridcolor='#222'),
                           xaxis=dict(gridcolor='#222'), coloraxis_showscale=False,
                           margin=dict(l=0,r=0,t=10,b=0), height=max(400, n2*22))
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        st.markdown("## Top Artist Per Year")
        era_rows = []
        for yr, grp in df.groupby('year'):
            top5 = grp.groupby('artistName')['ms'].sum().sort_values(ascending=False).head(5)
            for rank, (artist, ms) in enumerate(top5.items(), 1):
                era_rows.append({'Year': yr, 'Rank': rank, 'Artist': artist,
                                 'Hours': round(ms/3600000,1)})
        era_df = pd.DataFrame(era_rows)
        top1 = era_df[era_df['Rank']==1]
        fig3 = px.bar(top1, x='Year', y='Hours', text='Artist',
                      color_discrete_sequence=['#7C3AED'])
        fig3.update_traces(textposition='inside', textfont_size=11)
        fig3.update_layout(plot_bgcolor='#111',paper_bgcolor='#111',font_color='#888',
                           xaxis=dict(gridcolor='#222'), yaxis=dict(gridcolor='#222'),
                           margin=dict(l=0,r=0,t=10,b=0))
        st.plotly_chart(fig3, use_container_width=True)

        st.markdown("## Full Top 5 Per Year")
        pivot = era_df[era_df['Rank']<=3].pivot_table(
            index='Year', columns='Rank', values='Artist', aggfunc='first')
        pivot.columns = ['#1','#2','#3']
        st.dataframe(pivot, use_container_width=True)
