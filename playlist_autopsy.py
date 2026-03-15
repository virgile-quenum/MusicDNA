import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

VIOLET = "#7C3AED"
VIOLET_LIGHT = "#A78BFA"

def render(dfm, playlists):
    st.title("📋 Playlist Autopsy")
    st.markdown("*Which playlists you actually use vs. which are archives.*")

    if not playlists:
        st.warning("No playlist data — upload your standard export zip alongside the Extended History.")
        return

    played_tracks = set(dfm['trackName'].str.lower().str.strip())

    pl_stats = []
    for pl in playlists:
        items = pl.get('items', [])
        if len(items) < 5:
            continue
        pl_tracks = set()
        pl_artists = set()
        for item in items:
            t = item.get('track', {})
            if t.get('trackName'):
                pl_tracks.add(t['trackName'].lower().strip())
            if t.get('artistName'):
                pl_artists.add(t['artistName'])
        if not pl_tracks:
            continue
        played_in  = pl_tracks & played_tracks
        activation = round(len(played_in) / len(pl_tracks) * 100, 1)
        diversity  = round(len(pl_artists) / len(items) * 100, 1) if items else 0
        pl_stats.append({
            'name':           pl['name'],
            'total':          len(items),
            'activation':     activation,
            'unique_artists': len(pl_artists),
            'diversity':      diversity,
        })

    if not pl_stats:
        st.warning("No playlists with enough tracks found.")
        return

    pl_df = pd.DataFrame(pl_stats).sort_values('activation', ascending=False)

    alive = len(pl_df[pl_df['activation'] > 20])
    dead  = len(pl_df[pl_df['activation'] < 5])

    c1, c2, c3 = st.columns(3)
    for col, val, lbl in [
        (c1, f"{len(pl_df)}", "Playlists analysed"),
        (c2, f"{alive}",      "Active (>20% played)"),
        (c3, f"{dead}",       "Archives (<5% played)"),
    ]:
        with col:
            st.markdown(f"<div class='metric-card'><div class='metric-val'>{val}</div>"
                        f"<div class='metric-lbl'>{lbl}</div></div>",
                        unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Activation Map", "Most Active", "Archives"])

    with tab1:
        fig = px.scatter(
            pl_df, x='diversity', y='activation', size='total',
            text='name', color='activation',
            color_continuous_scale=['#e74c3c', '#f39c12', VIOLET],
            labels={'diversity': 'Artist Diversity %',
                    'activation': 'Activation %', 'total': 'Tracks'},
            hover_data=['total', 'unique_artists']
        )
        fig.update_traces(textposition='top center', textfont_size=9)
        fig.update_layout(
            plot_bgcolor='#111', paper_bgcolor='#111', font_color='#888',
            xaxis=dict(gridcolor='#1a1a1a'),
            yaxis=dict(gridcolor='#1a1a1a'),
            height=600, margin=dict(l=0, r=0, t=20, b=0)
        )
        fig.add_hline(y=20, line_dash='dot', line_color='#f59e0b',
                      annotation_text='20% threshold')
        fig.add_vline(x=50, line_dash='dot', line_color='#555')
        st.plotly_chart(fig, use_container_width=True)
        st.caption("Top-right = diverse & active. Bottom-left = focused archive. Size = number of tracks.")

    with tab2:
        top15 = pl_df.sort_values('activation', ascending=False).head(15)
        fig2 = go.Figure(go.Bar(
            x=top15['activation'],
            y=top15['name'],
            orientation='h',
            marker_color=VIOLET,
            text=[f"{a}%" for a in top15['activation']],
            textposition='outside',
        ))
        fig2.update_layout(
            plot_bgcolor='#111', paper_bgcolor='#111', font_color='#aaa',
            yaxis=dict(autorange='reversed', gridcolor='#1a1a1a',
                       tickfont=dict(size=12, color='#ccc')),
            xaxis=dict(gridcolor='#1a1a1a', title='Activation %', range=[0, 115]),
            margin=dict(l=220, r=60, t=10, b=20),
            height=480
        )
        st.plotly_chart(fig2, use_container_width=True)

    with tab3:
        dead_pl = pl_df[pl_df['activation'] < 5].sort_values('total', ascending=False)
        st.markdown(f"### {len(dead_pl)} playlists built — never revisited")
        if dead_pl.empty:
            st.success("None! You actually use all your playlists. Rare.")
        else:
            st.dataframe(
                dead_pl[['name', 'total', 'activation', 'unique_artists']].rename(columns={
                    'name': 'Playlist', 'total': 'Tracks',
                    'activation': 'Played %', 'unique_artists': 'Artists'
                }).reset_index(drop=True),
                use_container_width=True
            )
