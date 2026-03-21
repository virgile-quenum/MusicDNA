import streamlit as st
import pandas as pd

VIOLET = "#7C3AED"
VIOLET_LIGHT = "#A78BFA"

def render(dfm=None):
    st.title("Discovery")
    st.markdown("*Artists you should know — matched to your DNA.*")

    try:
        from spotify_auth import is_authenticated, api_get
        authenticated = is_authenticated()
    except Exception:
        authenticated = False

    tab1, tab2 = st.tabs(["Related Artists", "Hidden Gems from Your History"])

    with tab1:
        st.markdown("### Artists Similar to Your Top Artists")
        st.caption("Based on Spotify's artist graph — not the deprecated recommendations endpoint.")

        if not authenticated:
            st.warning("Connect Spotify to enable this feature.")
        else:
            time_range = st.selectbox("Based on your top artists from",
                                      ["Last 6 months", "Last 4 weeks", "All time"],
                                      key="tr_related")
            tr_map = {"Last 6 months": "medium_term",
                      "Last 4 weeks":  "short_term",
                      "All time":      "long_term"}

            with st.spinner("Loading related artists..."):
                top_data = api_get("me/top/artists",
                                   {"time_range": tr_map[time_range], "limit": 10})
                top_artists = top_data.get('items', []) if top_data else []

            if not top_artists:
                st.error("Could not load your top artists.")
            else:
                known_ids = set(a['id'] for a in top_artists)
                known_names = set(dfm['artistName'].str.lower()) if dfm is not None else set()
                related = {}

                for artist in top_artists[:5]:
                    data = api_get("artists/" + artist['id'] + "/related-artists")
                    if not data:
                        continue
                    for r in data.get('artists', [])[:4]:
                        if r['id'] not in known_ids and r['name'].lower() not in known_names:
                            if r['id'] not in related:
                                related[r['id']] = {
                                    'name':       r['name'],
                                    'popularity': r.get('popularity', 0),
                                    'genres':     r.get('genres', [])[:2],
                                    'url':        r.get('external_urls', {}).get('spotify', ''),
                                    'via':        artist['name'],
                                }

                if not related:
                    st.info("No new related artists found. You might already know them all.")
                else:
                    st.markdown("**" + str(len(related)) + " artists you should know:**")
                    st.markdown("---")
                    cols = st.columns(2)
                    for i, (rid, info) in enumerate(
                        sorted(related.items(), key=lambda x: -x[1]['popularity'])
                    ):
                        with cols[i % 2]:
                            pop = info['popularity']
                            pop_label = "Underground" if pop < 30 else "Emerging" if pop < 55 else "Known"
                            pop_color = "#1DB954" if pop < 30 else "#f59e0b" if pop < 55 else "#888"
                            genres = " · ".join(info['genres']) if info['genres'] else ""
                            link = ""
                            if info['url']:
                                link = "<a href='" + info['url'] + "' target='_blank' style='color:" + VIOLET_LIGHT + ";font-size:.78em;'>Open in Spotify</a>"
                            st.markdown(
                                "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
                                "border-left:3px solid " + VIOLET + ";border-radius:8px;"
                                "padding:14px;margin-bottom:10px;'>"
                                "<div style='display:flex;justify-content:space-between;align-items:center;'>"
                                "<div style='font-weight:800;color:#fff;font-size:.95em;'>" + info['name'] + "</div>"
                                "<span style='color:" + pop_color + ";font-size:.72em;font-weight:700;"
                                "background:" + pop_color + "22;padding:2px 8px;border-radius:10px;'>" + pop_label + "</span>"
                                "</div>"
                                "<div style='color:#555;font-size:.78em;margin-top:4px;'>Because you listen to: <b style='color:#888;'>" + info['via'] + "</b></div>"
                                + ("<div style='color:#444;font-size:.75em;margin-top:2px;'>" + genres + "</div>" if genres else "") +
                                "<div style='margin-top:6px;'>" + link + "</div>"
                                "</div>",
                                unsafe_allow_html=True
                            )

    with tab2:
        st.markdown("### Hidden Gems — Artists You Liked But Never Really Listened To")
        st.caption("From your own listening history — no Spotify API needed.")

        if dfm is None or dfm.empty:
            st.warning("Upload your Extended History zip to enable this analysis.")
        else:
            col1, col2 = st.columns(2)
            with col1:
                min_plays = st.slider("Minimum plays to count as 'known'", 1, 20, 3,
                                       key="gem_min")
            with col2:
                top_n = st.slider("Number of gems to show", 10, 50, 20,
                                   key="gem_top")

            artist_plays = dfm.groupby('artistName').agg(
                plays=('trackName', 'count'),
                hours=('ms', lambda x: x.sum() / 3600000),
                tracks=('trackName', 'nunique'),
                last_played=('ts', 'max')
            ).reset_index()

            gems = artist_plays[
                (artist_plays['plays'] >= 1) &
                (artist_plays['plays'] < min_plays)
            ].sort_values('plays', ascending=False).head(top_n)

            if gems.empty:
                st.info("No hidden gems found with current filters.")
            else:
                st.markdown("**" + str(len(gems)) + " artists you discovered but never committed to:**")
                st.markdown("---")
                cols = st.columns(2)
                for i, (_, row) in enumerate(gems.iterrows()):
                    with cols[i % 2]:
                        last = row['last_played'].strftime('%b %Y') if pd.notna(row['last_played']) else ""
                        st.markdown(
                            "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
                            "border-left:3px solid #f59e0b;border-radius:8px;"
                            "padding:12px;margin-bottom:8px;'>"
                            "<div style='font-weight:700;color:#fff;font-size:.9em;margin-bottom:4px;'>" + str(row['artistName']) + "</div>"
                            "<div style='color:#555;font-size:.78em;line-height:1.7;'>"
                            + str(int(row['plays'])) + " play" + ("s" if row['plays'] > 1 else "") +
                            " · " + str(int(row['tracks'])) + " track" + ("s" if row['tracks'] > 1 else "") +
                            (" · Last: " + last if last else "") +
                            "</div>"
                            "</div>",
                            unsafe_allow_html=True
                        )

            st.markdown("---")
            st.markdown("### Artists You Skipped Most")
            st.caption("High skip rate = potential hidden gem you gave up on too fast.")

            if 'skipped' in dfm.columns:
                skip_stats = dfm.groupby('artistName').agg(
                    plays=('trackName', 'count'),
                    skips=('skipped', 'sum')
                ).reset_index()
                skip_stats = skip_stats[skip_stats['plays'] >= 3]
                skip_stats['skip_rate'] = skip_stats['skips'] / skip_stats['plays']
                skip_stats = skip_stats[
                    (skip_stats['skip_rate'] > 0.5) &
                    (skip_stats['plays'] < 20)
                ].sort_values('skip_rate', ascending=False).head(15)

                if not skip_stats.empty:
                    cols = st.columns(2)
                    for i, (_, row) in enumerate(skip_stats.iterrows()):
                        with cols[i % 2]:
                            pct = int(row['skip_rate'] * 100)
                            st.markdown(
                                "<div style='background:#0f0505;border:1px solid #dc262633;"
                                "border-radius:8px;padding:12px;margin-bottom:8px;'>"
                                "<div style='font-weight:700;color:#fff;font-size:.9em;'>" + str(row['artistName']) + "</div>"
                                "<div style='color:#888;font-size:.78em;margin-top:4px;'>"
                                + str(pct) + "% skip rate · " + str(int(row['plays'])) + " plays"
                                "</div>"
                                "</div>",
                                unsafe_allow_html=True
                            )
                else:
                    st.info("No high-skip artists found.")
