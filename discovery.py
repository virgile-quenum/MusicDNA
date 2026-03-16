import streamlit as st
import pandas as pd
from spotify_auth import is_authenticated, api_get
from spotify_api import get_top_artists, get_recommendations, create_playlist

VIOLET = "#7C3AED"
VIOLET_LIGHT = "#A78BFA"

def render(dfm=None):
    st.title("Discovery")
    st.markdown("*Artists you should know — matched to your DNA. Not what Spotify wants to sell you.*")

    if not is_authenticated():
        st.warning("Connect your Spotify account to get personalized recommendations.")
        st.info("Click 'Connect Spotify' in the sidebar to enable this feature.")
        return

    tab1, tab2 = st.tabs(["Artists You Should Know", "Tracks Matching Your DNA"])

    with tab1:
        st.markdown("### Artists You Have Never Played — But Should")

        col1, col2, col3 = st.columns(3)
        with col1:
            underground = st.checkbox("Underground only (popularity below 50)", value=False)
        with col2:
            limit = st.slider("Number of suggestions", 10, 50, 20)
        with col3:
            time_range = st.selectbox("Based on your taste from",
                                      ["Last 6 months", "Last 4 weeks", "All time"], index=0)

        tr_map = {"Last 6 months": "medium_term",
                  "Last 4 weeks":  "short_term",
                  "All time":      "long_term"}

        with st.spinner("Finding artists matched to your taste..."):
            top = get_top_artists(tr_map[time_range], 5)
            if not top:
                st.error("Could not load your top artists. Make sure Spotify is connected.")
                return
            seed_ids = [a['id'] for a in top]
            max_pop  = 50 if underground else 100
            recs = get_recommendations(seed_artists=seed_ids, limit=limit, max_popularity=max_pop)

        if not recs:
            st.info("No recommendations found. Try changing the filters.")
            return

        known_artists = set(dfm['artistName'].str.lower()) if dfm is not None else set()

        new_artists = {}
        for track in recs:
            for artist in track.get('artists', []):
                name = artist.get('name', '')
                if name.lower() not in known_artists:
                    if name not in new_artists:
                        new_artists[name] = {
                            'name':        name,
                            'id':          artist.get('id'),
                            'tracks':      [],
                            'popularity':  track.get('popularity', 0),
                            'spotify_url': track.get('external_urls', {}).get('spotify', ''),
                        }
                    new_artists[name]['tracks'].append(track.get('name', ''))

        if not new_artists:
            st.success("You already know all the recommended artists. Impressive.")
            return

        st.markdown(f"**{len(new_artists)} artists matched to your taste that you have never played:**")
        st.markdown("---")

        cols = st.columns(2)
        for i, (name, info) in enumerate(
            sorted(new_artists.items(), key=lambda x: -x[1]['popularity'])
        ):
            with cols[i % 2]:
                pop = info['popularity']
                pop_label = "Underground" if pop < 30 else "Emerging" if pop < 55 else "Known"
                pop_color = "#1DB954" if pop < 30 else "#f59e0b" if pop < 55 else "#888"
                tracks_preview = ", ".join(info['tracks'][:2])
                spotify_link = ""
                if info['spotify_url']:
                    spotify_link = f"<a href='{info['s
