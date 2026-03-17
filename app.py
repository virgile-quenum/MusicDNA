import streamlit as st
import json, zipfile, io, sys, os
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from filters import split
from spotify_auth import handle_callback, is_authenticated, get_auth_url

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
              ('lib', {}), ('playlists', []), ('mode', None)]:
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
            lib = json.loads(z.read(lf))
        for pf in pfs:
            try:
                playlists.extend(json.loads(z.read(pf)).get('playlists', []))
            except:
                pass
    return records, lib, playlists, mode

with st.sidebar:
    st.markdown(
        "<div style='padding:16px 0 8px;text-align:center;'>"
        "<div style='font-size:1.5em;font-weight:900;color:#fff;'>🎵 MusicDNA</div>"
        "<div style='font-size:.68em;color:#555;margin-top:2px;'>powered by DhalsimStream</div>"
        "</div>",
        unsafe_allow_html=True
    )
    st.markdown("---")

    if not st.session_state.data_loaded:
        st.markdown(
            "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
            "border-radius:8px;padding:14px;margin-bottom:12px;'>"
            "<div style='color:#A78BFA;font-weight:700;font-size:.8em;"
            "text-transform:uppercase;letter-spacing:.06em;margin-bottom:10px;'>"
            "How to get started</div>"
            "<div style='color:#666;font-size:.8em;line-height:2;'>"
            "<b style='color:#ccc;'>Step 1</b> — Upload Extended History zip<br>"
            "<b style='color:#ccc;'>Step 2</b> — Upload Standard Export zip<br>"
            "<b style='color:#ccc;'>Step 3</b> — Click Analyse<br>"
            "<b style='color:#ccc;'>Step 4</b> — Connect Spotify for Discovery"
            "</div>"
            "</div>",
            unsafe_allow_html=True
        )

    if is_authenticated():
        st.success("Spotify connected")
        if st.button("Disconnect", use_container_width=True):
            del st.session_state['spotify_token']
            st.rerun()
    else:
        auth_url = get_auth_url()
        st.markdown(
            "<a href='" + auth_url + "' target='_self' "
            "style='display:block;background:#1DB954;color:#000;font-weight:800;"
            "text-align:center;padding:10px;border-radius:8px;"
            "text-decoration:none;font-size:.9em;margin-bottom:8px;'>"
            "Step 4 — Connect Spotify</a>",
            unsafe_allow_html=True
        )
        st.caption("Enables Discovery and recommendations")

    st.markdown("---")

    if not st.session_state.data_loaded:
        st.markdown("**Step 1 — Extended History** *(required)*")
        st.caption("Your full 12-year analysis. The big zip.")
        zip1 = st.file_uploader("Extended history zip", type="zip",
                                 key="zip1", label_visibility="collapsed")
        st.markdown("**Step 2 — Standard Export** *(recommended)*")
        st.caption("Unlocks Likes Autopsy and Playlist Autopsy. The small zip.")
        zip2 = st.file_uploader("Standard export zip", type="zip",
                                 key="zip2", label_visibility="collapsed")
        if zip1:
            if st.button("Step 3 — Analyse", use_container_width=True, type="primary"):
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
    else:
        dfm  = st.session_state.dfm
        dfd  = st.session_state.dfd
        mode = st.session_state.mode
        lib  = st.session_state.lib
        if mode == 'extended':
            st.success("Extended (" + str(int(dfm['year'].min())) + "-" + str(int(dfm['year'].max())) + ")")
        else:
            st.warning("Standard export (12 months only)")
        if lib.get('tracks'):          st.success("Likes data loaded")
        else:                          st.warning("No likes - upload standard zip")
        if st.session_state.playlists: st.success("Playlist data loaded")
        else:                          st.warning("No playlists - upload standard zip")
        st.markdown("---")
        if st.button("Load new file", use_container_width=True):
            for k in ['data_loaded', 'dfm', 'dfd', 'lib', 'playlists', 'mode']:
                st.session_state[k] = False if k == 'data_loaded' else ({} if k == 'lib' else ([] if k == 'playlists' else None))
            st.rerun()

    if st.session_state.data_loaded:
        st.markdown("---")
        page = st.radio("", [
            "Overview", "Artists and Tracks", "Time Patterns",
            "Parent Mode", "Likes Autopsy", "Playlist Autopsy",
            "Hall of Shame", "Celebrity Twin", "Musical Horoscope",
            "Discovery",
        ], label_visibility="collapsed")
        kids_on = st.toggle("Include daughters content", value=False)
        dfm_ = st.session_state.dfm
        if dfm_ is not None:
            st.caption("Your music: " + str(len(dfm_)) + " plays - " + str(round(dfm_['ms'].sum()/3600000)) + "h")

if not st.session_state.data_loaded and not is_authenticated():
    import landing
    landing.render(get_auth_url)
    st.stop()

if not st.session_state.data_loaded and is_authenticated():
    import discovery
    discovery.render(None)
    st.stop()

dfm       = st.session_state.dfm
dfd       = st.session_state.dfd
lib       = st.session_state.lib
playlists = st.session_state.playlists
kids_on   = False
df        = pd.concat([dfm, dfd]) if (kids_on and not dfd.empty) else dfm

if   "Overview"   in page: import overview;         overview.render(dfm, dfd, kids_on)
elif "Artists"    in page: import artists;          artists.render(df)
elif "Time"       in page: import time_patterns;    time_patterns.render(df)
elif "Parent"     in page: import parent_mode;      parent_mode.render(dfm, dfd, [])
elif "Likes"      in page: import likes_autopsy;    likes_autopsy.render(dfm, lib)
elif "Playlist"   in page: import playlist_autopsy; playlist_autopsy.render(dfm, playlists)
elif "Hall"       in page: import hall_of_shame;    hall_of_shame.render(dfm, lib)
elif "Celebrity"  in page: import celebrity_twin;   celebrity_twin.render(dfm)
elif "Horoscope"  in page: import horoscope;        horoscope.render(dfm, dfd)
elif "Discovery"  in page: import discovery;        discovery.render(dfm)
