import streamlit as st
import pandas as pd
import plotly.graph_objects as go

VIOLET       = "#7C3AED"
VIOLET_LIGHT = "#A78BFA"

def render(dfm, lib):
    st.title("📋 Playlist Autopsy")
    st.markdown("*Which playlists you actually use — vs. which are archives you built and forgot.*")

    # handle lib as dict or list
    if isinstance(lib, dict):
        playlists = lib.get('playlists', [])
        liked     = lib.get('tracks', [])
    elif isinstance(lib, list):
        playlists = lib
        liked     = []
    else:
        playlists = []
        liked     = []

    if not playlists:
        st.warning("No playlist data — upload your standard export zip alongside the Extended History.")
        return

    rows = []
    for pl in playlists:
        name   = pl.get('name', 'Unnamed')
        items  = pl.get('items', [])
        tracks = [i.get('track', {}) for i in items if i.get('track')]
        track_names   = [t.get('trackName', '') for t in tracks if t.get('trackName')]
        artist_names  = [t.get('artistName', '') for t in tracks if t.get('artistName')]
        rows.append({
            'name':         name,
            'total_tracks': len(track_names),
            'unique_artists': len(set(artist_names)),
            'tracks':        track_names,
        })

    pl_df = pd.DataFrame(rows)

    if pl_df.empty:
        st.info("No playlist content found.")
        return

    # cross with history
    played_tracks = set(dfm['trackName'].str.lower().str.strip())

    def overlap(track_list):
        if not track_list:
            return 0
        hits = sum(1 for t in track_list if t.lower().strip() in played_tracks)
        return round(hits / len(track_list) * 100, 1)

    pl_df['play_overlap_pct'] = pl_df['tracks'].apply(overlap)
    pl_df['status'] = pl_df['play_overlap_pct'].apply(
        lambda x: 'Active' if x >= 30 else ('Occasional' if x >= 10 else 'Archive')
    )

    # summary
    c1, c2, c3, c4 = st.columns(4)
    active     = len(pl_df[pl_df['status'] == 'Active'])
    occasional = len(pl_df[pl_df['status'] == 'Occasional'])
    archive    = len(pl_df[pl_df['status'] == 'Archive'])
    total      = len(pl_df)

    for col, val, lbl in [
        (c1, str(total),      "Total playlists"),
        (c2, str(active),     "Active (30%+ overlap)"),
        (c3, str(occasional), "Occasional"),
        (c4, str(archive),    "Archives — never played"),
    ]:
        with col:
            st.markdown(
                "<div class='metric-card'><div class='metric-val'>" + val + "</div>"
                "<div class='metric-lbl'>" + lbl + "</div></div>",
                unsafe_allow_html=True
            )

    st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["All Playlists", "Archives", "Most Active"])

    with tab1:
        st.markdown("### All Playlists — by play overlap")
        st.caption("% of tracks in each playlist that appear in your listening history.")

        disp = pl_df[['name','total_tracks','unique_artists','play_overlap_pct','status']].copy()
        disp = disp.sort_values('play_overlap_pct', ascending=False)
        disp.columns = ['Playlist', 'Tracks', 'Artists', 'Play overlap %', 'Status']

        def color_status(val):
            if val == 'Active':     return 'color: #1DB954'
            if val == 'Occasional': return 'color: #f59e0b'
            return 'color: #555'

        st.dataframe(
            disp.reset_index(drop=True),
            use_container_width=True,
            height=500
        )

    with tab2:
        archives = pl_df[pl_df['status'] == 'Archive'].sort_values('total_tracks', ascending=False)
        st.markdown("### " + str(len(archives)) + " Archive Playlists")
        st.caption("You built these. You never came back.")

        if archives.empty:
            st.success("No archives — you actually use all your playlists.")
        else:
            cols = st.columns(2)
            for i, (_, row) in enumerate(archives.iterrows()):
                with cols[i % 2]:
                    st.markdown(
                        "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
                        "border-left:3px solid #333;border-radius:8px;"
                        "padding:14px;margin-bottom:10px;'>"
                        "<div style='font-weight:700;color:#666;font-size:.9em;'>"
                        + str(row['name']) + "</div>"
                        "<div style='color:#444;font-size:.76em;margin-top:4px;'>"
                        + str(int(row['total_tracks'])) + " tracks · "
                        + str(int(row['unique_artists'])) + " artists · "
                        + str(row['play_overlap_pct']) + "% played"
                        "</div>"
                        "</div>",
                        unsafe_allow_html=True
                    )

    with tab3:
        active_pl = pl_df[pl_df['status'] == 'Active'].sort_values('play_overlap_pct', ascending=False)
        st.markdown("### Your Most Used Playlists")

        if active_pl.empty:
            st.info("No playlists with 30%+ overlap found.")
        else:
            fig = go.Figure(go.Bar(
                x=active_pl['play_overlap_pct'],
                y=active_pl['name'],
                orientation='h',
                marker_color=VIOLET,
                text=[str(p) + "%" for p in active_pl['play_overlap_pct']],
                textposition='outside',
            ))
            fig.update_layout(
                plot_bgcolor='#111', paper_bgcolor='#111', font_color='#aaa',
                yaxis=dict(autorange='reversed', tickfont=dict(size=11, color='#ccc')),
                xaxis=dict(gridcolor='#1a1a1a', title='Play overlap %', range=[0, 110]),
                margin=dict(l=200, r=60, t=10, b=20),
                height=max(300, len(active_pl) * 32)
            )
            st.plotly_chart(fig, use_container_width=True)
