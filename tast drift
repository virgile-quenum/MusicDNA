import streamlit as st
import pandas as pd
from spotify_auth import api_get, is_authenticated

VIOLET       = "#7C3AED"
VIOLET_LIGHT = "#A78BFA"
GREEN        = "#1DB954"
AMBER        = "#f59e0b"
RED          = "#f87171"

# ── helpers ───────────────────────────────────────────────────────────────────

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

# ── analysis functions ────────────────────────────────────────────────────────

def _spotify_top_artists(tr_key):
    data = api_get("me/top/artists", {"time_range": tr_key, "limit": 20})
    return data.get("items", []) if data else []

def _spotify_top_tracks(tr_key):
    data = api_get("me/top/tracks", {"time_range": tr_key, "limit": 20})
    return data.get("items", []) if data else []

def _history_top_artists(dfm, n=20):
    return (
        dfm.groupby("artistName")
        .agg(plays=("trackName","count"), hours=("ms", lambda x: x.sum()/3600000))
        .sort_values("plays", ascending=False)
        .head(n)
        .reset_index()
    )

def _history_top_tracks(dfm, n=20):
    return (
        dfm.groupby(["artistName","trackName"])
        .agg(plays=("ms","count"), hours=("ms", lambda x: x.sum()/3600000))
        .sort_values("plays", ascending=False)
        .head(n)
        .reset_index()
    )


def _artist_drift(spotify_artists, history_df):
    """
    Compare Spotify's top 20 artists vs. history's top 20 artists.
    Returns: only_spotify, only_history, in_both
    """
    spot_names  = {a["name"].lower(): a for a in spotify_artists}
    hist_names  = set(history_df["artistName"].str.lower())

    only_spot   = [a for name, a in spot_names.items() if name not in hist_names]
    only_hist   = history_df[~history_df["artistName"].str.lower().isin(spot_names)]
    in_both     = [a for name, a in spot_names.items() if name in hist_names]

    return only_spot, only_hist, in_both


def _track_drift(spotify_tracks, history_df):
    """
    Tracks in Spotify top 20 but rarely played in history — Spotify over-indexing.
    Tracks played a lot in history but not in Spotify top 20 — history says more.
    """
    spot_names = {(t["name"].lower(), t["artists"][0]["name"].lower()): t
                  for t in spotify_tracks if t.get("artists")}

    history_df["_key"] = (history_df["trackName"].str.lower() + "|" +
                          history_df["artistName"].str.lower())
    spot_keys   = {t["name"].lower() + "|" + t["artists"][0]["name"].lower()
                   for t in spotify_tracks if t.get("artists")}

    # top history tracks not in Spotify top 20
    hist_hidden = history_df[~history_df["_key"].isin(spot_keys)].head(10)

    # Spotify top tracks with low play count in history
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
                "name":    t["name"],
                "artist":  t["artists"][0]["name"],
                "plays":   plays,
                "pop":     t.get("popularity", 0),
                "url":     t.get("external_urls", {}).get("spotify", ""),
            })

    return hist_hidden, over_indexed


# ── render ────────────────────────────────────────────────────────────────────

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

    hist_artists = _history_top_artists(dfm, 30)
    hist_tracks  = _history_top_tracks(dfm, 50)

    tab1, tab2, tab3 = st.tabs(["Artist Drift", "Track Drift", "The Verdict"])

    # ── Tab 1: artist drift ───────────────────────────────────────────────────
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
                    "<div style='font-size:1.8em;font-weight:900;color:" + GREEN + ";'>"
                    + str(len(in_both)) + "</div>"
                    "<div style='font-size:.72em;color:#555;margin-top:4px;'>in both lists</div>"
                    "</div>", unsafe_allow_html=True
                )
            with c2:
                st.markdown(
                    "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
                    "border-radius:10px;padding:14px;text-align:center;'>"
                    "<div style='font-size:1.8em;font-weight:900;color:" + AMBER + ";'>"
                    + str(len(only_spot)) + "</div>"
                    "<div style='font-size:.72em;color:#555;margin-top:4px;'>"
                    "Spotify says yes, history disagrees</div>"
                    "</div>", unsafe_allow_html=True
                )
            with c3:
                st.markdown(
                    "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
                    "border-radius:10px;padding:14px;text-align:center;'>"
                    "<div style='font-size:1.8em;font-weight:900;color:" + VIOLET_LIGHT + ";'>"
                    + str(len(only_hist)) + "</div>"
                    "<div style='font-size:.72em;color:#555;margin-top:4px;'>"
                    "History says yes, Spotify forgot</div>"
                    "</div>", unsafe_allow_html=True
                )

            if only_spot:
                _section_title("Spotify over-indexes — you played these recently but not historically")
                cols = st.columns(2)
                for i, a in enumerate(only_spot):
                    genres = ", ".join(a.get("genres", [])[:2])
                    url    = a.get("external_urls", {}).get("spotify", "")
                    link   = ("<a href='" + url + "' target='_blank' style='color:" +
                              VIOLET_LIGHT + ";font-size:.75em;'>Open ↗</a>") if url else ""
                    with cols[i % 2]:
                        _card(
                            "<div style='display:flex;justify-content:space-between;'>"
                            "<div>"
                            "<div style='font-weight:700;color:#fff;'>" + a["name"] + "</div>"
                            + ("<div style='color:#555;font-size:.78em;margin-top:2px;'>"
                               + genres + "</div>" if genres else "") +
                            "</div><div>" + link + "</div></div>",
                            border=AMBER
                        )

            if not only_hist.empty:
                _section_title("Your history remembers — Spotify forgot these artists")
                cols = st.columns(2)
                for i, (_, row) in enumerate(only_hist.iterrows()):
                    with cols[i % 2]:
                        _card(
                            "<div style='font-weight:700;color:#fff;'>"
                            + str(row["artistName"]) + "</div>"
                            "<div style='color:#555;font-size:.78em;margin-top:3px;'>"
                            + str(int(row["plays"])) + " plays · "
                            + str(round(row["hours"], 1)) + "h total"
                            "</div>",
                            border=VIOLET_LIGHT
                        )

    # ── Tab 2: track drift ────────────────────────────────────────────────────
    with tab2:
        st.markdown("### Tracks Spotify thinks define you — vs. what you actually played")

        if not spot_tracks:
            st.warning("Could not load Spotify top tracks.")
        else:
            hist_hidden, over_indexed = _track_drift(spot_tracks, hist_tracks)

            if over_indexed:
                _section_title(
                    "Spotify top 20 — but barely in your history "
                    "(" + str(len(over_indexed)) + " tracks)"
                )
                st.caption("These tracks appear in your current Spotify top 20 but have fewer than 5 plays in your full history.")
                cols = st.columns(2)
                for i, t in enumerate(over_indexed):
                    url  = t.get("url", "")
                    link = ("<a href='" + url + "' target='_blank' style='color:" +
                            VIOLET_LIGHT + ";font-size:.75em;'>Open ↗</a>") if url else ""
                    with cols[i % 2]:
                        _card(
                            "<div style='display:flex;justify-content:space-between;align-items:center;'>"
                            "<div>"
                            "<div style='font-weight:700;color:#fff;font-size:.9em;'>"
                            + t["name"] + "</div>"
                            "<div style='color:#666;font-size:.78em;margin-top:2px;'>"
                            + t["artist"] + "</div>"
                            "<div style='color:#444;font-size:.75em;margin-top:2px;'>"
                            + str(t["plays"]) + " plays in history · popularity "
                            + str(t["pop"]) + "</div>"
                            "</div><div>" + link + "</div></div>",
                            border=AMBER
                        )

            if not hist_hidden.empty:
                _section_title("Your most-played tracks — not in Spotify's top 20")
                st.caption("These are the tracks your history says define you. Spotify doesn't see them anymore.")
                cols = st.columns(2)
                for i, (_, row) in enumerate(hist_hidden.iterrows()):
                    with cols[i % 2]:
                        _card(
                            "<div style='font-weight:700;color:#fff;font-size:.9em;'>"
                            + str(row["trackName"]) + "</div>"
                            "<div style='color:#666;font-size:.78em;margin-top:2px;'>"
                            + str(row["artistName"]) + "</div>"
                            "<div style='color:#444;font-size:.75em;margin-top:2px;'>"
                            + str(int(row["plays"])) + " plays · "
                            + str(round(row["hours"], 1)) + "h"
                            "</div>",
                            border=VIOLET_LIGHT
                        )

    # ── Tab 3: verdict ────────────────────────────────────────────────────────
    with tab3:
        st.markdown("### The Verdict — how accurate is Spotify's model of you?")

        if not spot_artists or hist_artists.empty:
            st.info("Not enough data to compute a verdict.")
        else:
            only_spot, only_hist, in_both = _artist_drift(spot_artists, hist_artists)
            total   = len(spot_artists)
            overlap = len(in_both)
            score   = int((overlap / total) * 100) if total > 0 else 0

            if score >= 70:
                verdict     = "Spotify knows you well."
                explanation = ("More than " + str(score) + "% of what Spotify thinks you love "
                               "matches your actual history. The algorithm has you figured out.")
                color       = GREEN
            elif score >= 45:
                verdict     = "Spotify has a partial picture."
                explanation = ("About " + str(score) + "% overlap. "
                               "There's a real gap between your recent activity "
                               "and your long-term listening identity.")
                color       = AMBER
            else:
                verdict     = "Spotify barely knows you."
                explanation = ("Only " + str(score) + "% of Spotify's top artists "
                               "match your actual history. "
                               "The algorithm is working on a very short memory.")
                color       = RED

            st.markdown(
                "<div style='background:#0f0f0f;border:2px solid " + color + "44;"
                "border-radius:16px;padding:28px;text-align:center;margin-bottom:20px;'>"
                "<div style='font-size:3em;font-weight:900;color:" + color + ";'>"
                + str(score) + "%</div>"
                "<div style='font-size:1.1em;font-weight:800;color:#fff;margin:8px 0;'>"
                + verdict + "</div>"
                "<div style='color:#888;font-size:.88em;line-height:1.6;max-width:480px;margin:0 auto;'>"
                + explanation + "</div>"
                "</div>",
                unsafe_allow_html=True
            )

            # breakdown
            col1, col2 = st.columns(2)
            with col1:
                _card(
                    "<div style='color:#ccc;font-size:.85em;line-height:1.7;'>"
                    "<b style='color:#fff;'>" + str(overlap) + " artists</b> "
                    "appear in both your Spotify top and your history top."
                    "</div>",
                    border=GREEN
                )
            with col2:
                _card(
                    "<div style='color:#ccc;font-size:.85em;line-height:1.7;'>"
                    "<b style='color:#fff;'>" + str(len(only_spot)) + " artists</b> "
                    "that Spotify thinks you love have little or no trace in your "
                    "full listening history."
                    "</div>",
                    border=AMBER
                )
