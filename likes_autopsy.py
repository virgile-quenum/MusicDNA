import streamlit as st
import pandas as pd
import plotly.express as px

def render(dfm, lib):
    st.title("💔 Likes Autopsy")
    st.markdown("*What you **think** you love vs. what you actually play.*")

    liked = lib.get('tracks', [])
    if not liked:
        st.warning("YourLibrary.json not found in data/")
        return

    liked_df = pd.DataFrame(liked)
    played_tracks = set(dfm['trackName'].str.lower().str.strip())
    played_artists = dfm.groupby('artistName')['ms'].agg(['count','sum']).reset_index()
    played_artists.columns = ['artist','plays','total_ms']

    liked_by_artist = liked_df.groupby('artist').size().reset_index(name='liked_count')
    merged = liked_by_artist.merge(played_artists, on='artist', how='outer').fillna(0)
    merged['liked_count'] = merged['liked_count'].astype(int)
    merged['plays']       = merged['plays'].astype(int)
    merged['hours']       = (merged['total_ms']/3600000).round(2)

    never_played = sum(1 for t in liked if t['track'].lower().strip() not in played_tracks)
    ghost_artists= len(merged[(merged['liked_count']>0)&(merged['plays']==0)])

    c1,c2,c3,c4 = st.columns(4)
    for col,val,lbl in [
        (c1, f"{len(liked):,}",       "Total liked tracks"),
        (c2, f"{never_played:,}",     f"Never played ({never_played/len(liked)*100:.0f}%)"),
        (c3, f"{ghost_artists}",      "Artists liked, never played"),
        (c4, f"{len(liked)-never_played:,}", "Active likes"),
    ]:
        with col:
            st.markdown(f"<div class='metric-card'><div class='metric-val'>{val}</div>"
                        f"<div class='metric-lbl'>{lbl}</div></div>", unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["Most Liked Artists", "The Gap", "Ghost Artists"])

    with tab1:
        top_liked = liked_by_artist.sort_values('liked_count', ascending=False).head(20)
        fig = px.bar(top_liked, x='liked_count', y='artist', orientation='h',
                     color_discrete_sequence=['#7C3AED'])
        fig.update_layout(plot_bgcolor='#111',paper_bgcolor='#111',font_color='#888',
                          yaxis=dict(autorange='reversed',gridcolor='#222'),
                          xaxis=dict(gridcolor='#222'),margin=dict(l=0,r=0,t=10,b=0),
                          height=500)
        st.plotly_chart(fig, use_container_width=True)

    with tab2:
        st.markdown("### The Identity Gap — Liked ≠ Played")
        st.caption("Artists you liked heavily but rarely play (admired, not consumed) vs. artists you play constantly but never liked (visceral, not curated)")

        admired = merged[(merged['liked_count']>=5)&(merged['plays']<10)].sort_values('liked_count',ascending=False).head(12)
        visceral = merged[(merged['liked_count']<=1)&(merged['plays']>=30)].sort_values('plays',ascending=False).head(12)

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**🧠 You admire but don't play**")
            st.caption("Liked a lot — listened rarely")
            for _,r in admired.iterrows():
                st.markdown(f"- **{r['artist']}** — {r['liked_count']} liked, {r['plays']} plays")
        with col2:
            st.markdown("**❤️ You play but never liked**")
            st.caption("Listened constantly — never saved")
            for _,r in visceral.iterrows():
                st.markdown(f"- **{r['artist']}** — {r['plays']} plays, {r['liked_count']} liked")

        st.markdown("""<div class='insight'>🔍 <b>The gap reveals two listening modes</b>:
        intellectual curation (likes) vs. visceral consumption (plays).
        Most people's identity and reality don't match. Yours especially.</div>""",
        unsafe_allow_html=True)

    with tab3:
        ghost = merged[(merged['liked_count']>0)&(merged['plays']==0)].sort_values('liked_count',ascending=False)
        st.markdown(f"### {len(ghost)} Artists You Liked But Never Played")
        st.caption("Music you saved at some point and completely forgot.")
        st.dataframe(ghost[['artist','liked_count']].rename(
            columns={'artist':'Artist','liked_count':'Tracks Liked'}
        ).reset_index(drop=True), use_container_width=True, height=500)
