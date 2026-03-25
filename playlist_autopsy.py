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
        "<div style='font-size:.72em;color:#888;margin-top:4px;'>" + lbl + "</div>"
        "</div>"
    )

def _pct_bars(pct_12m, pct_all):
    bar_12m = (
        "<div style='margin-top:8px;'>"
        "<div style='display:flex;justify-content:space-between;margin-bottom:2px;'>"
        "<span style='font-size:.72em;color:#aaa;'>Played last 12 months</span>"
        "<span style='font-size:.72em;font-weight:700;color:" + GREEN + ";'>" + str(pct_12m) + "% of tracks</span>"
        "</div>"
        "<div style='background:#1e1e1e;border-radius:3px;height:5px;'>"
        "<div style='background:" + GREEN + ";width:" + str(min(pct_12m, 100)) + "%;height:5px;border-radius:3px;'></div>"
        "</div></div>"
    )
    bar_all = (
        "<div style='margin-top:6px;'>"
        "<div style='display:flex;justify-content:space-between;margin-bottom:2px;'>"
        "<span style='font-size:.72em;color:#888;'>Played all-time</span>"
        "<span style='font-size:.72em;color:#aaa;'>" + str(pct_all) + "% of tracks</span>"
        "</div>"
        "<div style='background:#1a1a1a;border-radius:3px;height:3px;'>"
        "<div style='background:#555;width:" + str(min(pct_all, 100)) + "%;height:3px;border-radius:3px;'></div>"
        "</div></div>"
    )
    return bar_12m + bar_all

def _status_label(status):
    labels = {
        "Active":  ("In rotation", GREEN),
        "Dormant": ("On pause",    AMBER),
        "Archive": ("Forgotten",   "#888"),
        "Ghost":   ("Never used",  RED),
    }
    return labels.get(status, (status, "#888"))

def _jaccard(set_a, set_b):
    if not set_a or not set_b:
        return 0.0
    inter = len(set_a & set_b)
    union = len(set_a | set_b)
    return inter / union if union > 0 else 0.0

def _build_playlist_stats(playlists, dfm):
    played_all = set(dfm["trackName"].str.lower().str.strip())
    cutoff_12m = dfm["ts"].max() - pd.DateOffset(months=12)
    played_12m = set(dfm[dfm["ts"] >= cutoff_12m]["trackName"].str.lower().str.strip())
    last_played_map = (
        dfm.groupby(dfm["trackName"].str.lower().str.strip())["ts"].max().to_dict()
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
                "pct_12m": 0, "pct_all": 0, "last_played": None,
                "status": "Ghost", "artist_set": set(), "track_set": set()
            })
            continue
        track_names  = [t["track"] for t in tracks]
        artist_set   = set(t["artist"] for t in tracks if t["artist"])
        n            = len(track_names)
        played_12m_n = sum(1 for t in track_names if t in played_12m)
        played_all_n = sum(1 for t in track_names if t in played_all)
        pct_12m      = round(played_12m_n / n * 100)
        pct_all      = round(played_all_n / n * 100)
        last_dates   = [last_played_map[t] for t in track_names if t in last_played_map]
        last_played  = max(last_dates) if last_dates else None
        if n < 3 or played_all_n == 0:
            status = "Ghost"
        elif pct_all >= 40 and played_12m_n >= 1:
            status = "Active"
        elif played_all_n > 0 and played_12m_n == 0:
            status = "Dormant"
        elif pct_all < 20:
            status = "Archive"
        else:
            status = "Dormant"
        rows.append({
            "name": name, "total_tracks": n,
            "unique_artists": len(artist_set),
            "pct_12m": pct_12m, "pct_all": pct_all,
            "last_played": last_played, "status": status,
            "artist_set": artist_set, "track_set": set(track_names),
        })
    return pd.DataFrame(rows)


def render(dfm, playlists):
    st.title("📋 Playlist Autopsy")
    st.markdown("*Which playlists you actually use vs. ones you built and forgot.*")

    st.markdown(
        "<div style='background:#0f0f0f;border:1px solid #1e1e1e;border-radius:8px;"
        "padding:12px 16px;margin-bottom:16px;'>"
        "<div style='color:#aaa;font-size:.82em;line-height:1.8;'>"
        "<b style='color:#fff;'>How it's calculated:</b> "
        "For each playlist, we check what % of its tracks appear anywhere in your listening history. "
        "Spotify doesn't record which playlist triggered a play — so these % reflect "
        "whether you played the track, regardless of source. "
        "<b style='color:#A78BFA;'>Last 12 months</b> = recent activity. "
        "<b style='color:#888;'>All-time</b> = ever played since your first export."
        "</div></div>",
        unsafe_allow_html=True
    )

    if isinstance(playlists, dict):
        playlists = playlists.get("playlists", [])
    if not playlists:
        st.warning("No playlist data — upload your standard export zip.")
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

    c1, c2, c3, c4, c5 = st.columns(5)
    for col, val, lbl, color in [
        (c1, total,     "Total playlists", VIOLET_LIGHT),
        (c2, n_active,  "In rotation",     GREEN),
        (c3, n_dormant, "On pause",        AMBER),
        (c4, n_archive, "Forgotten",       "#888"),
        (c5, n_ghost,   "Never used",      RED),
    ]:
        with col:
            st.markdown(_stat(val, lbl, color), unsafe_allow_html=True)

    st.markdown("---")

    tab1, tab2, tab3, tab4 = st.tabs([
        "In rotation (" + str(n_active) + ")",
        "On pause & Forgotten (" + str(n_dormant + n_archive) + ")",
        "Identity Gap",
        "Merge Candidates",
    ])

    # ── Tab 1: Active ─────────────────────────────────────────────────────
    with tab1:
        st.markdown("### Playlists in rotation")
        st.caption("40%+ of tracks played all-time AND at least 1 play in the last 12 months.")
        active = df[df["status"] == "Active"].sort_values("pct_12m", ascending=False)
        if active.empty:
            st.info("No active playlists detected.")
        else:
            cols = st.columns(2)
            for i, (_, row) in enumerate(active.iterrows()):
                last = row["last_played"].strftime("%b %Y") if row["last_played"] else "unknown"
                with cols[i % 2]:
                    _card(
                        "<div style='font-weight:700;color:#fff;font-size:.92em;'>"
                        + _esc(row["name"]) + "</div>"
                        "<div style='color:#888;font-size:.76em;margin-top:3px;'>"
                        + str(int(row["total_tracks"])) + " tracks · "
                        + str(int(row["unique_artists"])) + " artists · last: " + last + "</div>"
                        + _pct_bars(row["pct_12m"], row["pct_all"]),
                        border=GREEN
                    )

    # ── Tab 2: Dormant + Archive ──────────────────────────────────────────
    with tab2:
        st.markdown("### Playlists on pause or forgotten")
        st.markdown(
            "<div style='font-size:.82em;line-height:1.8;margin-bottom:12px;'>"
            "<span style='color:#f59e0b;font-weight:700;'>On pause</span>"
            "<span style='color:#aaa;'> — used before, nothing played in the last 12 months.</span><br>"
            "<span style='color:#888;font-weight:700;'>Forgotten</span>"
            "<span style='color:#aaa;'> — built but barely used, less than 20% of tracks ever played.</span>"
            "</div>",
            unsafe_allow_html=True
        )
        dead = df[df["status"].isin(["Archive", "Dormant"])].copy()
        dead = dead.sort_values("pct_all")
        if dead.empty:
            st.success("Nothing on pause or forgotten.")
        else:
            cols = st.columns(2)
            for i, (_, row) in enumerate(dead.iterrows()):
                last  = row["last_played"].strftime("%b %Y") if row["last_played"] else "Never played"
                label, color = _status_label(row["status"])
                with cols[i % 2]:
                    _card(
                        "<div style='display:flex;justify-content:space-between;align-items:center;'>"
                        "<div style='font-weight:700;color:#ccc;font-size:.9em;'>"
                        + _esc(row["name"])
                        + " <span style='color:" + color + ";font-size:.7em;background:"
                        + color + "22;padding:1px 7px;border-radius:8px;'>"
                        + label + "</span></div>"
                        "<span style='color:#888;font-size:.76em;'>last: " + last + "</span>"
                        "</div>"
                        + _pct_bars(row["pct_12m"], row["pct_all"]),
                        border=color
                    )

        ghosts = df[df["status"] == "Ghost"].sort_values("total_tracks", ascending=False)
        if not ghosts.empty:
            st.markdown("---")
            st.markdown("### " + str(len(ghosts)) + " Never used — built, zero plays")
            cols = st.columns(2)
            for i, (_, row) in enumerate(ghosts.iterrows()):
                with cols[i % 2]:
                    _card(
                        "<div style='font-weight:700;color:#888;'>" + _esc(row["name"]) + "</div>"
                        "<div style='color:#555;font-size:.76em;margin-top:4px;'>"
                        + str(int(row["total_tracks"])) + " tracks · 0% played</div>",
                        border="#444"
                    )

    # ── Tab 3: Identity Gap ───────────────────────────────────────────────
    with tab3:
        st.markdown("### The gap between what you build and what you play")
        st.caption("Playlists sorted by lowest all-time play rate. Minimum 5 tracks.")
        gap = (
            df[(df["total_tracks"] >= 5) & (df["pct_all"] < 80)]
            .sort_values("pct_all").head(30)
        )
        if gap.empty:
            st.success("No significant gaps found.")
        else:
            fig = go.Figure(go.Bar(
                x=gap["pct_all"],
                y=gap["name"].apply(_esc),
                orientation="h",
                marker_color=[RED if p < 20 else AMBER if p < 40 else VIOLET for p in gap["pct_all"]],
                text=[str(p) + "% of tracks played (" + str(int(t)) + " total)"
                      for p, t in zip(gap["pct_all"], gap["total_tracks"])],
                textposition="outside",
            ))
            fig.update_layout(
                plot_bgcolor="#111", paper_bgcolor="#111", font_color="#aaa",
                yaxis=dict(autorange="reversed", tickfont=dict(size=11, color="#ccc")),
                xaxis=dict(gridcolor="#1a1a1a", title="% of tracks played all-time", range=[0, 130]),
                margin=dict(l=200, r=80, t=10, b=20),
                height=max(300, len(gap) * 30)
            )
            st.plotly_chart(fig, use_container_width=True)

    # ── Tab 4: Merge Candidates ───────────────────────────────────────────
    with tab4:
        st.markdown("### Playlists that overlap — merge candidates")
        st.caption("Pairs sharing 40%+ of their artists. In rotation or on pause only, minimum 3 tracks.")
        candidates = df[
            (df["status"].isin(["Active", "Dormant"])) & (df["total_tracks"] >= 3)
        ].sort_values("pct_all", ascending=False).head(50).reset_index(drop=True)

        if len(candidates) < 2:
            st.info("Not enough playlists to find merge candidates.")
        else:
            pairs = []
            for i in range(len(candidates)):
                for j in range(i + 1, len(candidates)):
                    ra  = candidates.iloc[i]
                    rb  = candidates.iloc[j]
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
                        "<div style='color:#888;font-size:.78em;margin-top:4px;'>"
                        + str(row["shared"]) + " shared artists · "
                        + str(row["ta"]) + " + " + str(row["tb"]) + " tracks</div>"
                        "</div>"
                        "<span style='color:" + sc + ";font-size:1.1em;font-weight:900;"
                        "background:" + sc + "22;padding:4px 12px;border-radius:10px;'>"
                        + str(row["sim"]) + "% overlap</span>"
                        "</div>",
                        border=sc
                    )
