import streamlit as st

VIOLET = "#7C3AED"
VIOLET_LIGHT = "#A78BFA"

def render(dfm=None):
    st.title("Discovery")
    st.markdown("*Artists you should know — matched to your DNA.*")

    try:
        from spotify_auth import is_authenticated, api_get
        from spotify_api import get_top_artists, get_recommendations, create_playlist
        authenticated = is_authenticated()
    except Exception:
        authenticated = False

    if not authenticated:
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
        tr_map = {"Last 6 months": "medium_term", "Last 4 weeks": "short_term", "All time": "long_term"}

        with st.spinner("Finding artists matched to your taste..."):
            top = get_top_artists(tr_map[time_range], 5)
            if not top:
                st.error("Could not load your top artists.")
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
                            'name': name, 'id': artist.get('id'),
                            'tracks': [], 'popularity': track.get('popularity', 0),
                            'spotify_url': track.get('external_urls', {}).get('spotify', ''),
                        }
                    new_artists[name]['tracks'].append(track.get('name', ''))

        if not new_artists:
            st.success("You already know all the recommended artists. Impressive.")
            return

        st.markdown("**" + str(len(new_artists)) + " artists matched to your taste that you have never played:**")
        st.markdown("---")

        cols = st.columns(2)
        for i, (name, info) in enumerate(sorted(new_artists.items(), key=lambda x: -x[1]['popularity'])):
            with cols[i % 2]:
                pop = info['popularity']
                pop_label = "Underground" if pop < 30 else "Emerging" if pop < 55 else "Known"
                pop_color = "#1DB954" if pop < 30 else "#f59e0b" if pop < 55 else "#888"
                tracks_preview = ", ".join(info['tracks'][:2])
                spotify_link = ""
                if info['spotify_url']:
                    spotify_link = "<a href='" + info['spotify_url'] + "' target='_blank' style='color:" + VIOLET_LIGHT + ";font-size:.78em;'>Open in Spotify</a>"
                st.markdown(
                    "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
                    "border-left:3px solid " + VIOLET + ";border-radius:8px;padding:14px;margin-bottom:10px;'>"
                    "<div style='display:flex;justify-content:space-between;align-items:center;'>"
                    "<div style='font-weight:800;color:#fff;font-size:.95em;'>" + name + "</div>"
                    "<span style='color:" + pop_color + ";font-size:.72em;font-weight:700;"
                    "background:" + pop_color + "22;padding:2px 8px;border-radius:10px;'>" + pop_label + "</span>"
                    "</div>"
                    "<div style='color:#555;font-size:.78em;margin-top:5px;'>Via: " + tracks_preview + "</div>"
                    "<div style='margin-top:6px;'>" + spotify_link + "</div>"
                    "</div>",
                    unsafe_allow_html=True
                )

        st.markdown("---")
        if st.button("Save these artists to a Spotify playlist", type="primary"):
            user = api_get("me")
            if user:
                track_uris = [t.get('uri') for t in recs if t.get('uri')]
                url = create_playlist(user['id'], "MusicDNA Discovery", track_uris)
                if url:
                    st.success("Playlist created! [Open in Spotify](" + url + ")")
                else:
                    st.error("Could not create playlist.")

    with tab2:
        st.markdown("### Tracks That Match Your Musical DNA")
        with st.spinner("Loading track recommendations..."):
            top_tracks = api_get("me/top/tracks", {"time_range": "medium_term", "limit": 5})
            if not top_tracks:
                st.error("Could not load your top tracks.")
                return
            seed_track_ids = [t['id'] for t in top_tracks.get('items', [])]
            rec_tracks = get_recommendations(seed_tracks=seed_track_ids, limit=20)

        if not rec_tracks:
            st.info("No track recommendations found.")
            return

        known_tracks = set(dfm['trackName'].str.lower()) if dfm is not None else set()
        for track in rec_tracks:
            artists = ", ".join(a['name'] for a in track.get('artists', []))
            url     = track.get('external_urls', {}).get('spotify', '')
            known   = track['name'].lower() in known_tracks
            label   = "already in your history" if known else "new to you"
            color   = "#555" if known else VIOLET_LIGHT
            st.markdown(
                "<div style='display:flex;justify-content:space-between;align-items:center;"
                "padding:9px 12px;border-bottom:1px solid #1a1a1a;'>"
                "<div><span style='color:#fff;font-weight:600;'>" + track['name'] + "</span>"
                "<span style='color:#555;font-size:.82em;'> -- " + artists + "</span></div>"
                "<div style='display:flex;gap:12px;align-items:center;'>"
                "<span style='color:" + color + ";font-size:.75em;'>" + label + "</span>"
                "<a href='" + url + "' target='_blank' style='color:" + VIOLET_LIGHT + ";font-size:.78em;'>Play</a>"
                "</div></div>",
                unsafe_allow_html=True
            )
