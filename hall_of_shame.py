import streamlit as st
import pandas as pd

VIOLET       = "#7C3AED"
VIOLET_LIGHT = "#A78BFA"

# keywords that indicate children's content
KIDS_KEYWORDS = [
    'lullaby', 'lullabies', 'nursery', 'rhyme', 'rhymes', 'bébé', 'bebe',
    'enfant', 'children', 'kids', 'baby', 'babies', 'bambin', 'berceuse',
    'comptine', 'dodo', 'minnie', 'mickey', 'peppa', 'cocomelon',
    "music for babies", "música para bebés", "música para bebes",
    "judson mancebo", "lullaby time", "marco bernardo", "beth mclaughlin",
    "anny versini", "henri dès", "henri des",
]

def _is_kids(artist_name, track_name):
    text = (artist_name + " " + track_name).lower()
    return any(kw in text for kw in KIDS_KEYWORDS)

VERDICTS = [
    ("{n}x. Not in your liked tracks. You play it anyway. Make it make sense.",  False, True),
    ("{n}x. {t}. No comment. Actually {n} comments. We are saving them.",        True,  True),
    ("{n}x. {t}. You know every word. Just admit it.",                            True,  False),
    ("{n}x. {t} by {a}. Played {n} times. Never liked. The definition of complicated.", False, False),
    ("{n}x. {t}. The whole body was involved. Every single time.",                True,  False),
    ("{n}x. {t} by {a}. You took it very personally.",                           True,  False),
    ("{n}x. {t}. Not in your liked tracks. The algorithm knows before you do.",  False, True),
    ("{n}x. {t} by {a}. {n} plays. We counted. So did you.",                    True,  False),
]

def _verdict(rank, track, artist, plays, is_liked, is_late):
    template, req_liked, req_late = VERDICTS[rank % len(VERDICTS)]
    return ("#" + str(rank + 1) + " — " +
            template.format(n=plays, t=track, a=artist))

def render(dfm, lib=None):
    st.title("😳 Hall of Shame")
    st.markdown("*Your most-played tracks — identified, exposed, judged. Without mercy.*")

    # get liked tracks for context
    liked_tracks = set()
    if lib:
        if isinstance(lib, dict):
            liked_raw = lib.get('tracks', [])
        elif isinstance(lib, list):
            liked_raw = lib
        else:
            liked_raw = []
        for t in liked_raw:
            name = t.get('track', t.get('trackName', ''))
            if name:
                liked_tracks.add(name.lower().strip())

    # filter out children's content
    df = dfm.copy()
    df['_is_kids'] = df.apply(
        lambda r: _is_kids(r.get('artistName', ''), r.get('trackName', '')), axis=1
    )
    kids_count = df['_is_kids'].sum()
    df_clean   = df[~df['_is_kids']]

    if kids_count > 0:
        st.caption(
            str(int(kids_count)) + " children's content plays excluded. "
            "Use 'Include children's content' toggle to see everything."
        )

    # top tracks
    top = (
        df_clean.groupby(['trackName', 'artistName'])
        .agg(
            plays      =('ms', 'count'),
            late_night =('hour', lambda x: ((x >= 23) | (x <= 3)).sum()),
            ms_total   =('ms', 'sum'),
        )
        .reset_index()
        .sort_values('plays', ascending=False)
        .head(20)
    )

    if top.empty:
        st.info("Not enough data.")
        return

    # table header
    st.markdown(
        "<div style='display:grid;grid-template-columns:1fr 100px 80px 1fr;"
        "padding:8px 16px;border-bottom:1px solid #1e1e1e;margin-bottom:4px;'>"
        "<div style='font-size:.72em;color:#555;text-transform:uppercase;"
        "letter-spacing:.08em;'>Track and Artist</div>"
        "<div style='font-size:.72em;color:#555;text-transform:uppercase;"
        "letter-spacing:.08em;'>Plays</div>"
        "<div style='font-size:.72em;color:#555;text-transform:uppercase;"
        "letter-spacing:.08em;'>Late Night</div>"
        "<div style='font-size:.72em;color:#555;text-transform:uppercase;"
        "letter-spacing:.08em;'>Verdict</div>"
        "</div>",
        unsafe_allow_html=True
    )

    for rank, (_, row) in enumerate(top.iterrows()):
        track   = str(row['trackName'])
        artist  = str(row['artistName'])
        plays   = int(row['plays'])
        late    = int(row['late_night'])
        is_liked = track.lower().strip() in liked_tracks
        liked_label = (
            "<span style='color:#1DB954;font-size:.7em;margin-left:6px;'>· liked</span>"
            if is_liked else
            "<span style='color:#444;font-size:.7em;margin-left:6px;'>· not liked</span>"
        )
        verdict = _verdict(rank, track, artist, plays, is_liked, late > 10)

        border = "#7C3AED" if rank < 3 else "#1e1e1e"

        st.markdown(
            "<div style='display:grid;grid-template-columns:1fr 100px 80px 1fr;"
            "padding:14px 16px;border:1px solid " + border + ";"
            "border-radius:8px;margin-bottom:6px;background:#0f0f0f;'>"

            "<div>"
            "<div style='font-weight:700;color:#fff;font-size:.92em;'>"
            + track + liked_label +
            "</div>"
            "<div style='color:#555;font-size:.78em;margin-top:3px;'>" + artist + "</div>"
            "</div>"

            "<div style='color:#A78BFA;font-weight:900;font-size:1.1em;"
            "align-self:center;'>" + str(plays) + "x</div>"

            "<div style='color:#666;font-size:.88em;align-self:center;'>"
            + str(late) + "x</div>"

            "<div style='color:#555;font-size:.8em;line-height:1.5;"
            "align-self:center;font-style:italic;'>" + verdict + "</div>"

            "</div>",
            unsafe_allow_html=True
        )
