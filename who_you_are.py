"""
who_you_are.py — Behavioral passport module.
Combines score dimensions, Last.fm data, Witness signals,
and Claude API narrative into a unified profile.
"""

import streamlit as st
import pandas as pd
import json
import os
import time
import requests
from collections import defaultdict

VIOLET       = "#7C3AED"
VIOLET_LIGHT = "#A78BFA"
GREEN        = "#1DB954"
AMBER        = "#f59e0b"
RED          = "#f87171"
BLUE         = "#60a5fa"

KIDS_KW = [
    'bébé','baby','lullaby','titounis','mancebo','bernardo','celesti',
    'mclaughlin','moons','kiboomers','teddy','wonderland','comptines',
    'petit ours','ainsi font','percussioney','batukem','tukada',
    'música para bebés','alain royer','miracle tones',
]
def _is_kids(n): return any(k in n.lower() for k in KIDS_KW)

# ── Trait computation ─────────────────────────────────────────────────────────

def _compute_traits(dfm, dfd=None):
    """
    Compute 5 behavioral traits. Returns dict with scores 0-100 and raw stats.
    """
    df_c = dfm[~dfm['artistName'].apply(_is_kids)]
    yr_min = int(df_c['year'].min())
    yr_max = int(df_c['year'].max())
    n_years = max(yr_max - yr_min + 1, 1)
    my_h = df_c['ms'].sum() / 3600000

    # ── 1. Depth vs Surface ───────────────────────────────────────────────
    # plays_per_track on top 20 artists — lower = deeper exploration
    artist_detail = df_c.groupby('artistName').agg(
        _hours        =('ms', lambda x: x.sum()/3600000),
        _total_plays  =('trackName', 'count'),
        _unique_tracks=('trackName', 'nunique'),
    )
    top20 = artist_detail.nlargest(20, '_hours')
    top20['_ppt'] = top20['_total_plays'] / top20['_unique_tracks']
    avg_ppt           = top20['_ppt'].mean()
    avg_unique_tracks = top20['_unique_tracks'].mean()

    # Score: high unique tracks + low plays/track = deep
    exploration_s = min(avg_unique_tracks / 40, 1.0)
    loop_penalty  = max(0, (avg_ppt - 10) / 40)
    depth_raw     = exploration_s - loop_penalty
    depth_score   = round(max(min(depth_raw, 1.0), 0.0) * 100)

    # ── 2. Exploration vs Loyalty ─────────────────────────────────────────
    new_per_year = df_c.groupby('year')['artistName'].apply(
        lambda x: x[~x.isin(df_c[df_c['year'] < x.name]['artistName'])].nunique()
        if x.name > yr_min else x.nunique()
    ).mean()
    art_per_100h = (df_c['artistName'].nunique() / my_h * 100) if my_h > 0 else 0

    # benchmark: 380 new/year = 100%, 120 art/100h = 100%
    exploration_score = round(min(
        (new_per_year / 380 * 0.6 + art_per_100h / 120 * 0.4), 1.0
    ) * 100)

    # ── 3. Intentionality ────────────────────────────────────────────────
    skip_rate   = dfm['skipped'].mean() * 100 if 'skipped' in dfm.columns else 20
    shuffle_pct = dfm['shuffle'].mean() * 100 if 'shuffle' in dfm.columns else 30
    track_counts = dfm.groupby('trackName').size()
    repeat_rate  = (track_counts > 1).sum() / max(len(track_counts), 1) * 100

    intent_raw = (1 - skip_rate/100) * 0.45 + (1 - shuffle_pct/100) * 0.35 + repeat_rate/100 * 0.20
    intentionality_score = round(min(intent_raw / 0.75, 1.0) * 100)

    # ── 4. Emotional Volatility ───────────────────────────────────────────
    monthly = dfm.groupby('ym')['ms'].sum() / 3600000
    avg_m   = monthly.mean()
    std_m   = monthly.std()
    cv      = std_m / avg_m if avg_m > 0 else 0  # coefficient of variation

    # High obsessions = high volatility
    df_s = dfm.sort_values('ts').copy()
    df_s['gap'] = df_s['ts'].diff().dt.total_seconds().fillna(0)
    df_s['sid'] = (df_s['gap'] > 1800).cumsum()
    sessions       = df_s.groupby('sid')['ms'].sum() / 3600000
    binge_sessions = int((sessions >= 2).sum())
    binge_rate     = binge_sessions / max(len(sessions), 1)

    volatility_raw   = cv * 0.6 + binge_rate * 0.4
    volatility_score = round(min(volatility_raw / 0.8, 1.0) * 100)

    # ── 5. Mainstream Alignment ───────────────────────────────────────────
    mainstream_score = 50  # default — overridden by Last.fm if available
    avg_listeners    = 0
    try:
        import lastfm
        if lastfm.is_available():
            result = lastfm.compute_mainstream_score(df_c, top_n=30)
            mainstream_score = result.get("mainstream_score", 50)
            avg_listeners    = result.get("avg_listeners", 0)
    except Exception:
        pass

    return {
        # Scores 0-100
        "depth_score":         depth_score,
        "exploration_score":   exploration_score,
        "intentionality_score":intentionality_score,
        "volatility_score":    volatility_score,
        "mainstream_score":    mainstream_score,
        # Raw stats for narrative
        "avg_ppt":             round(avg_ppt, 1),
        "avg_unique_tracks":   round(avg_unique_tracks, 1),
        "new_per_year":        int(new_per_year),
        "art_per_100h":        round(art_per_100h, 1),
        "skip_rate":           round(skip_rate, 1),
        "shuffle_pct":         round(shuffle_pct, 1),
        "binge_sessions":      binge_sessions,
        "cv":                  round(cv, 2),
        "avg_listeners":       avg_listeners,
        "n_years":             n_years,
        "yr_min":              yr_min,
        "yr_max":              yr_max,
    }

def _percentile_label(score):
    """Convert 0-100 score to percentile label."""
    if score >= 92: return "Top 5%",    GREEN
    if score >= 80: return "Top 20%",   VIOLET_LIGHT
    if score >= 55: return "Above avg", VIOLET_LIGHT
    if score >= 40: return "Average",   "#888"
    return "Below avg", AMBER

# ── Key moments from Witness signals ─────────────────────────────────────────

def _get_key_moments(dfm, dfd=None):
    """Extract 3-4 key moments from behavioral signals."""
    moments = []
    df_c = dfm[~dfm['artistName'].apply(_is_kids)]

    # Peak year
    yearly = dfm.groupby('year')['ms'].sum() / 3600000
    peak_yr = int(yearly.idxmax())
    peak_h  = round(yearly.max())
    moments.append({
        "year":  peak_yr,
        "icon":  "📈",
        "color": VIOLET_LIGHT,
        "text":  str(peak_yr) + " was your peak year — " + str(peak_h) + "h of music.",
    })

    # Biggest obsession
    track_counts = df_c.groupby(['trackName','artistName']).size().reset_index(name='plays')
    if not track_counts.empty:
        top_obs = track_counts.loc[track_counts['plays'].idxmax()]
        if top_obs['plays'] >= 20:
            moments.append({
                "year":  None,
                "icon":  "🔁",
                "color": RED,
                "text":  '"' + str(top_obs['trackName']) + '" — ' +
                         str(int(top_obs['plays'])) + ' plays. ' +
                         "That is not listening. That is something else.",
            })

    # Parenthood signal
    if dfd is not None and not dfd.empty and 'ym' in dfd.columns:
        kids_m = dfd.groupby('ym')['ms'].sum() / 3600000
        kids_m = kids_m[kids_m > 1]
        if not kids_m.empty:
            first = kids_m.index.min()
            yr    = int(first[:4])
            moments.append({
                "year":  yr,
                "icon":  "👶",
                "color": "#f472b6",
                "text":  str(yr) + " — children's content appeared. " +
                         "Your listening split in two. The data saw it before you announced it.",
            })

    # Silence period
    monthly = df_c.groupby('ym')['ms'].sum() / 3600000
    avg_m   = monthly.mean()
    min_yr  = int(df_c.groupby('year')['ms'].sum().idxmin())
    min_h   = round(df_c.groupby('year')['ms'].sum().min() / 3600000)
    if min_h < avg_m * 8:
        moments.append({
            "year":  min_yr,
            "icon":  "🔇",
            "color": "#555",
            "text":  str(min_yr) + " — your quietest year. " + str(min_h) +
                     "h total. Something else was louder.",
        })

    return moments[:4]

# ── Genres summary ────────────────────────────────────────────────────────────

def _get_genre_summary():
    """Get top genres from session cache if available."""
    cache_key = "genre_inline_data"
    if cache_key not in st.session_state:
        return None
    data        = st.session_state[cache_key]
    genre_hours = data.get("genre_hours", {})
    total_h     = sum(genre_hours.values())
    if total_h == 0:
        return None
    sorted_g = sorted(genre_hours.items(), key=lambda x: -x[1])
    return [(g, round(h/total_h*100)) for g, h in sorted_g if h/total_h > 0.03][:5]

# ── Claude API narrative ──────────────────────────────────────────────────────

def _generate_narrative(traits, score_data, moments, genres):
    """
    Call Claude API to generate a personalized behavioral narrative.
    Returns a string of 5-6 sentences.
    """
    # Build context for Claude
    top_artist  = score_data.get('top_artist', '—')
    top_artist_h = round(score_data.get('top_artist_h', 0))
    archetype   = score_data.get('archetype', {}).get('name', '—')

    genre_str = ""
    if genres:
        genre_str = ", ".join([g + " (" + str(p) + "%)" for g, p in genres[:3]])

    moments_str = " ".join([m["text"] for m in moments[:3]])

    prompt = f"""You are analyzing someone's music listening behavior across {traits['n_years']} years of Spotify data ({traits['yr_min']}–{traits['yr_max']}).

Here are their key behavioral stats:
- Top artist all-time: {top_artist} ({top_artist_h}h)
- Musical archetype: {archetype}
- Depth score: {traits['depth_score']}/100 (avg {traits['avg_ppt']} plays per track on top artists, {traits['avg_unique_tracks']} unique tracks per top artist)
- Exploration score: {traits['exploration_score']}/100 ({traits['new_per_year']} new artists/year, {traits['art_per_100h']} artists per 100h)
- Intentionality score: {traits['intentionality_score']}/100 (skip rate {traits['skip_rate']}%, shuffle {traits['shuffle_pct']}%)
- Emotional volatility: {traits['volatility_score']}/100 ({traits['binge_sessions']} binge sessions ≥2h, monthly variation coefficient {traits['cv']})
- Mainstream alignment: {traits['mainstream_score']}/100
- Dominant genres: {genre_str if genre_str else 'not detected yet'}
- Key life moments in data: {moments_str}

Write a behavioral portrait of this person in exactly 5 sentences. Rules:
1. Be direct and specific — use the actual numbers and artist names
2. Reveal something they probably didn't know about themselves
3. The tone is honest, slightly uncomfortable, never judgmental
4. Do not mention Spotify or music apps by name
5. Do not use "you" at the start of every sentence — vary the structure
6. Each sentence should reveal a different dimension of their personality
7. The last sentence should be about what the data cannot tell us

Return only the 5 sentences, nothing else."""

    try:
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers={"Content-Type": "application/json"},
            json={
                "model":      "claude-sonnet-4-20250514",
                "max_tokens": 400,
                "messages":   [{"role": "user", "content": prompt}],
            },
            timeout=30,
        )
        if response.status_code == 200:
            data = response.json()
            return data["content"][0]["text"].strip()
    except Exception:
        pass

    # Fallback — algo narrative
    lines = []
    lines.append(
        str(traits['n_years']) + " years of data. " +
        str(traits['new_per_year']) + " new artists per year on average. " +
        ("Wide and restless." if traits['exploration_score'] > 60 else "Focused and selective.")
    )
    lines.append(
        top_artist + " — " + str(top_artist_h) + "h. " +
        "That is not a favourite. That is a relationship."
    )
    if traits['volatility_score'] > 60:
        lines.append(
            str(traits['binge_sessions']) + " sessions over 2 hours. " +
            "The listening is not regular — it comes in waves. Something triggers it."
        )
    if traits['mainstream_score'] < 35:
        lines.append(
            "The artists you listen to have an average of " +
            f"{traits['avg_listeners']:,}" + " Last.fm listeners. " +
            "You are not listening to what most people listen to. That is a choice."
        )
    lines.append(
        "The data records what you played, when, and how many times. " +
        "It does not record why. That part belongs to you."
    )
    return " ".join(lines)

# ── Rendering ─────────────────────────────────────────────────────────────────

def render(dfm, dfd=None, lib=None, playlists=None):
    st.markdown(
        "<span style='color:#A78BFA;font-size:.75em;font-weight:700;"
        "text-transform:uppercase;letter-spacing:.1em;'>Behavioral Passport</span>",
        unsafe_allow_html=True
    )
    st.title("Who You Are")
    st.markdown(
        "<div style='color:#888;font-size:.88em;margin-bottom:24px;'>"
        "Not what you claim to listen to. Not what the algorithm thinks. "
        "What your data actually says about you."
        "</div>",
        unsafe_allow_html=True
    )

    if dfm is None or dfm.empty:
        st.warning("Upload your Extended History zip to enable this analysis.")
        return

    if dfd is None: dfd = pd.DataFrame()

    # ── Load score data ───────────────────────────────────────────────────
    import score as score_mod
    s = score_mod.compute_score(dfm, dfd, lib, playlists)
    if not s: return

    # ── Compute traits ────────────────────────────────────────────────────
    cache_key = "who_you_are_traits"
    if cache_key not in st.session_state:
        with st.spinner("Analysing your behavioral patterns..."):
            traits = _compute_traits(dfm, dfd)
            st.session_state[cache_key] = traits
    traits = st.session_state[cache_key]

    # ── Section 1 — Narrative ─────────────────────────────────────────────
    st.markdown(
        "<div style='color:#A78BFA;font-size:.72em;font-weight:700;"
        "text-transform:uppercase;letter-spacing:.1em;margin-bottom:12px;'>"
        "The Reading</div>",
        unsafe_allow_html=True
    )

    genres    = _get_genre_summary()
    moments   = _get_key_moments(dfm, dfd)
    narr_key  = "who_narrative"

    if narr_key not in st.session_state:
        with st.spinner("Generating your behavioral portrait..."):
            narrative = _generate_narrative(traits, s, moments, genres)
            st.session_state[narr_key] = narrative

    narrative = st.session_state[narr_key]

    # Split into sentences for visual treatment
    sentences = [s2.strip() for s2 in narrative.replace("...", "…").split(". ") if s2.strip()]
    narr_html = ""
    for i, sent in enumerate(sentences):
        if not sent.endswith((".", "!", "?", "…")):
            sent += "."
        opacity  = "1" if i == 0 else str(round(1 - i * 0.08, 2))
        narr_html += (
            "<div style='color:#ccc;font-size:.95em;line-height:1.9;"
            "margin-bottom:8px;opacity:" + opacity + ";'>"
            + sent + "</div>"
        )

    st.markdown(
        "<div style='background:linear-gradient(135deg,#06060f,#0a001a);"
        "border:1px solid #7C3AED33;border-radius:16px;padding:28px 32px;"
        "margin-bottom:24px;'>"
        + narr_html +
        "</div>",
        unsafe_allow_html=True
    )

    # ── Section 2 — 5 Behavioral traits ──────────────────────────────────
    st.markdown(
        "<div style='color:#A78BFA;font-size:.72em;font-weight:700;"
        "text-transform:uppercase;letter-spacing:.1em;margin-bottom:16px;'>"
        "Your 5 Behavioral Traits</div>",
        unsafe_allow_html=True
    )

    trait_defs = [
        {
            "name":    "Depth",
            "icon":    "🔬",
            "score":   traits["depth_score"],
            "detail":  str(traits["avg_unique_tracks"]) + " unique tracks · " +
                       str(traits["avg_ppt"]) + "x plays/track on top artists",
            "low":     "Surface consumer — you sample, rarely dive deep.",
            "high":    "Deep listener — you know catalogues, not just hits.",
        },
        {
            "name":    "Exploration",
            "icon":    "🌍",
            "score":   traits["exploration_score"],
            "detail":  str(traits["new_per_year"]) + " new artists/year · " +
                       str(traits["art_per_100h"]) + " per 100h",
            "low":     "Loyal — you return to what you know.",
            "high":    "Explorer — always looking for what's next.",
        },
        {
            "name":    "Intentionality",
            "icon":    "🎯",
            "score":   traits["intentionality_score"],
            "detail":  str(traits["skip_rate"]) + "% skip · " +
                       str(traits["shuffle_pct"]) + "% shuffle",
            "low":     "Passive — music as background, algorithm decides.",
            "high":    "Deliberate — every play is a choice.",
        },
        {
            "name":    "Emotional Volatility",
            "icon":    "🌊",
            "score":   traits["volatility_score"],
            "detail":  str(traits["binge_sessions"]) + " binge sessions · " +
                       "variation index " + str(traits["cv"]),
            "low":     "Stable — regular, consistent listening patterns.",
            "high":    "Volatile — intense bursts followed by silence.",
        },
        {
            "name":    "Mainstream Alignment",
            "icon":    "📡",
            "score":   traits["mainstream_score"],
            "detail":  ("avg " + f"{traits['avg_listeners']:,}" + " Last.fm listeners"
                        if traits["avg_listeners"] > 0 else "Last.fm not loaded yet"),
            "low":     "Underground — you listen to what most people never find.",
            "high":    "Mainstream — you move with the crowd.",
        },
    ]

    for trait in trait_defs:
        score      = trait["score"]
        pct_label, pct_color = _percentile_label(score)
        bar_w      = score
        bar_color  = GREEN if score >= 70 else VIOLET_LIGHT if score >= 45 else AMBER

        description = trait["high"] if score >= 55 else trait["low"]

        st.markdown(
            "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
            "border-radius:10px;padding:16px;margin-bottom:10px;'>"
            "<div style='display:flex;justify-content:space-between;"
            "align-items:center;margin-bottom:8px;'>"
            "<div>"
            "<span style='font-size:.88em;font-weight:800;color:#fff;'>"
            + trait["icon"] + " " + trait["name"] + "</span>"
            "<span style='color:#555;font-size:.75em;margin-left:10px;'>"
            + trait["detail"] + "</span>"
            "</div>"
            "<div style='display:flex;align-items:center;gap:10px;'>"
            "<span style='font-size:.72em;font-weight:700;color:" + pct_color + ";"
            "background:" + pct_color + "22;padding:2px 8px;border-radius:8px;'>"
            + pct_label + "</span>"
            "<span style='font-size:.88em;font-weight:900;color:" + bar_color + ";'>"
            + str(score) + "/100</span>"
            "</div>"
            "</div>"
            "<div style='background:#1a1a1a;border-radius:4px;height:6px;margin-bottom:8px;'>"
            "<div style='background:" + bar_color + ";width:" + str(bar_w) + "%;"
            "height:6px;border-radius:4px;'></div>"
            "</div>"
            "<div style='color:#555;font-size:.78em;font-style:italic;'>"
            + description + "</div>"
            "</div>",
            unsafe_allow_html=True
        )

    st.markdown("---")

    # ── Section 3 — Positioning vs the crowd ─────────────────────────────
    st.markdown(
        "<div style='color:#A78BFA;font-size:.72em;font-weight:700;"
        "text-transform:uppercase;letter-spacing:.1em;margin-bottom:16px;'>"
        "Where You Stand</div>",
        unsafe_allow_html=True
    )
    st.caption("Compared to the average Spotify user — based on published benchmarks.")

    benchmarks = [
        ("Unique artists lifetime",   s.get('unique_artists', 0), 500,
         str(s.get('unique_artists', 0)) + " vs avg 500"),
        ("New artists per year",       traits["new_per_year"],     80,
         str(traits["new_per_year"]) + " vs avg 80"),
        ("Skip rate",                  100 - traits["skip_rate"],  75,
         str(traits["skip_rate"]) + "% skip vs avg 25%"),
        ("Hours per year",             s.get('total_plays', 0) * 3.5 / 3600 / s.get('n_years', 1), 400,
         str(int(dfm['ms'].sum()/3600000/max(s.get('n_years',1),1))) + "h/year vs avg 400h"),
    ]

    cols = st.columns(2)
    for i, (label, user_val, bench_val, detail) in enumerate(benchmarks):
        ratio = user_val / bench_val if bench_val > 0 else 1
        if ratio >= 3:    pct_str, color = "Top 5%",    GREEN
        elif ratio >= 2:  pct_str, color = "Top 15%",   VIOLET_LIGHT
        elif ratio >= 1.2: pct_str, color = "Above avg", VIOLET_LIGHT
        elif ratio >= 0.8: pct_str, color = "Average",   "#888"
        else:              pct_str, color = "Below avg",  AMBER

        with cols[i % 2]:
            st.markdown(
                "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
                "border-radius:10px;padding:14px;margin-bottom:10px;'>"
                "<div style='display:flex;justify-content:space-between;"
                "align-items:center;margin-bottom:4px;'>"
                "<span style='font-size:.8em;color:#aaa;font-weight:600;'>"
                + label + "</span>"
                "<span style='color:" + color + ";font-size:.72em;font-weight:700;"
                "background:" + color + "22;padding:2px 8px;border-radius:8px;'>"
                + pct_str + "</span>"
                "</div>"
                "<div style='color:#555;font-size:.75em;'>" + detail + "</div>"
                "</div>",
                unsafe_allow_html=True
            )

    st.markdown("---")

    # ── Section 4 — Key moments ───────────────────────────────────────────
    st.markdown(
        "<div style='color:#A78BFA;font-size:.72em;font-weight:700;"
        "text-transform:uppercase;letter-spacing:.1em;margin-bottom:16px;'>"
        "Moments The Data Remembers</div>",
        unsafe_allow_html=True
    )

    for moment in moments:
        st.markdown(
            "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
            "border-left:3px solid " + moment["color"] + ";border-radius:8px;"
            "padding:12px 16px;margin-bottom:8px;display:flex;gap:12px;'>"
            "<span style='font-size:1.2em;'>" + moment["icon"] + "</span>"
            "<div style='color:#aaa;font-size:.85em;line-height:1.6;'>"
            + moment["text"] + "</div>"
            "</div>",
            unsafe_allow_html=True
        )

    st.markdown("---")

    # ── Section 5 — Genres ────────────────────────────────────────────────
    st.markdown(
        "<div style='color:#A78BFA;font-size:.72em;font-weight:700;"
        "text-transform:uppercase;letter-spacing:.1em;margin-bottom:12px;'>"
        "Your Sound</div>",
        unsafe_allow_html=True
    )

    if genres:
        GENRE_COLORS = {
            "Hip-Hop / Rap":      "#f87171",
            "R&B / Soul":         "#A78BFA",
            "Jazz / Folk":        "#60a5fa",
            "Reggae / Dancehall": "#1DB954",
            "Afro":               "#f59e0b",
            "Caribbean":          "#f472b6",
            "Brazilian":          "#34d399",
            "Pop":                "#888",
            "Electronic":         "#818cf8",
            "Rock / Indie":       "#fb923c",
            "Classical / World":  "#94a3b8",
            "Other":              "#444",
        }
        genre_html = "<div style='display:flex;flex-wrap:wrap;gap:8px;'>"
        for genre, pct in genres:
            color = GENRE_COLORS.get(genre, "#888")
            genre_html += (
                "<span style='color:" + color + ";font-size:.82em;font-weight:700;"
                "background:" + color + "22;padding:5px 14px;border-radius:20px;'>"
                + genre + " · " + str(pct) + "%</span>"
            )
        genre_html += "</div>"
        st.markdown(genre_html, unsafe_allow_html=True)
        st.markdown(
            "<div style='color:#444;font-size:.75em;margin-top:8px;'>"
            "Open Musical Horoscope → Your Genres tab for the full breakdown."
            "</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            "<div style='color:#555;font-size:.82em;'>"
            "Go to Musical Horoscope → Your Genres tab to load your genre profile first."
            "</div>",
            unsafe_allow_html=True
        )

    # ── Refresh ───────────────────────────────────────────────────────────
    st.markdown("---")
    col_a, col_b = st.columns([1, 3])
    with col_a:
        if st.button("Refresh analysis"):
            for k in [cache_key, narr_key]:
                if k in st.session_state:
                    del st.session_state[k]
            st.rerun()
