import streamlit as st
import pandas as pd
import plotly.graph_objects as go

VIOLET       = "#7C3AED"
VIOLET_LIGHT = "#A78BFA"


def _confidence(liked_count, plays, total_plays):
    """
    Internal confidence score — not displayed.
    High confidence = lots of data on both sides (likes + plays).
    Low confidence = only one signal available.
    """
    likes_signal = min(liked_count / 10, 1.0)
    plays_signal = min(plays / 50, 1.0) if total_plays > 0 else 0
    volume_bonus = min(total_plays / 500, 0.2)
    return round((likes_signal * 0.5 + plays_signal * 0.5 + volume_bonus), 3)


def render(dfm, lib):
    st.title("💔 Likes Autopsy")
    st.markdown("*What you **think** you love vs. what you **actually** play.*")

    # handle lib as dict or list
    if isinstance(lib, dict):
        liked = lib.get('tracks', [])
    elif isinstance(lib, list):
        liked = lib
    else:
        liked = []

    if not liked:
        st.warning("No likes data — upload your standard export zip alongside the Extended History.")
        return

    liked_df = pd.DataFrame(liked)

    # normalise column names
    if 'track' not in liked_df.columns and 'trackName' in liked_df.columns:
        liked_df = liked_df.rename(columns={'trackName': 'track', 'artistName': 'artist'})
    if 'artist' not in liked_df.columns:
        liked_df['artist'] = ''
    if 'track' not in liked_df.columns:
        liked_df['track'] = ''

    played_tracks  = set(dfm['trackName'].str.lower().str.strip())
    total_plays    = len(dfm)

    played_artists = dfm.groupby('artistName').agg(
        plays=('ms', 'count'),
        hours=('ms', lambda x: round(x.sum() / 3600000, 2))
    ).reset_index()

    PLAY_THRESHOLD = 15

    liked_by_artist = liked_df.groupby('artist').size().reset_index(name='liked_count')
    merged = liked_by_artist.merge(
        played_artists.rename(columns={'artistName': 'artist'}),
        on='artist', how='outer'
    ).fillna(0)
    merged['liked_count'] = merged['liked_count'].astype(int)
    merged['plays']       = merged['plays'].astype(int)
    merged['hours']       = merged['hours'].round(2)

    # confidence score — used for sorting only, not displayed
    merged['_confidence'] = merged.apply(
        lambda r: _confidence(r['liked_count'], r['plays'], total_plays), axis=1
    )

    def classify(row):
        if row['liked_count'] >= 3 and row['plays'] >= 20: return 'Active'
        if row['liked_count'] >= 3 and row['plays'] < 5:   return 'Admired'
        if row['liked_count'] < 2  and row['plays'] >= PLAY_THRESHOLD: return 'Visceral'
        return 'Neutral'

    merged['profile'] = merged.apply(classify, axis=1)

    never_played = sum(
        1 for t in liked
        if str(t.get('track', t.get('trackName', ''))).lower().strip() not in played_tracks
    )
    total_liked = len(liked)

    c1, c2, c3, c4 = st.columns(4)
    for col, val, lbl in [
        (c1, str(total_liked),                                  "Tracks liked"),
        (c2, str(never_played) + " (" + str(int(never_played / max(total_liked, 1) * 100)) + "%)", "Never played"),
        (c3, str(len(merged[merged['profile'] == 'Admired'])),  "Admired but not consumed"),
        (c4, str(len(merged[merged['profile'] == 'Visceral'])), "Played but never liked"),
    ]:
        with col:
            st.markdown(
                "<div class='metric-card'><div class='metric-val'>" + val + "</div>"
                "<div class='metric-lbl'>" + lbl + "</div></div>",
                unsafe_allow_html=True
            )

    tab1, tab2, tab3 = st.tabs(["The Identity Gap", "Most Liked Artists", "Ghost Artists"])

    with tab1:
        st.markdown("### The Gap — Who You Think You Are vs. Who You Are")
        st.caption(
            "Left: artists you liked heavily but barely play. "
            "Right: artists you play constantly but never saved. "
            "Sorted by data confidence — stronger signals first."
        )
        col1, col2 = st.columns(2)

        admired = (
            merged[(merged['liked_count'] >= 5) & (merged['plays'] < 10)]
            .sort_values('_confidence', ascending=False)
            .head(30)
        )
        visceral = (
            merged[(merged['liked_count'] <= 1) & (merged['plays'] >= PLAY_THRESHOLD)]
            .sort_values('_confidence', ascending=False)
            .head(30)
        )

        with col1:
            st.markdown("**You admire but do not really play**")
            st.caption("Liked a lot — listened rarely. Cultural identity, not daily taste.")
            if admired.empty:
                st.info("None detected.")
            else:
                fig = go.Figure(go.Bar(
                    x=admired['liked_count'],
                    y=admired['artist'],
                    orientation='h',
                    marker_color='#9B59B6',
                    text=[str(c) + " liked / " + str(p) + " plays"
                          for c, p in zip(admired['liked_count'], admired['plays'])],
                    textposition='outside',
                ))
                fig.update_layout(
                    plot_bgcolor='#111', paper_bgcolor='#111', font_color='#aaa',
                    yaxis=dict(autorange='reversed', tickfont=dict(size=11, color='#ccc')),
                    xaxis=dict(gridcolor='#1a1a1a', title='Tracks liked'),
                    margin=dict(l=150, r=100, t=10, b=20),
                    height=max(300, len(admired) * 28)
                )
                st.plotly_chart(fig, use_container_width=True)

        with col2:
            st.markdown("**You play but never formally liked**")
            st.caption("Listened constantly — never saved. Visceral, unfiltered, real.")
            if visceral.empty:
                st.info("None detected.")
            else:
                fig2 = go.Figure(go.Bar(
                    x=visceral['plays'],
                    y=visceral['artist'],
                    orientation='h',
                    marker_color=VIOLET,
                    text=[str(p) + " plays / " + str(c) + " liked"
                          for p, c in zip(visceral['plays'], visceral['liked_count'])],
                    textposition='outside',
                ))
                fig2.update_layout(
                    plot_bgcolor='#111', paper_bgcolor='#111', font_color='#aaa',
                    yaxis=dict(autorange='reversed', tickfont=dict(size=11, color='#ccc')),
                    xaxis=dict(gridcolor='#1a1a1a', title='Plays'),
                    margin=dict(l=150, r=100, t=10, b=20),
                    height=max(300, len(visceral) * 28)
                )
                st.plotly_chart(fig2, use_container_width=True)

        st.markdown(
            "<div class='insight'>The gap reveals two parallel listening modes. "
            "Your likes reflect cultural identity — artists you respect and want associated with your taste. "
            "Your plays reveal what you actually need musically, day to day, unfiltered. "
            "The overlap is smaller than most people think.</div>",
            unsafe_allow_html=True
        )

    with tab2:
        st.markdown("### Most Liked Artists")
        top = liked_by_artist.sort_values('liked_count', ascending=False).head(30)
        fig3 = go.Figure(go.Bar(
            x=top['liked_count'], y=top['artist'], orientation='h',
            marker_color=VIOLET_LIGHT,
            text=[str(c) for c in top['liked_count']],
            textposition='outside',
        ))
        fig3.update_layout(
            plot_bgcolor='#111', paper_bgcolor='#111', font_color='#aaa',
            yaxis=dict(autorange='reversed', tickfont=dict(size=12, color='#ccc')),
            xaxis=dict(gridcolor='#1a1a1a', title='Tracks liked'),
            margin=dict(l=160, r=60, t=10, b=20),
            height=max(500, len(top) * 28)
        )
        st.plotly_chart(fig3, use_container_width=True)

    with tab3:
        ghost = (
            merged[(merged['liked_count'] > 0) & (merged['plays'] == 0)]
            .sort_values('liked_count', ascending=False)
        )
        st.markdown("### " + str(len(ghost)) + " Artists — Liked, Never Played")
        st.caption("You saved their music at some point. You never came back.")
        if ghost.empty:
            st.success("None — you actually listen to what you like.")
        else:
            st.dataframe(
                ghost[['artist', 'liked_count']].rename(
                    columns={'artist': 'Artist', 'liked_count': 'Tracks Liked'}
                ).reset_index(drop=True),
                use_container_width=True,
                height=600
            )
