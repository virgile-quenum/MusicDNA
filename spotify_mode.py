import streamlit as st
import pandas as pd
from collections import Counter
from spotify_auth import api_get

VIOLET       = "#7C3AED"
VIOLET_LIGHT = "#A78BFA"
GREEN        = "#1DB954"
AMBER        = "#f59e0b"

# ── ui helpers ────────────────────────────────────────────────────────────────

def _card(content, border=VIOLET):
    st.markdown(
        "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
        "border-left:3px solid " + border + ";border-radius:8px;"
        "padding:14px;margin-bottom:10px;'>" + content + "</div>",
        unsafe_allow_html=True
    )

def _pill(label, color):
    return (
        "<span style='color:" + color + ";font-size:.72em;font-weight:700;"
        "background:" + color + "22;padding:2px 8px;border-radius:10px;"
        "margin-left:6px;'>" + label + "</span>"
    )

def _popularity_label(pop):
    if pop < 30:  return "Underground", GREEN
    if pop < 55:  return "Emerging",    AMBER
    return "Mainstream", "#888"

def _audio_bar(label, value, color=VIOLET_LIGHT):
    pct = int(value * 100)
    return (
        "<div style='margin-bottom:10px;'>"
        "<div style='display:flex;justify-content:space-between;margin-bottom:3px;'>"
        "<span style='font-size:.8em;color:#888;'>" + label + "</span>"
        "<span style='font-size:.8em;font-weight:700;color:" + color + ";'>"
        + str(pct) + "%</span></div>"
        "<div style='background:#1e1e1e;border-radius:4px;height:6px;'>"
        "<div style='background:" + color + ";width:" + str(pct) + "%;"
        "height:6px;border-radius:4px;'></div></div></div>"
    )

def _fetch_audio_features(track_ids):
    if not track_ids:
        return []
    data = api_get("audio-features", {"ids": ",".join(track_ids[:50])})
    return [f for f in (data.get("audio_features", []) if data else []) if f]

def _stat_card(val, lbl, color=VIOLET_LIGHT):
    return (
        "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
        "border-radius:10px;padding:14px;text-align:center;'>"
        "<div style='font-size:1.5em;font-weight:900;color:" + color + ";'>"
        + str(val) + "</div>"
        "<div style='font-size:.72em;color:#555;margin-top:4px;'>" + lbl + "</div>"
        "</div>"
    )

def _taste_summary(top_genres, avg_pop, avg_energy, avg_dance, avg_bpm):
    lines = []
    if avg_pop < 35:
        lines.append("You dig deep — most of what you listen to hasn't found a mainstream audience yet.")
    elif avg_pop < 60:
        lines.append("Your taste sits between the underground and the mainstream. Curious, not obscure.")
    else:
        lines.append("You lean mainstream — you know what you like and it's popular for a reason.")

    if avg_energy > 0.7:
        lines.append("High energy is your default. Chill playlists are probably not your thing.")
    elif avg_energy < 0.4:
        lines.append("You prefer low-intensity listening — focus, late-night, or introspective.")
    else:
        lines.append("Your energy level is balanced — you move between intensity and calm.")

    if avg_bpm:
        if avg_bpm > 125:
            lines.append("Your average BPM (" + str(int(avg_bpm)) + ") — you like music that moves.")
        elif avg_bpm < 90:
            lines.append("Your average BPM (" + str(int(avg_bpm)) + ") is slow. You're not in a hurry.")
        else:
            lines.append("Average BPM: " + str(int(avg_bpm)) + " — mid-tempo, versatile.")

    if top_genres:
        lines.append("Dominant genre signal: <b style='color:#fff;'>" + top_genres[0] + "</b>.")

    return lines

# ── sections ──────────────────────────────────────────────────────────────────

def _render_top_tracks(tr_key):
    with st.spinner("Loading..."):
        data = api_get("me/top/tracks", {"time_range": tr_key, "limit": 20})
    tracks = data.get("items", []) if data else []
    if not tracks:
        st.warning("No top tracks found.")
        return []

    track_ids = [t["id"] for t in tracks if t.get("id")]
    features  = _fetch_audio_features(track_ids)
    feat_map  = {f["id"]: f for f in features if f and "id" in f}

    cols = st.columns(2)
    for i, t in enumerate(tracks):
        feat    = feat_map.get(t["id"], {})
        artists = ", ".join(a["name"] for a in t.get("artists", []))
        pop     = t.get("popularity", 0)
        pl, pc  = _popularity_label(pop)
        bpm     = feat.get("tempo")
        energy  = feat.get("energy")
        url     = t.get("external_urls", {}).get("spotify", "")
        meta    = []
        if bpm:    meta.append(str(int(bpm)) + " BPM")
        if energy: meta.append("Energy " + str(int(energy * 100)) + "%")
        link = ("<a href='" + url + "' target='_blank' style='color:" +
                VIOLET_LIGHT + ";font-size:.75em;'>Open ↗</a>") if url else ""
        with cols[i % 2]:
            _card(
                "<div style='display:flex;justify-content:space-between;align-items:flex-start;'>"
                "<div style='flex:1;'>"
                "<div style='font-weight:800;color:#fff;font-size:.92em;'>"
                + str(i + 1) + ". " + t["name"] + _pill(pl, pc) + "</div>"
                "<div style='color:#666;font-size:.78em;margin-top:3px;'>" + artists + "</div>"
                + ("<div style='color:#444;font-size:.75em;margin-top:4px;'>"
                   + " · ".join(meta) + "</div>" if meta else "") +
                "</div><div style='margin-left:8px;'>" + link + "</div></div>"
            )
    return tracks


def _render_top_artists(tr_key):
    with st.spinner("Loading..."):
        data = api_get("me/top/artists", {"time_range": tr_key, "limit": 20})
    artists = data.get("items", []) if data else []
    if not artists:
        st.warning("No top artists found.")
        return []

    all_genres = []
    cols = st.columns(2)
    for i, a in enumerate(artists):
        pop    = a.get("popularity", 0)
        pl, pc = _popularity_label(pop)
        genres = a.get("genres", [])[:2]
        all_genres.extend(a.get("genres", []))
        url  = a.get("external_urls", {}).get("spotify", "")
        link = ("<a href='" + url + "' target='_blank' style='color:" +
                VIOLET_LIGHT + ";font-size:.75em;'>Open ↗</a>") if url else ""
        with cols[i % 2]:
            _card(
                "<div style='display:flex;justify-content:space-between;align-items:center;'>"
                "<div>"
                "<div style='font-weight:800;color:#fff;font-size:.92em;'>"
                + str(i + 1) + ". " + a["name"] + _pill(pl, pc) + "</div>"
                + ("<div style='color:#555;font-size:.75em;margin-top:3px;'>"
                   + " · ".join(genres) + "</div>" if genres else "") +
                "</div><div>" + link + "</div></div>"
            )
    return all_genres


def _render_recently_played():
    with st.spinner("Loading..."):
        data = api_get("me/player/recently-played", {"limit": 50})
    items = data.get("items", []) if data else []
    if not items:
        st.warning("No recently played tracks found.")
        return

    rows = []
    for item in items:
        t = item.get("track", {})
        rows.append({
            "track":     t.get("name", ""),
            "artist":    ", ".join(a["name"] for a in t.get("artists", [])),
            "played_at": item.get("played_at", "")[:16].replace("T", " "),
            "url":       t.get("external_urls", {}).get("spotify", ""),
        })
    df = pd.DataFrame(rows)

    c1, c2, c3 = st.columns(3)
    with c1: st.markdown(_stat_card(df["track"].nunique(), "unique tracks"), unsafe_allow_html=True)
    with c2: st.markdown(_stat_card(df["artist"].nunique(), "unique artists"), unsafe_allow_html=True)
    with c3:
        top = df["artist"].value_counts().index[0] if not df.empty else "—"
        st.markdown(_stat_card(top, "most played lately", AMBER), unsafe_allow_html=True)

    st.markdown("<div style='margin-top:16px;'></div>", unsafe_allow_html=True)
    cols = st.columns(2)
    for i, row in df.iterrows():
        link = ("<a href='" + row["url"] + "' target='_blank' style='color:" +
                VIOLET_LIGHT + ";font-size:.75em;'>Open ↗</a>") if row["url"] else ""
        with cols[i % 2]:
            _card(
                "<div style='display:flex;justify-content:space-between;align-items:center;'>"
                "<div>"
                "<div style='font-weight:700;color:#fff;font-size:.88em;'>" + row["track"] + "</div>"
                "<div style='color:#666;font-size:.76em;margin-top:2px;'>" + row["artist"] + "</div>"
                "<div style='color:#333;font-size:.72em;margin-top:2px;'>" + row["played_at"] + "</div>"
                "</div><div>" + link + "</div></div>",
                border="#333"
            )


def _render_audio_profile(tracks, all_genres, tr_key):
    if not tracks:
        st.info("No tracks available for audio analysis.")
        return

    track_ids = [t["id"] for t in tracks if t.get("id")]
    features  = _fetch_audio_features(track_ids)
    if not features:
        st.warning("Could not load audio features from Spotify.")
        return

    df  = pd.DataFrame(features)
    avg = df[["energy","danceability","valence","acousticness",
              "instrumentalness","speechiness","tempo"]].dropna().mean()

    bpm = avg.get("tempo")
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.markdown(_stat_card(str(int(bpm)) if bpm else "—", "avg BPM", VIOLET_LIGHT), unsafe_allow_html=True)
    with c2: st.markdown(_stat_card(str(int(avg.get("energy",0)*100))+"%", "energy", "#f87171"), unsafe_allow_html=True)
    with c3: st.markdown(_stat_card(str(int(avg.get("danceability",0)*100))+"%", "danceability", GREEN), unsafe_allow_html=True)
    with c4: st.markdown(_stat_card(str(int(avg.get("valence",0)*100))+"%", "positivity", AMBER), unsafe_allow_html=True)

    st.markdown("<div style='margin-top:20px;'></div>", unsafe_allow_html=True)

    bars = ""
    for label, key, color in [
        ("Energy",           "energy",           "#f87171"),
        ("Danceability",     "danceability",      GREEN),
        ("Positivity",       "valence",           AMBER),
        ("Acousticness",     "acousticness",      "#60a5fa"),
        ("Instrumentalness", "instrumentalness",  VIOLET_LIGHT),
        ("Speechiness",      "speechiness",       "#34d399"),
    ]:
        if key in avg:
            bars += _audio_bar(label, avg[key], color)

    st.markdown(
        "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
        "border-radius:12px;padding:20px;'>" + bars + "</div>",
        unsafe_allow_html=True
    )

    # taste summary
    pop_data = api_get("me/top/tracks", {"time_range": tr_key, "limit": 20})
    pops     = [t.get("popularity", 0) for t in (pop_data.get("items", []) if pop_data else [])]
    avg_pop  = sum(pops) / len(pops) if pops else 0
    top_genres = [g for g, _ in Counter(all_genres).most_common(5)]

    lines = _taste_summary(top_genres, avg_pop,
                           float(avg.get("energy", 0)),
                           float(avg.get("danceability", 0)),
                           float(bpm) if bpm else None)

    st.markdown(
        "<div style='color:#A78BFA;font-size:.75em;font-weight:700;"
        "text-transform:uppercase;letter-spacing:.1em;"
        "margin:24px 0 12px;'>What the data says about you</div>",
        unsafe_allow_html=True
    )
    for line in lines:
        _card("<div style='color:#ccc;font-size:.88em;line-height:1.6;'>" + line + "</div>")


# ── main ──────────────────────────────────────────────────────────────────────

def render():
    st.markdown(
        "<span style='color:" + VIOLET_LIGHT + ";font-size:.75em;font-weight:700;"
        "text-transform:uppercase;letter-spacing:.1em;'>Spotify Mode</span>",
        unsafe_allow_html=True
    )
    st.title("Your Music Right Now")
    st.caption("Spotify snapshot — connect your Extended History zip for the full 12-year analysis.")

    time_range = st.selectbox("Time window",
                              ["Last 4 weeks", "Last 6 months", "All time"],
                              key="sm_time_range")
    tr_map = {"Last 4 weeks": "short_term",
              "Last 6 months": "medium_term",
              "All time": "long_term"}
    tr_key = tr_map[time_range]

    tab1, tab2, tab3, tab4 = st.tabs(
        ["Top Tracks", "Top Artists", "Recently Played", "Audio Profile"]
    )

    # fetch once, share across tabs
    with tab1:
        st.markdown("### Top Tracks — " + time_range)
        top_tracks = _render_top_tracks(tr_key)

    with tab2:
        st.markdown("### Top Artists — " + time_range)
        all_genres = _render_top_artists(tr_key)

    with tab3:
        st.markdown("### Last 50 Plays")
        _render_recently_played()

    with tab4:
        st.markdown("### Audio Profile")
        st.caption("Built from the audio features of your top 20 tracks.")
        _render_audio_profile(
            top_tracks if top_tracks else [],
            all_genres if all_genres else [],
            tr_key
        )

    st.markdown("---")
    st.markdown(
        "<div style='background:#0f0f0f;border:1px solid " + VIOLET + "44;"
        "border-radius:12px;padding:16px;text-align:center;'>"
        "<div style='color:#555;font-size:.82em;'>This is your Spotify snapshot. "
        "For 12 years of history, skip rates, playlist autopsy and everything "
        "Wrapped never showed you —</div>"
        "<div style='color:" + VIOLET_LIGHT + ";font-weight:700;font-size:.88em;"
        "margin-top:6px;'>upload your Extended History zip in the sidebar.</div>"
        "</div>",
        unsafe_allow_html=True
    )
