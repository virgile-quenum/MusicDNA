import streamlit as st
import pandas as pd
from collections import Counter
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

def _stat(val, lbl, color=VIOLET_LIGHT):
    st.markdown(
        "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
        "border-radius:10px;padding:14px;text-align:center;'>"
        "<div style='font-size:1.5em;font-weight:900;color:" + color + ";'>"
        + str(val) + "</div>"
        "<div style='font-size:.72em;color:#555;margin-top:4px;'>" + lbl + "</div>"
        "</div>",
        unsafe_allow_html=True
    )

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

def _fetch_features_for_uris(track_uris):
    """Fetch audio features from a list of spotify:track:XXX URIs."""
    ids = [u.split(":")[-1] for u in track_uris if u and u.startswith("spotify:track:")]
    if not ids:
        return {}
    # batch in groups of 50
    feat_map = {}
    for i in range(0, min(len(ids), 200), 50):
        batch = ids[i:i+50]
        data  = api_get("audio-features", {"ids": ",".join(batch)})
        for f in (data.get("audio_features", []) if data else []):
            if f and "id" in f:
                feat_map[f["id"]] = f
    return feat_map

def _uri_to_id(uri):
    if uri and uri.startswith("spotify:track:"):
        return uri.split(":")[-1]
    return None

# ── analysis ──────────────────────────────────────────────────────────────────

def _yearly_audio_profile(dfm):
    """
    Computes per-year audio averages using top played track_uris from history.
    Returns a DataFrame with columns: year, energy, danceability, valence, tempo, n_tracks
    """
    if "track_uri" not in dfm.columns:
        return pd.DataFrame()

    # get top 30 most played tracks per year (to limit API calls)
    yearly = (
        dfm[dfm["track_uri"].str.startswith("spotify:track:", na=False)]
        .groupby(["year", "track_uri"])
        .size()
        .reset_index(name="plays")
    )

    years       = sorted(yearly["year"].unique())
    all_uris    = yearly.groupby("year").apply(
        lambda x: x.nlargest(30, "plays")["track_uri"].tolist()
    )
    unique_uris = list({u for uris in all_uris for u in uris})

    if not unique_uris:
        return pd.DataFrame()

    with st.spinner("Fetching audio features for your history (" + str(len(unique_uris)) + " tracks)..."):
        feat_map = _fetch_features_for_uris(unique_uris)

    if not feat_map:
        return pd.DataFrame()

    rows = []
    for year, uris in all_uris.items():
        feats = [feat_map[_uri_to_id(u)] for u in uris
                 if _uri_to_id(u) in feat_map]
        if not feats:
            continue
        df_f = pd.DataFrame(feats)
        row  = {"year": year}
        for col in ["energy","danceability","valence","acousticness","tempo"]:
            if col in df_f.columns:
                row[col] = df_f[col].mean()
        row["n_tracks"] = len(feats)
        rows.append(row)

    return pd.DataFrame(rows).sort_values("year")


def _current_audio_profile():
    """Fetch current top 20 tracks + audio features from Spotify."""
    data   = api_get("me/top/tracks", {"time_range": "medium_term", "limit": 20})
    tracks = data.get("items", []) if data else []
    if not tracks:
        return None, []
    ids   = [t["id"] for t in tracks if t.get("id")]
    feats = [f for f in (api_get("audio-features", {"ids": ",".join(ids[:50])}) or {}).get("audio_features", []) if f]
    if not feats:
        return None, tracks
    df    = pd.DataFrame(feats)
    avg   = df[["energy","danceability","valence","acousticness","tempo"]].dropna().mean()
    return avg, tracks


# ── render ────────────────────────────────────────────────────────────────────

def render(dfm):
    st.markdown(
        "<span style='color:" + VIOLET_LIGHT + ";font-size:.75em;font-weight:700;"
        "text-transform:uppercase;letter-spacing:.1em;'>Full DNA — File + Spotify</span>",
        unsafe_allow_html=True
    )
    st.title("Audio Profile")
    st.caption("How your musical energy, mood and tempo evolved over the years — vs. who you are now.")

    if not is_authenticated():
        st.warning("Connect Spotify to unlock this analysis (needed for audio features).")
        return

    if dfm is None or dfm.empty:
        st.warning("Upload your Extended History zip to enable this analysis.")
        return

    tab1, tab2 = st.tabs(["Evolution Over Time", "Now vs. History"])

    # ── Tab 1: evolution ──────────────────────────────────────────────────────
    with tab1:
        st.markdown("### How your sound changed year by year")
        st.caption("Built from your top 30 most-played tracks per year.")

        yearly_df = _yearly_audio_profile(dfm)

        if yearly_df.empty:
            st.info("Not enough track URI data to compute yearly audio profiles. "
                    "This requires an Extended History export.")
        else:
            try:
                import plotly.graph_objects as go

                fig = go.Figure()
                metrics = [
                    ("energy",       "Energy",       RED),
                    ("danceability", "Danceability",  GREEN),
                    ("valence",      "Positivity",    AMBER),
                    ("acousticness", "Acousticness",  "#60a5fa"),
                ]
                for key, label, color in metrics:
                    if key in yearly_df.columns:
                        fig.add_trace(go.Scatter(
                            x=yearly_df["year"],
                            y=(yearly_df[key] * 100).round(1),
                            mode="lines+markers",
                            name=label,
                            line=dict(color=color, width=2),
                            marker=dict(size=6),
                        ))

                fig.update_layout(
                    paper_bgcolor="#050505",
                    plot_bgcolor="#0f0f0f",
                    font=dict(color="#888", size=12),
                    legend=dict(bgcolor="#0f0f0f", bordercolor="#1e1e1e", borderwidth=1),
                    xaxis=dict(gridcolor="#1e1e1e", tickformat="d"),
                    yaxis=dict(gridcolor="#1e1e1e", title="Score (%)"),
                    margin=dict(l=0, r=0, t=10, b=0),
                    height=380,
                )
                st.plotly_chart(fig, use_container_width=True)

            except ImportError:
                # fallback table if plotly not available
                disp = yearly_df.copy()
                for col in ["energy","danceability","valence","acousticness"]:
                    if col in disp.columns:
                        disp[col] = (disp[col] * 100).round(1).astype(str) + "%"
                if "tempo" in disp.columns:
                    disp["tempo"] = disp["tempo"].round(0).astype(int).astype(str) + " BPM"
                st.dataframe(disp.set_index("year"), use_container_width=True)

            # highlight biggest change
            if len(yearly_df) >= 2 and "energy" in yearly_df.columns:
                first_e = yearly_df["energy"].iloc[0]
                last_e  = yearly_df["energy"].iloc[-1]
                delta   = last_e - first_e
                first_y = int(yearly_df["year"].iloc[0])
                last_y  = int(yearly_df["year"].iloc[-1])

                if abs(delta) > 0.08:
                    direction = "higher" if delta > 0 else "lower"
                    _card(
                        "<div style='color:#ccc;font-size:.88em;line-height:1.6;'>"
                        "Your energy level is <b style='color:#fff;'>"
                        + str(int(abs(delta) * 100)) + " points " + direction + "</b>"
                        " now than in " + str(first_y) + ". "
                        + ("You've been escalating." if delta > 0 else "You've mellowed out.")
                        + "</div>",
                        border=RED if delta > 0 else "#60a5fa"
                    )

            # BPM line
            if "tempo" in yearly_df.columns:
                st.markdown("### BPM Over Time")
                try:
                    import plotly.graph_objects as go
                    fig2 = go.Figure()
                    fig2.add_trace(go.Bar(
                        x=yearly_df["year"],
                        y=yearly_df["tempo"].round(0),
                        marker_color=VIOLET,
                        name="Avg BPM"
                    ))
                    fig2.update_layout(
                        paper_bgcolor="#050505",
                        plot_bgcolor="#0f0f0f",
                        font=dict(color="#888", size=12),
                        xaxis=dict(gridcolor="#1e1e1e", tickformat="d"),
                        yaxis=dict(gridcolor="#1e1e1e", title="BPM"),
                        margin=dict(l=0, r=0, t=10, b=0),
                        height=260,
                        showlegend=False
                    )
                    st.plotly_chart(fig2, use_container_width=True)
                except ImportError:
                    pass

    # ── Tab 2: now vs history ─────────────────────────────────────────────────
    with tab2:
        st.markdown("### Your current Spotify taste vs. your all-time history")
        st.caption("Left = your top tracks right now (6 months). Right = your all-time average from the full history.")

        current_avg, _ = _current_audio_profile()

        if current_avg is None:
            st.warning("Could not load current Spotify data.")
        elif yearly_df.empty:
            st.warning("Not enough history data for comparison.")
        else:
            # all-time average from history
            history_avg = yearly_df[["energy","danceability","valence","acousticness"]].mean()

            metrics = [
                ("energy",       "Energy",       RED),
                ("danceability", "Danceability",  GREEN),
                ("valence",      "Positivity",    AMBER),
                ("acousticness", "Acousticness",  "#60a5fa"),
            ]

            c_now, c_hist = st.columns(2)
            with c_now:
                st.markdown(
                    "<div style='color:#1DB954;font-size:.75em;font-weight:700;"
                    "text-transform:uppercase;letter-spacing:.08em;margin-bottom:12px;'>"
                    "Now (last 6 months)</div>",
                    unsafe_allow_html=True
                )
                now_bars = ""
                for _, key, color in metrics:
                    if key in current_avg:
                        now_bars += _audio_bar(key.capitalize(), float(current_avg[key]), color)
                st.markdown(
                    "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
                    "border-radius:12px;padding:16px;'>" + now_bars + "</div>",
                    unsafe_allow_html=True
                )

            with c_hist:
                st.markdown(
                    "<div style='color:" + VIOLET_LIGHT + ";font-size:.75em;font-weight:700;"
                    "text-transform:uppercase;letter-spacing:.08em;margin-bottom:12px;'>"
                    "All-time average</div>",
                    unsafe_allow_html=True
                )
                hist_bars = ""
                for _, key, color in metrics:
                    if key in history_avg:
                        hist_bars += _audio_bar(key.capitalize(), float(history_avg[key]), color)
                st.markdown(
                    "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
                    "border-radius:12px;padding:16px;'>" + hist_bars + "</div>",
                    unsafe_allow_html=True
                )

            # delta insights
            st.markdown(
                "<div style='color:#A78BFA;font-size:.75em;font-weight:700;"
                "text-transform:uppercase;letter-spacing:.1em;margin:20px 0 12px;'>"
                "What changed</div>",
                unsafe_allow_html=True
            )

            insights = []
            for label, key, color in metrics:
                if key in current_avg and key in history_avg:
                    delta = float(current_avg[key]) - float(history_avg[key])
                    if abs(delta) > 0.06:
                        direction = "up" if delta > 0 else "down"
                        pts       = str(int(abs(delta) * 100))
                        insights.append((label, direction, pts, color))

            if insights:
                for label, direction, pts, color in insights:
                    arrow = "↑" if direction == "up" else "↓"
                    change_desc = "higher" if direction == "up" else "lower"
                    _card(
                        "<span style='color:" + color + ";font-weight:800;font-size:.95em;'>"
                        + arrow + " " + label + "</span>"
                        "<span style='color:#888;font-size:.85em;margin-left:8px;'>"
                        + pts + " points " + change_desc + " than your all-time average"
                        "</span>",
                        border=color
                    )
            else:
                st.info("Your current listening profile is consistent with your all-time average. Stable taste.")
