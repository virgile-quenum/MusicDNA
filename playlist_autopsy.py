import streamlit as st
import pandas as pd
import plotly.express as px
from collections import defaultdict

def render(dfm, playlists):
    st.title("📋 Playlist Autopsy")
    st.markdown("*Which playlists you actually use vs. which are archives.*")

    if not playlists:
        st.warning("Playlist files not found in data/")
        return

    played_tracks = set(dfm['trackName'].str.lower().str.strip())

    pl_stats = []
    for pl in playlists:
        items = pl.get('items', [])
        if len(items) < 5: continue
        pl_tracks, pl_artists = set(), set()
        for item in items:
            t = item.get('track', {})
            if t.get('trackName'):
                pl_tracks.add(t['trackName'].lower().strip())
            if t.get('artistName'):
                pl_artists.add(t['artistName'])
        played_in = pl_tracks & played_tracks
        activation = len(played_in)/len(pl_tracks)*100 if pl_tracks else 0
        diversity  = len(pl_artists)/len(items)*100 if items else 0
        pl_stats.append({
            'name': pl['name'], 'total': len(items),
            'activation': round(activation,1),
            'unique_artists': len(pl_artists),
            'diversity': round(diversity,1),
        })

    pl_df = pd.DataFrame(pl_stats).sort_values('activation', ascending=False)

    c1,c2,c3 = st.columns(3)
    alive = len(pl_df[pl_df['activation']>20])
    dead  = len(pl_df[pl_df['activation']<5])
    for col,val,lbl in [
        (c1, f"{len(pl_df)}", "Playlists analysed"),
        (c2, f"{alive}",      "Active (>20% played)"),
        (c3, f"{dead}",       "Archives (<5% played)"),
    ]:
        with col:
            st.markdown(f"<div class='metric-card'><div class='metric-val'>{val}</div>"
                        f"<div class='metric-lbl'>{lbl}</div></div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Activation Map", "Most Active", "Archives"])

    with tab1:
        fig = px.scatter(pl_df, x='diversity', y='activation', size='total',
                         text='name', color='activation',
                         color_continuous_scale=['#e74c3c','#f39c12','#7C3AED'],
                         labels={'diversity':'Artist Diversity %','activation':'Activation %','total':'Tracks'},
                         hover_data=['total','unique_artists'])
        fig.update_traces(textposition='top center', textfont_size=9)
        fig.update_layout(plot_bgcolor='#111',paper_bgcolor='#111',font_color='#888',
                          xaxis=dict(gridcolor='#222'),yaxis=dict(gridcolor='#222'),
                          height=600, margin=dict(l=0,r=0,t=20,b=0))
        fig.add_hline(y=20, line_dash='dot', line_color='#f39c12')
        fig.add_vline(x=50, line_dash='dot', line_color='#3498db')
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Top-right = diverse & active. Bottom-left = focused archive. Size = number of tracks.")

    with tab2:
        top_active = pl_df.sort_values('activation', ascending=False).head(15)
        fig2 = px.bar(top_active, x='activation', y='name', orientation='h',
                      color='activation', color_continuous_scale=['#0a3d1f','#7C3AED'])
        fig2.update_layout(plot_bgcolor='#111',paper_bgcolor='#111',font_color='#888',
                           yaxis=dict(autorange='reversed',gridcolor='#222'),
                           xaxis=dict(gridcolor='#222',title='Activation %'),
                           coloraxis_showscale=False, margin=dict(l=0,r=0,t=10,b=0), height=450)
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        dead_pl = pl_df[pl_df['activation']<5].sort_values('total', ascending=False)
        st.markdown(f"### {len(dead_pl)} playlists built — never revisited")
        st.dataframe(dead_pl[['name','total','activation','unique_artists']].rename(columns={
            'name':'Playlist','total':'Tracks','activation':'Played %','unique_artists':'Artists'
        }).reset_index(drop=True), use_container_width=True)
