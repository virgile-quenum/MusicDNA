import streamlit as st
import pandas as pd
from collections import Counter

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

def _pill(label, color):
    return (
        "<span style='color:" + color + ";font-size:.72em;font-weight:700;"
        "background:" + color + "22;padding:2px 8px;border-radius:10px;"
        "margin-left:6px;'>" + label + "</span>"
    )

def _section_title(text):
    st.markdown(
        "<div style='color:#A78BFA;font-size:.75em;font-weight:700;"
        "text-transform:uppercase;letter-spacing:.1em;margin:20px 0 12px;'>"
        + text + "</div>",
        unsafe_allow_html=True
    )

def _popularity_label(pop):
    if pop < 30: return "Underground", GREEN
    if pop < 55: return "Emerging",    AMBER
    return "Mainstream", "#888"

def _render_related(dfm):
    st.markdown("### Artists Similar to Your Top Artists")
    st.caption("Based on Spotify's artist graph — works without the deprecated recommendations endpoint.")

    try:
        from spotify_auth import is_authenticated, api_get
        authenticated = is_authenticated()
    except Exception:
        authenticated = False

    if not authenticated:
        st.warning("Connect Spotify to enable this feature.")
        return

    time_range = st.selectbox("Based on your top artists from",
                              ["Last 6 months", "Last 4 weeks", "All time"],
                              key="exp_related_tr")
    tr_map = {"Last 6 months": "medium_term", "Last 4 weeks": "short_term", "All time": "long_term"}

    with st.spinner("Loading related artists..."):
        top_data = api_get("me/top/artists", {"time_range": tr_map[time_range], "limit": 10})
        top_artists = top_data.get('items', []) if top_data else []

    if not top_artists:
        st.error("Could not load your top artists.")
        return

    known_ids = set(a['id'] for a in top_artists)
    if dfm is not None:
        regular = dfm.groupby('artistName')['trackName'].count()
        known_names = set(regular[regular >= 5].index.str.lower())
    else:
        known_names = set()

    related = {}
    for artist in top_artists[:5]:
        data = api_get("artists/" + artist['id'] + "/related-artists")
        if not data:
            continue
        for r in data.get('artists', [])[:6]:
            if r['id'] not in known_ids and r['name'].lower() not in known_names:
                if r['id'] not in related:
                    related[r['id']] = {
                        'name':       r['name'],
                        'popularity': r.get('popularity', 0),
                        'genres':     r.get('genres', [])[:2],
                        'url':        r.get('external_urls', {}).get('spotify', ''),
                        'via':        artist['name'],
                    }

    if not related:
        st.info("No new related artists found. Your taste is already very broad.")
        return

    st.markdown("**" + str(len(related)) + " artists you should know:**")
    st.markdown("---")
    cols = st.columns(2)
    for i, (rid, info) in enumerate(sorted(related.items(), key=lambda x: -x[1]['popularity'])):
        with cols[i % 2]:
            pl, pc = _popularity_label(info['popularity'])
            genres = " · ".join(info['genres']) if info['genres'] else ""
            link = ""
            if info['url']:
                link = "<a href='" + info['url'] + "' target='_blank' style='color:" + VIOLET_LIGHT + ";font-size:.75em;'>Open ↗</a>"
            _card(
                "<div style='display:flex;justify-content:space-between;align-items:flex-start;'>"
                "<div>"
                "<div style='font-weight:800;color:#fff;font-size:.92em;'>"
                + info['name'] + _pill(pl, pc) + "</div>"
                "<div style='color:#555;font-size:.78em;margin-top:3px;'>Because you listen to: "
                "<b style='color:#888;'>" + info['via'] + "</b></div>"
                + ("<div style='color:#444;font-size:.75em;margin-top:2px;'>" + genres + "</div>" if genres else "") +
                "</div><div style='margin-left:8px;'>" + link + "</div>"
                "</div>"
            )

def _render_hidden_gems(dfm):
    st.markdown("### Hidden Gems — Artists You Discovered But Never Committed To")
    st.caption("From your own listening history — no Spotify API needed.")

    if dfm is None or dfm.empty:
        st.warning("Upload your Extended History zip to enable this analysis.")
        return

    col1, col2 = st.columns(2)
    with col1:
        min_plays = st.slider("Max plays to count as uncommitted", 1, 20, 3, key="gem_min")
    with col2:
        top_n = st.slider("Number of gems to show", 10, 50, 20, key="gem_top")

    artist_plays = dfm.groupby('artistName').agg(
        plays=('trackName', 'count'),
        tracks=('trackName', 'nunique'),
        last_played=('ts', 'max')
    ).reset_index()

    gems = artist_plays[
        (artist_plays['plays'] >= 1) & (artist_plays['plays'] <= min_plays)
    ].sort_values('plays', ascending=False).head(top_n)

    if gems.empty:
        st.info("No hidden gems found with current filters.")
    else:
        st.markdown("**" + str(len(gems)) + " artists you discovered but never committed to:**")
        st.markdown("---")
        cols = st.columns(2)
        for i, (_, row) in enumerate(gems.iterrows()):
            last = row['last_played'].strftime('%b %Y') if pd.notna(row['last_played']) else ""
            with cols[i % 2]:
                _card(
                    "<div style='font-weight:700;color:#fff;font-size:.9em;margin-bottom:4px;'>"
                    + str(row['artistName']) + "</div>"
                    "<div style='color:#555;font-size:.78em;line-height:1.7;'>"
                    + str(int(row['plays'])) + " play" + ("s" if row['plays'] > 1 else "")
                    + " · " + str(int(row['tracks'])) + " track" + ("s" if row['tracks'] > 1 else "")
                    + (" · Last: " + last if last else "") + "</div>",
                    border=AMBER
                )

    st.markdown("---")
    st.markdown("### Artists You Skipped Most")
    if 'skipped' in dfm.columns:
        skip_stats = dfm.groupby('artistName').agg(
            plays=('trackName', 'count'), skips=('skipped', 'sum')
        ).reset_index()
        skip_stats = skip_stats[skip_stats['plays'] >= 3]
        skip_stats['skip_rate'] = skip_stats['skips'] / skip_stats['plays']
        skip_stats = skip_stats[
            (skip_stats['skip_rate'] > 0.5) & (skip_stats['plays'] < 20)
        ].sort_values('skip_rate', ascending=False).head(15)
        if not skip_stats.empty:
            cols = st.columns(2)
            for i, (_, row) in enumerate(skip_stats.iterrows()):
                with cols[i % 2]:
                    _card(
                        "<div style='font-weight:700;color:#fff;font-size:.9em;'>"
                        + str(row['artistName']) + "</div>"
                        "<div style='color:#888;font-size:.78em;margin-top:4px;'>"
                        + str(int(row['skip_rate'] * 100)) + "% skip rate · "
                        + str(int(row['plays'])) + " plays</div>",
                        border=RED
                    )
        else:
            st.info("No high-skip artists found.")

def _artist_drift(spotify_artists, history_df):
    spot_names = {a["name"].lower(): a for a in spotify_artists}
    hist_names = set(history_df["artistName"].str.lower())
    only_spot  = [a for name, a in spot_names.items() if name not in hist_names]
    only_hist  = history_df[~history_df["artistName"].str.lower().isin(spot_names)]
    in_both    = [a for name, a in spot_names.items() if name in hist_names]
    return only_spot, only_hist, in_both

def _track_drift(spotify_tracks, history_df):
    history_df = history_df.copy()
    history_df["_key"] = history_df["trackName"].str.lower() + "|" + history_df["artistName"].str.lower()
    spot_keys  = {t["name"].lower() + "|" + t["artists"][0]["name"].lower()
                  for t in spotify_tracks if t.get("artists")}
    hist_hidden   = history_df[~history_df["_key"].isin(spot_keys)].head(10)
    over_indexed  = []
    for t in spotify_tracks:
        if not t.get("artists"):
            continue
        matches = history_df[
            (history_df["trackName"].str.lower() == t["name"].lower()) &
            (history_df["artistName"].str.lower() == t["artists"][0]["name"].lower())
        ]
        plays = int(matches["plays"].sum()) if not matches.empty else 0
        if plays < 5:
            over_indexed.append({
                "name": t["name"], "artist": t["artists"][0]["name"],
                "plays": plays, "pop": t.get("popularity", 0),
                "url": t.get("external_urls", {}).get("spotify", ""),
            })
    return hist_hidden, over_indexed

def _render_taste_drift(dfm):
    st.markdown("### Taste Drift — Spotify's Model vs. Your History")
    st.caption("Where Spotify's algorithm agrees with your actual history — and where it doesn't.")

    try:
        from spotify_auth import is_authenticated, api_get
        authenticated = is_authenticated()
    except Exception:
        authenticated = False

    if not authenticated:
        st.warning("Connect Spotify to unlock this analysis.")
        return
    if dfm is None or dfm.empty:
        st.warning("Upload your Extended History zip to enable this analysis.")
        return

    time_range = st.selectbox("Spotify window",
                              ["Last 6 months", "Last 4 weeks", "All time"],
                              key="td_tr")
    tr_map = {"Last 4 weeks": "short_term", "Last 6 months": "medium_term", "All time": "long_term"}
    tr_key = tr_map[time_range]

    with st.spinner("Loading Spotify data..."):
        spot_data    = api_get("me/top/artists", {"time_range": tr_key, "limit": 20})
        spot_artists = spot_data.get("items", []) if spot_data else []
        trk_data     = api_get("me/top/tracks",  {"time_range": tr_key, "limit": 20})
        spot_tracks  = trk_data.get("items", []) if trk_data else []

    hist_artists = (dfm.groupby("artistName")
        .agg(plays=("trackName","count"), hours=("ms", lambda x: x.sum()/3600000))
        .sort_values("plays", ascending=False).head(200).reset_index())
    hist_tracks = (dfm.groupby(["artistName","trackName"])
        .agg(plays=("ms","count"), hours=("ms", lambda x: x.sum()/3600000))
        .sort_values("plays", ascending=False).head(200).reset_index())

    sub1, sub2, sub3 = st.tabs(["Artist Drift", "Track Drift", "The Verdict"])

    with sub1:
        if not spot_artists:
            st.warning("Could not load Spotify top artists.")
            return
        only_spot, only_hist, in_both = _artist_drift(spot_artists, hist_artists)
        c1, c2, c3 = st.columns(3)
        for col, val, lbl, color in [
            (c1, str(len(in_both)),   "In both lists",                  GREEN),
            (c2, str(len(only_spot)), "Spotify says yes, history no",   AMBER),
            (c3, str(len(only_hist)), "History says yes, Spotify forgot", VIOLET_LIGHT),
        ]:
            with col:
                st.markdown(
                    "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
                    "border-radius:10px;padding:14px;text-align:center;'>"
                    "<div style='font-size:1.8em;font-weight:900;color:" + color + ";'>" + val + "</div>"
                    "<div style='font-size:.72em;color:#555;margin-top:4px;'>" + lbl + "</div>"
                    "</div>", unsafe_allow_html=True
                )
        if only_spot:
            _section_title("Spotify over-indexes — recent plays, not in your top 200 historically")
            cols = st.columns(2)
            for i, a in enumerate(only_spot):
                genres = ", ".join(a.get("genres", [])[:2])
                url    = a.get("external_urls", {}).get("spotify", "")
                link   = ("<a href='" + url + "' target='_blank' style='color:" + VIOLET_LIGHT + ";font-size:.75em;'>Open ↗</a>") if url else ""
                with cols[i % 2]:
                    _card(
                        "<div style='display:flex;justify-content:space-between;'>"
                        "<div><div style='font-weight:700;color:#fff;'>" + a["name"] + "</div>"
                        + ("<div style='color:#555;font-size:.78em;margin-top:2px;'>" + genres + "</div>" if genres else "") +
                        "</div><div>" + link + "</div></div>", border=AMBER
                    )
        if not only_hist.empty:
            _section_title("Your history remembers — Spotify forgot these")
            cols = st.columns(2)
            for i, (_, row) in enumerate(only_hist.iterrows()):
                with cols[i % 2]:
                    _card(
                        "<div style='font-weight:700;color:#fff;'>" + str(row["artistName"]) + "</div>"
                        "<div style='color:#555;font-size:.78em;margin-top:3px;'>"
                        + str(int(row["plays"])) + " plays · " + str(round(row["hours"], 1)) + "h</div>",
                        border=VIOLET_LIGHT
                    )

    with sub2:
        if not spot_tracks:
            st.warning("Could not load Spotify top tracks.")
            return
        hist_hidden, over_indexed = _track_drift(spot_tracks, hist_tracks)
        if over_indexed:
            _section_title("Spotify top 20 — but barely in your history")
            cols = st.columns(2)
            for i, t in enumerate(over_indexed):
                url  = t.get("url", "")
                link = ("<a href='" + url + "' target='_blank' style='color:" + VIOLET_LIGHT + ";font-size:.75em;'>Open ↗</a>") if url else ""
                with cols[i % 2]:
                    _card(
                        "<div style='display:flex;justify-content:space-between;align-items:center;'>"
                        "<div><div style='font-weight:700;color:#fff;font-size:.9em;'>" + t["name"] + "</div>"
                        "<div style='color:#666;font-size:.78em;'>" + t["artist"] + "</div>"
                        "<div style='color:#444;font-size:.75em;'>" + str(t["plays"]) + " plays · pop " + str(t["pop"]) + "</div>"
                        "</div><div>" + link + "</div></div>", border=AMBER
                    )
        if not hist_hidden.empty:
            _section_title("Your most-played tracks — not in Spotify's top 20")
            cols = st.columns(2)
            for i, (_, row) in enumerate(hist_hidden.iterrows()):
                with cols[i % 2]:
                    _card(
                        "<div style='font-weight:700;color:#fff;font-size:.9em;'>" + str(row["trackName"]) + "</div>"
                        "<div style='color:#666;font-size:.78em;'>" + str(row["artistName"]) + "</div>"
                        "<div style='color:#444;font-size:.75em;'>" + str(int(row["plays"])) + " plays · " + str(round(row["hours"], 1)) + "h</div>",
                        border=VIOLET_LIGHT
                    )

    with sub3:
        if not spot_artists or hist_artists.empty:
            st.info("Not enough data.")
            return
        only_spot, only_hist, in_both = _artist_drift(spot_artists, hist_artists)
        total   = len(spot_artists)
        overlap = len(in_both)
        score   = int((overlap / total) * 100) if total > 0 else 0
        if score >= 70:
            verdict, explanation, color = "Spotify knows you well.", str(score) + "% match with your actual history.", GREEN
        elif score >= 45:
            verdict, explanation, color = "Spotify has a partial picture.", str(score) + "% overlap. Real gap between recent and long-term identity.", AMBER
        else:
            verdict, explanation, color = "Spotify barely knows you.", "Only " + str(score) + "% match. Very short memory.", RED
        st.markdown(
            "<div style='background:#0f0f0f;border:2px solid " + color + "44;"
            "border-radius:16px;padding:28px;text-align:center;'>"
            "<div style='font-size:3em;font-weight:900;color:" + color + ";'>" + str(score) + "%</div>"
            "<div style='font-size:1.1em;font-weight:800;color:#fff;margin:8px 0;'>" + verdict + "</div>"
            "<div style='color:#888;font-size:.88em;line-height:1.6;max-width:480px;margin:0 auto;'>" + explanation + "</div>"
            "</div>",
            unsafe_allow_html=True
        )

def render(dfm=None):
    st.markdown(
        "<span style='color:#A78BFA;font-size:.75em;font-weight:700;"
        "text-transform:uppercase;letter-spacing:.1em;'>Discovery + Drift</span>",
        unsafe_allow_html=True
    )
    st.title("Explore")
    st.caption("New artists to discover. Hidden gems in your history. Where Spotify's model disagrees with yours.")

    tab1, tab2, tab3 = st.tabs(["Related Artists", "Hidden Gems", "Taste Drift"])

    with tab1:
        _render_related(dfm)
    with tab2:
        _render_hidden_gems(dfm)
    with tab3:
        _render_taste_drift(dfm)
