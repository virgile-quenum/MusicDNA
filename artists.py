import streamlit as st
import pandas as pd
import plotly.graph_objects as go

VIOLET = "#7C3AED"
VIOLET_LIGHT = "#A78BFA"

def render(df):
    st.title("🎤 Artists & Tracks")
    tab1, tab2, tab3 = st.tabs(["Top Artists", "Top Tracks", "Your Eras"])

    with tab1:
        n = st.slider("Number of artists", 10, 50, 20, key="art_n")
        artist_stats = df.groupby('artistName').agg(
            hours=('ms', lambda x: round(x.sum()/3600000,2)),
            plays=('ms','count'),
        ).sort_values('hours', ascending=False).head(n).reset_index()

        fig = go.Figure(go.Bar(
            x=artist_stats['hours'],
            y=artist_stats['artistName'],
            orientation='h',
            marker_color=VIOLET,
            text=[f"{h:.1f}h" for h in artist_stats['hours']],
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>%{x:.1f}h<extra></extra>'
        ))
        fig.update_layout(
            plot_bgcolor='#111', paper_bgcolor='#111', font_color='#aaa',
            yaxis=dict(autorange='reversed', gridcolor='#1a1a1a',
                       tickfont=dict(size=12, color='#ccc')),
            xaxis=dict(gridcolor='#1a1a1a', title='Hours'),
            margin=dict(l=180, r=80, t=10, b=20),
            height=max(400, n*26)
        )
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        n2 = st.slider("Number of tracks", 10, 50, 20, key="trk_n")
        track_stats = df.groupby(['trackName','artistName']).agg(
            plays=('ms','count'),
            hours=('ms', lambda x: round(x.sum()/3600000,2)),
            skip_rate=('skipped', lambda x: round(x.mean()*100,1))
        ).sort_values('plays', ascending=False).head(n2).reset_index()
        track_stats['label'] = (track_stats['trackName'].str[:38]
                                + ' — ' + track_stats['artistName'].str[:18])

        fig2 = go.Figure(go.Bar(
            x=track_stats['plays'],
            y=track_stats['label'],
            orientation='h',
            marker_color=VIOLET_LIGHT,
            text=[f"{p}x" for p in track_stats['plays']],
            textposition='outside',
            hovertemplate='<b>%{y}</b><br>%{x} plays<extra></extra>'
        ))
        fig2.update_layout(
            plot_bgcolor='#111', paper_bgcolor='#111', font_color='#aaa',
            yaxis=dict(autorange='reversed', gridcolor='#1a1a1a',
                       tickfont=dict(size=11, color='#ccc')),
            xaxis=dict(gridcolor='#1a1a1a', title='Plays'),
            margin=dict(l=300, r=80, t=10, b=20),
            height=max(400, n2*26)
        )
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        st.markdown("## Top 3 Artists Per Year")
        era_rows = []
        for yr, grp in df.groupby('year'):
            top3 = grp.groupby('artistName')['ms'].sum().sort_values(ascending=False).head(3)
            for rank, (artist, ms) in enumerate(top3.items(), 1):
                era_rows.append({'Year':yr,'Rank':rank,'Artist':artist,
                                 'Hours':round(ms/3600000,1)})
        era_df = pd.DataFrame(era_rows)

        top1 = era_df[era_df['Rank']==1]
        fig3 = go.Figure(go.Bar(
            x=top1['Year'], y=top1['Hours'],
            text=top1['Artist'], textposition='inside',
            marker_color=VIOLET,
            hovertemplate='%{text}<br>%{y:.1f}h<extra></extra>'
        ))
        fig3.update_layout(
            plot_bgcolor='#111', paper_bgcolor='#111', font_color='#aaa',
            xaxis=dict(gridcolor='#1a1a1a', dtick=1),
            yaxis=dict(gridcolor='#1a1a1a'),
            margin=dict(l=0,r=0,t=10,b=0), height=380
        )
        st.plotly_chart(fig3, use_container_width=True)

        pivot = era_df.pivot_table(
            index='Year', columns='Rank', values='Artist', aggfunc='first')
        pivot.columns = ['#1 Artist','#2 Artist','#3 Artist']
        st.dataframe(pivot, use_container_width=True)
