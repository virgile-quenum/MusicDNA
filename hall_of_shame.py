import streamlit as st
import pandas as pd
from filters import is_kids_content

VIOLET       = "#7C3AED"
VIOLET_LIGHT = "#A78BFA"

SARCASMS = [
    "You never liked it. Never saved it. Played it {n} times. That's not an accident.",
    "{n} plays and not a single like. You know exactly what you're doing.",
    "Played {n} times. Zero accountability. Respect, actually.",
    "{n} plays. Not in any playlist. Not liked. Just you, alone, committing.",
    "You built a whole relationship with this track. Officially unacknowledged.",
    "{n} plays with no paper trail. This is your listening equivalent of a burner phone.",
    "The algorithm knows. You know. Now everyone knows. {n} plays.",
    "Not liked. Not saved. {n} plays. You are the definition of 'it's complicated'.",
    "{n} plays and you still haven't liked it. Commitment issues or taste issues — pick one.",
    "Played {n} times. No trace in your library. Just vibes and plausible deniability.",
    "You have listened to this {n} times while actively refusing to admit you like it.",
    "{n} plays. This track has more time in your ears than most of your friends.",
    "You skipped saving it. You never skipped playing it. {n} times.",
    "{n} plays. No like. No playlist. A ghost relationship with a very real track.",
    "This is what {n} plays of unacknowledged love looks like.",
]

def _sarcasm(rank, track, artist, plays):
    template = SARCASMS[rank % len(SARCASMS)]
    return template.format(n=plays, t=track, a=artist)


def render(dfm, lib=None, playlists=None):
    st.title("😳 Hall of Shame")
    st.markdown("*Tracks you play constantly — but have never liked, never saved. Pure unfiltered taste.*")

    # build liked set
    liked_tracks = set()
    if lib:
        raw = lib.get('tracks', []) if isinstance(lib, dict) else (lib if isinstance(lib, list) else [])
        for t in raw:
            name = t.get('track', t.get('trackName', ''))
            if name:
                liked_tracks.add(name.lower().strip())

    # build playlist tracks set
    playlist_tracks = set()
    if playlists:
        for pl in playlists:
            for item in pl.get('items', []):
                track = item.get('track', {})
                name  = track.get('trackName', '')
                if name:
                    playlist_tracks.add(name.lower().strip())

    # filter children's content
    df = dfm.copy()
    df['_is_kids'] = df.apply(
        lambda r: is_kids_content(
            r.get('artistName', ''), r.get('trackName', ''), r.get('albumName', '')
        ), axis=1
    )
    kids_count = df['_is_kids'].sum()
    df_clean   = df[~df['_is_kids']]

    if kids_count > 0:
        st.caption(
            str(int(kids_count)) + " children's content plays excluded. "
            "Toggle 'Include children's content' in the sidebar to see everything."
        )

    # aggregate
    top_all = (
        df_clean.groupby(['trackName', 'artistName'])
        .agg(plays=('ms', 'count'), late_night=('hour', lambda x: ((x >= 23) | (x <= 3)).sum()))
        .reset_index()
        .sort_values('plays', ascending=False)
    )

    # THE SHAME FILTER: not liked AND not in any playlist
    top_all['_key']       = top_all['trackName'].str.lower().str.strip()
    top_all['is_liked']   = top_all['_key'].isin(liked_tracks)
    top_all['in_playlist']= top_all['_key'].isin(playlist_tracks)

    shame = top_all[
        (~top_all['is_liked']) & (~top_all['in_playlist'])
    ].head(20)

    if shame.empty:
        st.success("Nothing to shame — everything you play is either liked or in a playlist. Suspiciously tidy.")
        return

    # header
    st.markdown(
        "<div style='display:grid;grid-template-columns:1fr 90px 80px 1fr;"
        "padding:8px 16px;border-bottom:1px solid #1e1e1e;margin-bottom:4px;'>"
        "<span style='font-size:.72em;color:#555;text-transform:uppercase;letter-spacing:.08em;'>Track</span>"
        "<span style='font-size:.72em;color:#555;text-transform:uppercase;letter-spacing:.08em;'>Plays</span>"
        "<span style='font-size:.72em;color:#555;text-transform:uppercase;letter-spacing:.08em;'>Late night</span>"
        "<span style='font-size:.72em;color:#555;text-transform:uppercase;letter-spacing:.08em;'>Verdict</span>"
        "</div>",
        unsafe_allow_html=True
    )

    for rank, (_, row) in enumerate(shame.iterrows()):
        track  = str(row['trackName'])
        artist = str(row['artistName'])
        plays  = int(row['plays'])
        late   = int(row['late_night'])
        verdict = _sarcasm(rank, track, artist, plays)
        border  = VIOLET if rank < 3 else "#1e1e1e"

        st.markdown(
            "<div style='display:grid;grid-template-columns:1fr 90px 80px 1fr;"
            "padding:14px 16px;border:1px solid " + border + ";"
            "border-radius:8px;margin-bottom:6px;background:#0f0f0f;align-items:center;'>"

            "<div>"
            "<div style='font-weight:700;color:#fff;font-size:.92em;'>" + track + "</div>"
            "<div style='color:#555;font-size:.78em;margin-top:3px;'>" + artist + "</div>"
            "</div>"

            "<div style='color:#A78BFA;font-weight:900;font-size:1.1em;'>" + str(plays) + "x</div>"

            "<div style='color:#666;font-size:.88em;'>" + str(late) + "x</div>"

            "<div style='color:#555;font-size:.8em;line-height:1.5;font-style:italic;'>"
            + verdict + "</div>"

            "</div>",
            unsafe_allow_html=True
        )

    st.markdown("---")
    st.markdown(
        "<div style='color:#333;font-size:.75em;text-align:center;'>"
        "These tracks have no trace in your library. No like. No playlist. "
        "Just plays. The most honest data in this app."
        "</div>",
        unsafe_allow_html=True
    )
