"""
MusicDNA — Powered by DhalsimStream
OAuth Spotify + Extended History zip support
"""

import streamlit as st
import json, zipfile, io, sys, os
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from filters import split
from spotify_auth import handle_callback, is_authenticated, get_auth_url

st.set_page_config(page_title="MusicDNA", page_icon="🎵",
                   layout="wide", initial_sidebar_state="expanded")

VIOLET = "#7C3AED"
VIOLET_LIGHT = "#A78BFA"

st.markdown(f"""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700;900&display=swap');
* {{ font-family: 'Inter', sans-serif; }}
[data-testid="stSidebar"] {{ background: #0a0a0a; border-right: 1px solid #1a1a1a; }}
[data-testid="stSidebar"] * {{ color: #ccc; }}
.metric-card {{ background:#0f0f0f;border:1px solid #1e1e1e;border-radius:12px;
                padding:18px;text-align:center;margin:4px 0; }}
.metric-val {{ font-size:1.9em;font-weight:900;color:{VIOLET_LIGHT}; }}
.metric-lbl {{ font-size:.72em;color:#555;margin-top:5px; }}
.insight {{ background:#0f0f0f;border-left:3px solid {VIOLET};border-radius:6px;
            padding:11px 15px;margin:7px 0;font-size:.87em;color:#ccc;line-height:1.6; }}
.shame {{ background:#0f0505;border-left:3px solid #dc2626;border-radius:6px;
          padding:11px 15px;margin:7px 0;font-size:.87em;color:#ccc;line-height:1.6; }}
h1 {{ color:#fff !important; }}
h2 {{ color:{VIOLET_LIGHT} !important;font-size:1em !important;
      text-transform:uppercase;letter-spacing:.09em; }}
.stTabs [data-baseweb="tab"] {{ color:#666; }}
.stTabs [aria-selected="true"] {{ color:{VIOLET_LIGHT} !important; }}
</style>""", unsafe_allow_html=True)

handle_callback()

for k,v in [('data_loaded',False),('dfm',None),('dfd',None),
             ('lib',{}),('playlists',[]),('mode',None)]:
    if k not in st.session_state: st.session_state[k] = v

def parse_ext(r):
    if not (r.get('master_metadata_track_name')
            and str(r.get('spotify_track_uri','')).startswith('spotify:track:')
            and r.get('ms_played',0) >= 10000): return None
    return {'ts': r['ts'],
            'artistName': r.get('master_metadata_album_artist_name') or '',
            'trackName':  r.get('master_metadata_track_name') or '',
            'albumName':  r.get('master_metadata_album_album_name') or '',
            'ms': r['ms_played'], 'skipped': bool(r.get('skipped',False)),
            'reason_end': r.get('reason_end',''), 'shuffle': bool(r.get('shuffle',False)),
            'track_uri': r.get('spotify_track_uri',''), 'platform': r.get('platform','')}

def parse_std(r):
    if not (r.get('trackName') and r.get('ms_played',0) >= 10000): return None
    return {'ts': r.get('endTime',''), 'artistName': r.get('artistName',''),
            'trackName': r.get('trackName',''), 'albumName': '',
            'ms': r['ms_played'], 'skipped': r['ms_played']<30000,
            'reason_end': '', 'shuffle': False, 'track_uri': '', 'platform': ''}

def make_df(records):
    if not records: return pd.DataFrame()
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
        if lf: lib = json.loads(z.read(lf))
        for pf in pfs:
            try: playlists.extend(json.loads(z.read(pf)).get('playlists',[]))
            except: pass
    return records, lib, playlists, mode

with st.sidebar:
    st.markdown(
