import streamlit as st
import pandas as pd
import plotly.graph_objects as go

VIOLET       = "#7C3AED"
VIOLET_LIGHT = "#A78BFA"
GREEN        = "#1DB954"
AMBER        = "#f59e0b"
RED          = "#f87171"

def _esc(s):
    return str(s).replace("'", "&#39;").replace('"', "&quot;")

def _card(content, border=VIOLET):
    st.markdown(
        "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
        "border-left:3px solid " + border + ";border-radius:8px;"
        "padding:14px;margin-bottom:10px;'>" + content + "</div>",
        unsafe_allow_html=True
    )

def _stat(val, lbl, color=VIOLET_LIGHT):
    return (
        "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
        "border-radius:10px;padding:14px;text-align:center;'>"
        "<div style='font-size:1.6em;font-weight:900;color:" + color + ";'>" + str(val) + "</div>"
        "<div style='font-size:.72em;color:#555;margin-top:4px;'>" + lbl + "</div>"
        "</div>"
    )

def _jaccard(set_a, set_b):
    if not set_a or not set_b:
        return 0.0
    inter = len(set_a & set_b)
    union = len(set_a | set_b)
    return inter / union if union > 0 else 0.0

def _build_playlist_stats(playlists, dfm):
    played_set    = set(dfm["trackName"].str.lower().str.strip())
    cutoff_12m    = dfm["ts"].max() - pd.DateOffset(months=12)
    cutoff_24m    = dfm["ts"].max() - pd.DateOffset(months=24)
    recent_played = set(dfm[dfm["ts"] >= cutoff_12m]["trackName"].str.lower().str.strip())
    last_played_map = (
        dfm.groupby(dfm["trackName"].str.lower().str.strip())["ts"].max().to_dict()
    )
    plays_map = (
        dfm.groupby(dfm["trackName"].str.lower().str.strip())["ms"].count().to_dict()
    )
    rows = []
    for pl in playlists:
        name  = pl.get("name", "Unnamed")
        items = pl.get("items", [])
        tracks = []
        for item in items:
            t  = item.get("track", {})
            tn = t.get("trackName", "") or t.get("name", "")
            an = t.get("artistName", "") or t.get("artist", "")
            if tn:
                tracks.append({"track": tn.lower().strip(), "artist": an.lower().strip()})
        if not tracks:
            rows.append({
                "name": name, "total_tracks": 0, "unique_artists": 0,
                "plays": 0, "plays_12m": 0, "never_played": 0,
                "last_played": None, "pct_never": 100.0,
                "status": "Ghost", "artist_set": set(), "track_set": set()
            })
            continue
        track_names  = [t["track"] for t in tracks]
        artist_set   = set(t["artist"] for t in tracks if t["artist"])
        plays_total  = sum(plays_map.get(t, 0) for t in track_names)
        plays_12m    = sum(1 for t in track_names if t in recent_played)
        never_played = sum(1 for t in track_names if t not in played_set)
        pct_never    = round(never_played / len(track_names) * 100, 1)
        last_dates   = [last_played_map[t] for t in track_names if t in last_played_map]
        last_played  = max(last_dates) if last_dates else None
        if len(track_names) < 3 or plays_total == 0:
            status = "Ghost"
        elif last_played and last_played >= cutoff_12m and plays_12m >= 1:
            status = "Active"
        elif last_played and last_played < cutoff_24m:
            status = "Archive"
        elif last_played and last_played < cutoff_12m:
            status = "Dormant"
        else:
            status = "Active"
        rows.append({
            "name": name, "total_tracks": len(track_names),
            "unique_artists": len(artist_set), "plays": plays_total,
            "plays_12m": plays_12m, "never_played": never_played,
            "last_played": last_played, "pct_never": pct_never,
            "status": status, "artist_set": artist_set, "track_set": set(track_names),
        })
    return pd.DataFrame(rows)


def render(dfm, playlists):
    st.title("Playlist Autopsy")
    st.markdown("*Which playlists you actually use vs. archives you built and forgot.*")
    if isinstance(playlists, dict):
        playlists = playlists.get("playlists", [])
    if not playlists:
        st.warning("No playlist data - upload your standard export zip.")
        return
    df = _build_playlist_stats(playlists, dfm)
    if df.empty:
        st.info("No playlist content found.")
        return

    n_active  = len(df[df["status"] == "Active"])
    n_dormant = len(df[df["status"] == "Dormant"])
    n_archive = len(df[df["status"] == "Archive"])
    n_ghost   = len(df[df["status"] == "Ghost"])
    total     = len(df)
    avg_util  = round((1 - df["pct_never"].mean() / 100) * 100, 1)

    c1, c2, c3, c4, c5 = st.columns(5)
    for col, val, lbl, color in [
        (c1, total,     "Total playlists",      VIOLET_LIGHT),
        (c2, n_active,  "Active (12 months)",   GREEN),
        (c3, n_dormant, "Dormant (1-2 years)",  AMBER),
        (c4, n_archive, "Archive (2+ years)",   "#555"),
        (c5, n_ghost,   "Ghost (never played)", RED),
    ]:
        with col:
            st.markdown(_stat(val, lbl, color), unsafe_allow_html=True)

    st.markdown(
        "<div style='text-align:center;color:#555;font-size:.8em;margin:12px 0;'>"
        "Average utilisation: <b style='color:#ccc;'>" + str(avg_util) + "%</b>"
        " of added tracks played at least once.</div>",
        unsafe_allow_html=True
    )
    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs([
        "Active (" + str(n_active) + ")",
        "Archives and Dormant (" + str(n_archive + n_dormant) + ")",
        "Identity Gap",
        "Merge Candidates",
    ])

    with tab1:
        st.markdown("### Playlists used in the last 12 months")
        active = df[df["status"] == "Active"].sort_values("plays_12m", ascending=False)
        if active.empty:
            st.info("No active playlists detected.")
        else:
            cols = st.columns(2)
            for i, (_, row) in enumerate(active.iterrows()):
                last = row["last_played"].strftime("%b %Y") if row["last_played"] else "unknown"
                alert = ""
                if row["pct_never"] > 30:
                    alert = (
                        "<div style='color:#f87171;font-size:.75em;margin-top:4px;'>"
                        + str(int(row["never_played"])) + " tracks never played ("
                        + str(row["pct_never"]) + "%)</div>"
                    )
                with cols[i % 2]:
                    _card(
                        "<div style='font-weight:700;color:#fff;font-size:.92em;'>"
                        + _esc(row["name"]) + "</div>"
                        "<div style='margin-top:6px;font-size:.78em;color:#555;'>"
                        + str(int(row["total_tracks"])) + " tracks"
                        " | <span style='color:" + GREEN + ";font-weight:700;'>"
                        + str(int(row["plays_12m"])) + " plays (12m)</span>"
                        " | last: " + last + "</div>" + alert,
                        border=GREEN
                    )

    with tab2:
        st.markdown("### Playlists you built and stopped using")
        dead = df[df["status"].isin(["Archive", "Dormant"])].copy()
        dead["_sort"] = dead["last_played"].fillna(pd.Timestamp("2000-01-01"))
        dead = dead.sort_values("_sort")
        if dead.empty:
            st.success("No dormant or archive playlists found.")
        else:
            cols = st.columns(2)
            for i, (_, row) in enumerate(dead.iterrows()):
                last  = row["last_played"].strftime("%b %Y") if row["last_played"] else "Never played"
                color = "#555" if row["status"] == "Archive" else AMBER
                label = "Archive" if row["status"] == "Archive" else "Dormant"
                with cols[i % 2]:
                    _card(
                        "<div style='font-weight:700;color:#666;font-size:.9em;'>"
                        + _esc(row["name"])
                        + " <span style='color:" + color + ";font-size:.72em;background:"
                        + color + "22;padding:2px 8px;border-radius:10px;'>"
                        + label + "</span></div>"
                        "<div style='color:#444;font-size:.76em;margin-top:6px;'>"
                        + str(int(row["total_tracks"])) + " tracks | last: " + last + "</div>",
                        border=color
                    )
        ghosts = df[df["status"] == "Ghost"].sort_values("total_tracks", ascending=False)
        if not ghosts.empty:
            st.markdown("---")
            st.markdown("### " + str(len(ghosts)) + " Ghost Playlists - built, never played")
            cols = st.columns(2)
            for i, (_, row) in enumerate(ghosts.iterrows()):
                with cols[i % 2]:
                    _card(
                        "<div style='font-weight:700;color:#444;'>" + _esc(row["name"]) + "</div>"
                        "<div style='color:#333;font-size:.76em;margin-top:4px;'>"
                        + str(int(row["total_tracks"])) + " tracks | 0 plays</div>",
                        border="#333"
                    )

    with tab3:
        st.markdown("### The gap between what you build and what you play")
        st.caption("Minimum 5 tracks. Sorted by % unplayed.")
        gap = (
            df[(df["total_tracks"] >= 5) & (df["pct_never"] > 0)]
            .sort_values("pct_never", ascending=False).head(30)
        )
        if gap.empty:
            st.success("No significant gaps found.")
        else:
            fig = go.Figure(go.Bar(
                x=gap["pct_never"],
                y=gap["name"].apply(_esc),
                orientation="h",
                marker_color=[RED if p >= 70 else AMBER if p >= 40 else VIOLET for p in gap["pct_never"]],
                text=[str(p) + "% (" + str(int(n)) + "/" + str(int(t)) + ")"
                      for p, n, t in zip(gap["pct_never"], gap["never_played"], gap["total_tracks"])],
                textposition="outside",
            ))
            fig.update_layout(
                plot_bgcolor="#111", paper_bgcolor="#111", font_color="#aaa",
                yaxis=dict(autorange="reversed", tickfont=dict(size=11, color="#ccc")),
                xaxis=dict(gridcolor="#1a1a1a", title="% tracks never played", range=[0, 120]),
                margin=dict(l=200, r=80, t=10, b=20),
                height=max(300, len(gap) * 30)
            )
            st.plotly_chart(fig, use_container_width=True)

    with tab4:
        st.markdown("### Playlists that overlap - merge candidates")
        st.caption("Pairs sharing 40%+ of their artists.")
        candidates = df[
            (df["status"].isin(["Active", "Dormant"])) & (df["total_tracks"] >= 3)
        ].reset_index(drop=True)
        if len(candidates) < 2:
            st.info("Not enough playlists to find merge candidates.")
        else:
            pairs = []
            for i in range(len(candidates)):
                for j in range(i + 1, len(candidates)):
                    ra = candidates.iloc[i]
                    rb = candidates.iloc[j]
                    sim = _jaccard(ra["artist_set"], rb["artist_set"])
                    if sim >= 0.4:
                        pairs.append({
                            "a": ra["name"], "b": rb["name"],
                            "sim": round(sim * 100),
                            "shared": len(ra["artist_set"] & rb["artist_set"]),
                            "ta": int(ra["total_tracks"]), "tb": int(rb["total_tracks"]),
                        })
            if not pairs:
                st.info("No strong overlaps found.")
            else:
                for row in sorted(pairs, key=lambda x: -x["sim"]):
                    sc = GREEN if row["sim"] >= 70 else AMBER
                    _card(
                        "<div style='display:flex;justify-content:space-between;align-items:center;'>"
                        "<div>"
                        "<div style='font-weight:700;color:#fff;'>"
                        + _esc(row["a"]) + " + " + _esc(row["b"]) + "</div>"
                        "<div style='color:#555;font-size:.78em;margin-top:4px;'>"
                        + str(row["shared"]) + " shared artists | "
                        + str(row["ta"]) + " + " + str(row["tb"]) + " tracks</div>"
                        "</div>"
                        "<span style='color:" + sc + ";font-size:1.1em;font-weight:900;"
                        "background:" + sc + "22;padding:4px 12px;border-radius:10px;'>"
                        + str(row["sim"]) + "%</span>"
                        "</div>",
                        border=sc
                    )
