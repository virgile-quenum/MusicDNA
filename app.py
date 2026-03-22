import streamlit as st
import json, zipfile, io, sys, os
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from filters import split
from spotify_auth import handle_callback, is_authenticated, get_auth_url, render_connect_button

st.set_page_config(page_title="MusicDNA", page_icon="🎵",
                   layout="wide", initial_sidebar_state="expanded")

CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');
* { font-family: 'Inter', sans-serif; }
[data-testid="stSidebar"] { background: #0a0a0a; border-right: 1px solid #1a1a1a; }
[data-testid="stSidebar"] * { color: #ccc; }
.metric-card { background:#0f0f0f; border:1px solid #1e1e1e; border-radius:12px; padding:18px; text-align:center; margin:4px 0; }
.metric-val { font-size:1.9em; font-weight:900; color:#A78BFA; }
.metric-lbl { font-size:.72em; color:#555; margin-top:5px; }
.insight { background:#0f0f0f; border-left:3px solid #7C3AED; border-radius:6px; padding:11px 15px; margin:7px 0; font-size:.87em; color:#ccc; line-height:1.6; }
.shame { background:#0f0505; border-left:3px solid #dc2626; border-radius:6px; padding:11px 15px; margin:7px 0; font-size:.87em; color:#ccc; line-height:1.6; }
h1 { color:#fff !important; }
h2 { color:#A78BFA !important; font-size:1em !important; text-transform:uppercase; letter-spacing:.09em; }
.stTabs [data-baseweb="tab"] { color:#666; }
.stTabs [aria-selected="true"] { color:#A78BFA !important; }
</style>
"""
st.markdown(CSS, unsafe_allow_html=True)

handle_callback()

for k, v in [('data_loaded', False), ('dfm', None), ('dfd', None),
              ('lib', {}), ('playlists', []), ('mode', None),
              ('_page', 'Overview'), ('kids_on', False)]:
    if k not in st.session_state:
        st.session_state[k] = v

def parse_ext(r):
    if not (r.get('master_metadata_track_name')
            and str(r.get('spotify_track_uri', '')).startswith('spotify:track:')
            and r.get('ms_played', 0) >= 10000):
        return None
    return {
        'ts':         r['ts'],
        'artistName': r.get('master_metadata_album_artist_name') or '',
        'trackName':  r.get('master_metadata_track_name') or '',
        'albumName':  r.get('master_metadata_album_album_name') or '',
        'ms':         r['ms_played'],
        'skipped':    bool(r.get('skipped', False)),
        'reason_end': r.get('reason_end', ''),
        'shuffle':    bool(r.get('shuffle', False)),
        'track_uri':  r.get('spotify_track_uri', ''),
        'platform':   r.get('platform', ''),
    }

def parse_std(r):
    if not (r.get('trackName') and r.get('ms_played', 0) >= 10000):
        return None
    return {
        'ts': r.get('endTime', ''), 'artistName': r.get('artistName', ''),
        'trackName': r.get('trackName', ''), 'albumName': '',
        'ms': r['ms_played'], 'skipped': r['ms_played'] < 30000,
        'reason_end': '', 'shuffle': False, 'track_uri': '', 'platform': '',
    }

def make_df(records):
    if not records:
        return pd.DataFrame()
    df = pd.DataFrame(records)
    df['ts']    = pd.to_datetime(df['ts'], utc=True, errors='coerce').dt.tz_localize(None)
    df['year']  = df['ts'].dt.year
    df['month'] = df['ts'].dt.month
    df['hour']  = df['ts'].dt.hour
    df['dow']   = df['ts'].dt.dayofweek
    df['ym']    = df['ts'].dt.to_period('M').astype(str)
    return df

def read_zip(uploaded):
    records, lib, playlists, mode = [], {}, [], None
    with zipfile.ZipFile(io.BytesIO(uploaded.read())) as z:
        names = z.namelist()
        ext = [n for n in names if 'Streaming_History_Audio_' in n and n.endswith('.json')]
        std = [n for n in names if 'StreamingHistory_music_' in n and n.endswith('.json')]
        lf  = next((n for n in names if 'YourLibrary.json' in n), None)
        pfs = [n for n in names if 'Playlist' in n and n.endswith('.json')]
        if ext:
            mode = 'extended'
            for fn in ext:
                for r in json.loads(z.read(fn)):
                    rec = parse_ext(r)
                    if rec: records.append(rec)
        elif std:
            mode = 'standard'
            for fn in std:
                for r in json.loads(z.read(fn)):
                    rec = parse_std(r)
                    if rec: records.append(rec)
        if lf:
            raw_lib = json.loads(z.read(lf))
            lib = raw_lib if isinstance(raw_lib, dict) else {'tracks': raw_lib} if isinstance(raw_lib, list) else {}
        for pf in pfs:
            try:
                playlists.extend(json.loads(z.read(pf)).get('playlists', []))
            except:
                pass
    return records, lib, playlists, mode

PAGES_BASE = [
    "Overview", "Musical Horoscope", "Likes Autopsy", "Playlist Autopsy",
    "Discovery", "Hall of Shame", "Parent Mode", "Celebrity Twin",
    "Artists and Tracks", "Time Patterns",
]
PAGES_FULL_DNA = ["Taste Drift", "Audio Profile"]

# ── SIDEBAR ───────────────────────────────────────────────────────────────────

with st.sidebar:
    st.markdown(
        "<div style='padding:16px 0 8px;text-align:center;'>"
        "<div style='font-size:1.5em;font-weight:900;color:#fff;'>🎵 MusicDNA</div>"
        "<div style='font-size:.68em;color:#555;margin-top:2px;'>powered by DhalsimStream</div>"
        "</div>",
        unsafe_allow_html=True
    )
    st.markdown("---")

    if is_authenticated():
        st.success("✓ Spotify connected")
        if st.button("Disconnect", use_container_width=True):
            del st.session_state['spotify_token']
            st.rerun()
    else:
        # warn if files are loaded — connecting will wipe session
        if st.session_state.data_loaded:
            st.warning(
                "Connecting Spotify will reload the page and your files will need "
                "to be re-uploaded. Connect Spotify first next time."
            )
        render_connect_button("Connect Spotify")
        st.caption("Connect first — then upload your files to keep your session.")

    st.markdown("---")

    if not st.session_state.data_loaded:
        if is_authenticated():
            st.markdown(
                "<div style='background:#0f0f0f;border:1px solid #7C3AED44;"
                "border-radius:8px;padding:12px;margin-bottom:12px;'>"
                "<div style='color:#A78BFA;font-size:.78em;font-weight:700;margin-bottom:4px;'>"
                "Unlock Full DNA</div>"
                "<div style='color:#555;font-size:.76em;line-height:1.6;'>"
                "Upload your Extended History zip to add 9 deep analyses, "
                "Taste Drift and Audio Profile."
                "</div></div>",
                unsafe_allow_html=True
            )

        st.markdown("**Step 1 — Extended History**")
        st.caption("Your full 12-year analysis.")
        zip1 = st.file_uploader("Extended history zip", type="zip",
                                 key="zip1", label_visibility="collapsed")
        st.markdown("**Step 2 — Standard Export**")
        st.caption("Unlocks Likes Autopsy and Playlist Autopsy.")
        zip2 = st.file_uploader("Standard export zip", type="zip",
                                 key="zip2", label_visibility="collapsed")

        if zip1:
            if st.button("Analyse", use_container_width=True, type="primary"):
                with st.spinner("Loading your history..."):
                    records, lib, playlists, mode = read_zip(zip1)
                    if zip2:
                        _, lib2, pl2, _ = read_zip(zip2)
                        if lib2: lib = lib2
                        if pl2:  playlists = pl2
                    if records:
                        my_r, dau_r = split(records)
                        st.session_state.dfm       = make_df(my_r)
                        st.session_state.dfd       = make_df(dau_r)
                        st.session_state.lib       = lib
                        st.session_state.playlists = playlists
                        st.session_state.mode      = mode
                        st.session_state.data_loaded = True
                        st.rerun()
                    else:
                        st.error("No music data found.")

        if is_authenticated():
            st.markdown("---")
            st.session_state['_page'] = "spotify_mode"

    else:
        dfm_  = st.session_state.dfm
        mode_ = st.session_state.mode
        lib_  = st.session_state.lib

        if mode_ == 'extended':
            st.success("Extended (" + str(int(dfm_['year'].min())) + "–" + str(int(dfm_['year'].max())) + ")")
        else:
            st.warning("Standard export (12 months only)")

        has_likes     = bool(lib_.get('tracks')) if isinstance(lib_, dict) else bool(lib_)
        has_playlists = bool(st.session_state.playlists)
        if not has_likes:
            st.warning("No likes — upload standard zip")
        if not has_playlists:
            st.warning("No playlists — upload standard zip")

        st.markdown("---")
        if st.button("Load new file", use_container_width=True):
            for k in ['data_loaded','dfm','dfd','lib','playlists','mode']:
                st.session_state[k] = False if k=='data_loaded' else ({} if k=='lib' else ([] if k=='playlists' else None))
            st.rerun()

        st.markdown("---")

        nav_pages = PAGES_BASE.copy()
        if is_authenticated():
            st.markdown(
                "<div style='color:#1DB954;font-size:.72em;font-weight:700;"
                "text-transform:uppercase;letter-spacing:.06em;margin-bottom:4px;'>"
                "Full DNA unlocked</div>",
                unsafe_allow_html=True
            )
            nav_pages += PAGES_FULL_DNA

        st.session_state['_page'] = st.radio("", nav_pages, label_visibility="collapsed")

        kids_on = st.toggle("Include children's content", value=False)
        st.session_state['kids_on'] = kids_on
        st.caption(
            "Your music: " + str(len(dfm_)) + " plays · "
            + str(round(dfm_['ms'].sum() / 3600000)) + "h"
        )

# ── ROUTING ───────────────────────────────────────────────────────────────────

page = st.session_state.get('_page', 'Overview')

if not st.session_state.data_loaded and not is_authenticated():
    import landing
    landing.render(get_auth_url, data_loaded=False)
    st.stop()

if not st.session_state.data_loaded and is_authenticated():
    import spotify_mode
    spotify_mode.render()
    st.stop()

if not st.session_state.data_loaded:
    st.stop()

dfm       = st.session_state.dfm
dfd       = st.session_state.dfd
lib       = st.session_state.lib
playlists = st.session_state.playlists
kids_on   = st.session_state.get('kids_on', False)
df        = pd.concat([dfm, dfd]) if (kids_on and dfd is not None and not dfd.empty) else dfm

if   "Overview"          in page: import overview;         overview.render(dfm, dfd, kids_on)
elif "Musical Horoscope" in page: import horoscope;        horoscope.render(dfm, dfd)
elif "Likes Autopsy"     in page: import likes_autopsy;    likes_autopsy.render(dfm, lib)
elif "Playlist Autopsy"  in page: import playlist_autopsy; playlist_autopsy.render(dfm, playlists)
elif "Discovery"         in page: import discovery;        discovery.render(dfm)
elif "Hall of Shame"     in page: import hall_of_shame;    hall_of_shame.render(dfm, lib, playlists)
elif "Parent Mode"       in page: import parent_mode;      parent_mode.render(dfm, dfd, [])
elif "Celebrity Twin"    in page: import celebrity_twin;   celebrity_twin.render(dfm)
elif "Artists and Tracks"in page: import artists;          artists.render(df)
elif "Time Patterns"     in page: import time_patterns;    time_patterns.render(df)
elif "Taste Drift"       in page: import taste_drift;      taste_drift.render(dfm)
elif "Audio Profile"     in page: import audio_profile;    audio_profile.render(dfm)
