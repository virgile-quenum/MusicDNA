import streamlit as st
import pandas as pd
from spotify_auth import api_get, is_authenticated

VIOLET       = "#7C3AED"
VIOLET_LIGHT = "#A78BFA"
GREEN        = "#1DB954"
AMBER        = "#f59e0b"
RED          = "#f87171"

def _card(content, border=VIOLET):
    st.markdown(
        "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
        "border-left:3px solid " + border + ";border-radius:8px;"
        "padding:14px;margin-bottom:10px;'>" + content + "</div>",
        unsafe_allow_html=True
    )

def _section_title(text):
    st.markdown(
        "<div style='color:#A78BFA;font-size:.75em;font-weight:700;"
        "text-transform:uppercase;letter-spacing:.1em;margin:20px 0 12px;'>"
        + text + "</div>",
        unsafe_allow_html=True
    )

def _badge(text, color):
    return (
        "<span style='color:" + color + ";font-size:.72em;font-weight:700;"
        "background:" + color + "22;padding:2px 8px;border-radius:10px;"
        "margin-left:4px;'>" + text + "</span>"
    )

def _spotify_top_artists(tr_key):
    data = api_get("me/top/artists", {"time_range": tr_key, "limit": 20})
    return data.get("items", []) if data else []

def _spotify_top_tracks(tr_key):
    data = api_get("me/top/tracks", {"time_range": tr_key, "limit": 20})
    return data.get("items", []) if data else []

def _history_top_artists(dfm, n=200):
    return (
        dfm.groupby("artistName")
        .agg(plays=("trackName","count"), hours=("ms", lambda x: x.sum()/3600000))
        .sort_values("plays", ascending=False)
        .head(n)
        .reset_index()
    )

def _history_top_tracks(dfm, n=200):
    return (
        dfm.groupby(["artistName","trackName"])
        .agg(plays=("ms","count"), hours=("ms", lambda x: x.sum()/3600000))
        .sort_values("plays", ascending=False)
        .head(n)
        .reset_index()
    )

def _artist_drift(spotify_artists, history_df):
    spot_names  = {a["name"].lower(): a for a in spotify_artists}
    hist_names  = set(history_df["artistName"].str.lower())
    only_spot   = [a for name, a in spot_names.items() if name not in hist_names]
    only_hist   = history_df[~history_df["artistName"].str.lower().isin(spot_names)]
    in_both     = [a for name, a in spot_names.items() if name in hist_names]
    return only_spot, only_hist, in_both

def _track_drift(spotify_tracks, history_df):
    history_df["_key"] = (history_df["trackName"].str.lower() + "|" +
                          history_df["artistName"].str.lower())
    spot_keys = {t["name"].lower() + "|" + t["artists"][0]["name"].lower()
                 for t in spotify_tracks if t.get("artists")}
    hist_hidden = history_df[~history_df["_key"].isin(spot_keys)].head(10)
    over_indexed = []
    for t in spotify_tracks:
        if not t.get("artists"):
            continue
        tname   = t["name"].lower()
        aname   = t["artists"][0]["name"].lower()
        matches = history_df[
            (history_df["trackName"].str.lower() == tname) &
            (history_df["artistName"].str.lower() == aname)
        ]
        plays = int(matches["plays"].sum()) if not matches.empty else 0
        if plays < 5:
            over_indexed.append({
                "name":   t["name"],
                "artist": t["artists"][0]["name"],
                "plays":  plays,
                "pop":    t.get("popularity", 0),
                "url":    t.get("external_urls", {}).get("spotify", ""),
            })
    return hist_hidden, over_indexed

def render(dfm):
    st.markdown(
        "<span style='color:" + VIOLET_LIGHT + ";font-size:.75em;font-weight:700;"
        "text-transform:uppercase;letter-spacing:.1em;'>Full DNA — File + Spotify</span>",
        unsafe_allow_html=True
    )
    st.title("Taste Drift")
    st.caption(
        "Spotify builds your taste profile from recent plays. "
        "Your history knows the truth. Here's where they disagree."
    )

    if not is_authenticated():
        st.warning("Connect Spotify to unlock this analysis.")
        return
    if dfm is None or dfm.empty:
        st.warning("Upload your Extended History zip to enable this analysis.")
        return

    time_range = st.selectbox(
        "Spotify window to compare against",
        ["Last 6 months", "Last 4 weeks", "All time"],
        key="td_time_range"
    )
    tr_map = {"Last 4 weeks": "short_term",
              "Last 6 months": "medium_term",
              "All time": "long_term"}
    tr_key = tr_map[time_range]

    with st.spinner("Loading Spotify data..."):
        spot_artists = _spotify_top_artists(tr_key)
        spot_tracks  = _spotify_top_tracks(tr_key)

    hist_artists = _history_top_artists(dfm, 200)
    hist_tracks  = _history_top_tracks(dfm, 200)

    tab1, tab2, tab3 = st.tabs(["Artist Drift", "Track Drift", "The Verdict"])

    with tab1:
        st.markdown("### Who Spotify thinks you love vs. who your history says you love")

        if not spot_artists:
            st.warning("Could not load Spotify top artists.")
        else:
            only_spot, only_hist, in_both = _artist_drift(spot_artists, hist_artists)

            c1, c2, c3 = st.columns(3)
            with c1:
                st.markdown(
                    "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
                    "border-radius:10px;padding:14px;text-align:center;'>"
                    "<div style='font-size:1.8em;font-weight:900;color:" + GREEN + ";'>
