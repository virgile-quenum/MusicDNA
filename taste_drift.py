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
        "padding:14px;margin-bottom:8px;'>" + content + "</div>",
        unsafe_allow_html=True
    )

def _fetch_spotify_top(tr_key, limit=20):
    data = api_get("me/top/artists", {"time_range": tr_key, "limit": limit})
    if not data:
        return []
    return data.get("items", [])

def _history_top_artists(dfm, n=20):
    return (
        dfm.groupby("artistName")
        .agg(plays=("trackName", "count"), hours=("ms", lambda x: round(x.sum()/3600000, 1)))
        .sort_values("plays", ascending=False)
        .head(n)
        .reset_index()
    )

def _popularity_label(pop):
    if pop <= 0:  return None, None
    if pop < 30:  return "Underground", GREEN
    if pop < 55:  return "Emerging",    AMBER
    return "Mainstream", "#888"

def render(dfm):
    st.markdown(
        "<span style='color:" + VIOLET_LIGHT + ";font-size:.75em;font-weight:700;"
        "text-transform:uppercase;letter-spacing:.1em;'>Full DNA — File + Spotify</span>",
        unsafe_allow_html=True
    )
    st.title("Taste Drift")
    st.markdown(
        "*The you Spotify sees right now — vs. the you your history reveals.*"
    )

    if not is_authenticated():
        st.warning("Connect Spotify to unlock this analysis.")
        return
    if dfm is None or dfm.empty:
        st.warning("Upload your Extended History zip to enable this analysis.")
        return

    # ── Controls ──────────────────────────────────────────────────────────
    col_a, col_b, col_c = st.columns([3, 2, 1])
    with col_a:
        time_range = st.selectbox(
            "Spotify window",
            ["Last 6 months", "Last 4 weeks", "All time"],
            key="td_time_range"
        )
    with col_b:
        n_show = st.selectbox(
            "Artists to show",
            [10, 15, 20],
            index=0,
            key="td_n_show"
        )

    tr_map = {
        "Last 4 weeks":  "short_term",
        "Last 6 months": "medium_term",
        "All time":      "long_term",
    }
    tr_key = tr_map[time_range]

    with st.spinner("Loading Spotify data..."):
        spot_artists = _fetch_spotify_top(tr_key, limit=n_show)
    hist_artists = _history_top_artists(dfm, n_show)

    if not spot_artists:
        st.warning("Could not load Spotify top artists. Check your Spotify connection.")
        return

    spot_names = set(a["name"].lower() for a in spot_artists)
    hist_names = set(hist_artists["artistName"].str.lower())
    in_both    = spot_names & hist_names
    only_spot  = spot_names - hist_names
    only_hist  = hist_names - spot_names

    # ── Overlap score ─────────────────────────────────────────────────────
    overlap_pct = round(len(in_both) / max(n_show, 1) * 100)
    if overlap_pct >= 70:
        verdict = "Spotify has you figured out."
        sub     = str(overlap_pct) + "% of what Spotify thinks you love matches your actual history."
        v_color = GREEN
    elif overlap_pct >= 40:
        verdict = "Spotify sees part of you."
        sub     = str(overlap_pct) + "% overlap. A real gap between recent listening and long-term identity."
        v_color = AMBER
    else:
        verdict = "Spotify is looking at a stranger."
        sub     = "Only " + str(overlap_pct) + "% overlap. Two almost completely different people."
        v_color = RED

    st.markdown(
        "<div style='background:#0f0f0f;border:2px solid " + v_color + "44;"
        "border-radius:16px;padding:24px;text-align:center;margin:16px 0;'>"
        "<div style='font-size:3em;font-weight:900;color:" + v_color + ";'>"
        + str(overlap_pct) + "% match</div>"
        "<div style='font-size:1em;font-weight:800;color:#fff;margin:6px 0;'>"
        + verdict + "</div>"
        "<div style='color:#aaa;font-size:.85em;line-height:1.6;max-width:480px;margin:0 auto;'>"
        + sub + "</div>"
        "</div>",
        unsafe_allow_html=True
    )

    c1, c2, c3 = st.columns(3)
    for col, val, lbl, color in [
        (c1, str(len(in_both)),   "In both lists",                      GREEN),
        (c2, str(len(only_spot)), "Spotify only — not in your history",  AMBER),
        (c3, str(len(only_hist)), "History only — Spotify forgot them",  VIOLET_LIGHT),
    ]:
        with col:
            st.markdown(
                "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
                "border-radius:10px;padding:14px;text-align:center;'>"
                "<div style='font-size:1.8em;font-weight:900;color:" + color + ";'>" + val + "</div>"
                "<div style='font-size:.72em;color:#888;margin-top:4px;'>" + lbl + "</div>"
                "</div>",
                unsafe_allow_html=True
            )

    st.markdown("---")

    # ── Two columns — Spotify vs History ─────────────────────────────────
    col1, col2 = st.columns(2)

    with col1:
        st.markdown(
            "<div style='text-align:center;margin-bottom:12px;'>"
            "<div style='color:" + GREEN + ";font-size:.75em;font-weight:700;"
            "text-transform:uppercase;letter-spacing:.1em;'>Spotify thinks you are</div>"
            "<div style='color:#888;font-size:.75em;margin-top:4px;'>" + time_range + "</div>"
            "</div>",
            unsafe_allow_html=True
        )
        for i, a in enumerate(spot_artists):
            name    = a["name"]
            pop     = a.get("popularity", 0)
            pl, pc  = _popularity_label(pop)
            matched = name.lower() in in_both
            border  = GREEN if matched else "#1e1e1e"
            badge   = (
                " <span style='color:" + GREEN + ";font-size:.68em;"
                "background:#1DB95422;padding:1px 6px;border-radius:6px;'>✓ history</span>"
                if matched else ""
            )
            pop_badge = (
                "<span style='color:" + (pc or "#888") + ";font-size:.7em;font-weight:700;"
                "background:" + (pc or "#888") + "22;padding:2px 6px;border-radius:6px;'>"
                + (pl or "") + "</span>"
                if pl else ""
            )
            _card(
                "<div style='display:flex;justify-content:space-between;align-items:center;'>"
                "<div>"
                "<span style='color:#555;font-size:.78em;margin-right:6px;'>" + str(i+1) + ".</span>"
                "<span style='color:#fff;font-weight:700;font-size:.88em;'>" + name + "</span>"
                + badge +
                "</div>"
                + pop_badge +
                "</div>",
                border=border
            )

    with col2:
        st.markdown(
            "<div style='text-align:center;margin-bottom:12px;'>"
            "<div style='color:" + VIOLET_LIGHT + ";font-size:.75em;font-weight:700;"
            "text-transform:uppercase;letter-spacing:.1em;'>Your history says you are</div>"
            "<div style='color:#888;font-size:.75em;margin-top:4px;'>All-time top " + str(n_show) + "</div>"
            "</div>",
            unsafe_allow_html=True
        )
        for i, row in hist_artists.iterrows():
            name    = row["artistName"]
            matched = name.lower() in in_both
            border  = GREEN if matched else "#1e1e1e"
            badge   = (
                " <span style='color:" + GREEN + ";font-size:.68em;"
                "background:#1DB95422;padding:1px 6px;border-radius:6px;'>✓ Spotify</span>"
                if matched else ""
            )
            _card(
                "<div style='display:flex;justify-content:space-between;align-items:center;'>"
                "<div>"
                "<span style='color:#555;font-size:.78em;margin-right:6px;'>" + str(i+1) + ".</span>"
                "<span style='color:#fff;font-weight:700;font-size:.88em;'>" + name + "</span>"
                + badge +
                "</div>"
                "<span style='color:#888;font-size:.75em;'>"
                + str(int(row["plays"])) + " plays</span>"
                "</div>",
                border=border
            )

    st.markdown("---")

    # ── What Spotify forgot ───────────────────────────────────────────────
    if only_hist:
        st.markdown(
            "<div style='color:#A78BFA;font-size:.75em;font-weight:700;"
            "text-transform:uppercase;letter-spacing:.1em;margin-bottom:12px;'>"
            "Your history loves them — Spotify forgot</div>",
            unsafe_allow_html=True
        )
        forgotten_hist = hist_artists[hist_artists["artistName"].str.lower().isin(only_hist)]
        cols = st.columns(2)
        for i, (_, row) in enumerate(forgotten_hist.iterrows()):
            with cols[i % 2]:
                _card(
                    "<div style='font-weight:700;color:#fff;'>"
                    + str(row["artistName"]) + "</div>"
                    "<div style='color:#888;font-size:.78em;margin-top:3px;'>"
                    + str(int(row["plays"])) + " plays in history — invisible to Spotify right now"
                    "</div>",
                    border=VIOLET_LIGHT
                )

    # ── What Spotify over-indexes ─────────────────────────────────────────
    if only_spot:
        st.markdown("---")
        st.markdown(
            "<div style='color:#f59e0b;font-size:.75em;font-weight:700;"
            "text-transform:uppercase;letter-spacing:.1em;margin-bottom:12px;'>"
            "Spotify thinks they define you — barely in your history</div>",
            unsafe_allow_html=True
        )
        cols = st.columns(2)
        spot_only_list = [a for a in spot_artists if a["name"].lower() in only_spot]
        for i, a in enumerate(spot_only_list):
            url  = a.get("external_urls", {}).get("spotify", "")
            link = (
                "<a href='" + url + "' target='_blank' "
                "style='color:" + VIOLET_LIGHT + ";font-size:.75em;'>Open ↗</a>"
                if url else ""
            )
            with cols[i % 2]:
                _card(
                    "<div style='display:flex;justify-content:space-between;'>"
                    "<div style='font-weight:700;color:#fff;'>" + a["name"] + "</div>"
                    + link +
                    "</div>"
                    "<div style='color:#888;font-size:.78em;margin-top:3px;'>"
                    "In your Spotify top — not in your 12-year history"
                    "</div>",
                    border=AMBER
                )
