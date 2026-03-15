"""
MusicDNA — Powered by DhalsimStream
Supports: Extended History zip + optional Standard zip (for Likes & Playlists)
"""

import streamlit as st
import json, zipfile, io, sys, os
import pandas as pd

sys.path.insert(0, os.path.dirname(__file__))
from filters import split

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
    st.markdown(f"""<div style='padding:16px 0 8px;text-align:center;'>
      <div style='font-size:1.5em;font-weight:900;color:#fff;'>🎵 MusicDNA</div>
      <div style='font-size:.68em;color:#555;margin-top:2px;'>powered by DhalsimStream</div>
    </div>""", unsafe_allow_html=True)
    st.markdown("---")

    if not st.session_state.data_loaded:
        st.markdown("### 1. Extended History *(required)*")
        st.caption("Your full Spotify history — up to 12+ years.")
        zip1 = st.file_uploader("Extended history zip", type="zip",
                                 key="zip1", label_visibility="collapsed")
        st.markdown("### 2. Standard Export *(optional)*")
        st.caption("Unlocks: Likes Autopsy, Playlist Autopsy, Hall of Shame enriched.")
        zip2 = st.file_uploader("Standard export zip", type="zip",
                                 key="zip2", label_visibility="collapsed")
        if zip1:
            if st.button("🚀 Analyse", use_container_width=True, type="primary"):
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
        has_lib = bool(lib.get('tracks'))
        has_pl  = bool(st.session_state.playlists)
        if mode == 'extended':
            st.success(f"✅ Extended ({int(dfm['year'].min())}–{int(dfm['year'].max())})")
        else:
            st.warning("⚠️ Standard export (12 months only)")
        if has_lib: st.success("✅ Likes data loaded")
        else:       st.warning("⚠️ No likes — upload standard zip")
        if has_pl:  st.success("✅ Playlist data loaded")
        else:       st.warning("⚠️ No playlists — upload standard zip")
        st.markdown("---")
        page = st.radio("", [
            "🏠 Overview","🎤 Artists & Tracks","🕐 Time Patterns",
            "👶 Parent Mode","💔 Likes Autopsy","📋 Playlist Autopsy",
            "😳 Hall of Shame","⭐ Celebrity Twin","🔮 Musical Horoscope",
        ], label_visibility="collapsed")
        st.markdown("---")
        kids_on = st.toggle("👶 Include daughters content", value=False)
        st.caption(f"Your music: **{len(dfm):,}** plays · **{dfm['ms'].sum()/3600000:.0f}h**")
        if not dfd.empty:
            st.caption(f"Kids: **{dfd['ms'].sum()/3600000:.0f}h**")
        st.markdown("---")
        if st.button("🔄 Load new file", use_container_width=True):
            for k in ['data_loaded','dfm','dfd','lib','playlists','mode']:
                st.session_state[k] = False if k=='data_loaded' else ({} if k=='lib' else ([] if k=='playlists' else None))
            st.rerun()

if not st.session_state.data_loaded:
    st.markdown(f"""
    <div style='max-width:640px;margin:60px auto;text-align:center;'>
      <div style='font-size:4em;'>🎵</div>
      <h1 style='font-size:2.8em;font-weight:900;'>Music<span style='color:{VIOLET_LIGHT};'>DNA</span></h1>
      <p style='color:#555;font-size:.9em;margin-top:4px;'>powered by DhalsimStream</p>
      <p style='color:#777;font-size:1em;line-height:1.9;margin:28px 0;'>
        Upload your Spotify data and discover who you really are as a listener.<br>
        12 years of history. Not Wrapped. No fluff. Just data.
      </p>
      <div style='background:#0f0f0f;border:1px solid #1e1e1e;border-radius:12px;padding:24px;text-align:left;margin-bottom:16px;'>
        <div style='color:{VIOLET_LIGHT};font-weight:700;font-size:.82em;text-transform:uppercase;letter-spacing:.08em;margin-bottom:14px;'>
          📦 Step 1 — Extended History (required)</div>
        <div style='color:#888;font-size:.85em;line-height:2.2;'>
          1. Go to <b style='color:#fff;'>spotify.com/account/privacy</b><br>
          2. Scroll to "Download your data"<br>
          3. Select <b style='color:#fff;'>Extended streaming history</b> → Request<br>
          4. Wait up to 30 days → download zip → upload ←
        </div>
      </div>
      <div style='background:#0a0a0a;border:1px solid #f59e0b33;border-radius:12px;padding:20px;text-align:left;'>
        <div style='color:#f59e0b;font-weight:700;font-size:.82em;text-transform:uppercase;letter-spacing:.08em;margin-bottom:10px;'>
          ⚡ Step 2 — Standard Export (optional)</div>
        <div style='color:#666;font-size:.83em;line-height:2;'>
          Same page → select <b style='color:#aaa;'>Account data</b> (arrives in minutes).<br>
          Unlocks: <b style='color:#aaa;'>Likes Autopsy · Playlist Autopsy · Hall of Shame</b>
        </div>
      </div>
    </div>""", unsafe_allow_html=True)
    st.stop()

dfm       = st.session_state.dfm
dfd       = st.session_state.dfd
lib       = st.session_state.lib
playlists = st.session_state.playlists
kids_on   = False
df        = pd.concat([dfm, dfd]) if (kids_on and not dfd.empty) else dfm

if   page == "🏠 Overview":          import overview;         overview.render(dfm, dfd, kids_on)
elif page == "🎤 Artists & Tracks":  import artists;          artists.render(df)
elif page == "🕐 Time Patterns":     import time_patterns;    time_patterns.render(df)
elif page == "👶 Parent Mode":       import parent_mode;      parent_mode.render(dfm, dfd, [])
elif page == "💔 Likes Autopsy":     import likes_autopsy;    likes_autopsy.render(dfm, lib)
elif page == "📋 Playlist Autopsy":  import playlist_autopsy; playlist_autopsy.render(dfm, playlists)
elif page == "😳 Hall of Shame":     import hall_of_shame;    hall_of_shame.render(dfm, lib)
elif page == "⭐ Celebrity Twin":    import celebrity_twin;   celebrity_twin.render(dfm)
elif page == "🔮 Musical Horoscope": import horoscope;        horoscope.render(dfm, dfd)
