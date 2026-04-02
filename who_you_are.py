"""
who_you_are.py — Behavioral passport module.
Combines score dimensions, archetype, Last.fm data, Witness signals,
and Claude API narrative into a unified profile.

Prefetch contract:
  session_state['score']         — set by app.py after file parse (via score.compute_score)
  session_state['who_traits']    — set by prefetch_traits() called from app.py
  session_state['who_narrative'] — set lazily on first render, cached after
"""

import os
import streamlit as st
import pandas as pd
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


# ── Trait computation (called once at parse time via prefetch_traits) ─────────

def prefetch_traits(dfm, dfd=None):
    """
    Called from app.py immediately after file parse.
    Stores result in st.session_state['who_traits'].
    No-op if already cached.
    """
    if 'who_traits' in st.session_state:
        return
    st.session_state['who_traits'] = _compute_traits(dfm, dfd)


def _compute_traits(dfm, dfd=None):
    """
    Compute 5 behavioral traits. Returns dict with scores 0-100 and raw stats.
    All heavy pandas work happens here — called once, result cached.
    """
    df_c = dfm[~dfm['artistName'].apply(_is_kids)]
    yr_min  = int(df_c['year'].min())
    yr_max  = int(df_c['year'].max())
    n_years = max(yr_max - yr_min + 1, 1)
    my_h    = df_c['ms'].sum() / 3_600_000

    # ── 1. Depth vs Surface ───────────────────────────────────────────────
    artist_agg = df_c.groupby('artistName').agg(
        _hours        =('ms', lambda x: x.sum() / 3_600_000),
        _total_plays  =('trackName', 'count'),
        _unique_tracks=('trackName', 'nunique'),
    )
    top20 = artist_agg.nlargest(20, '_hours').copy()
    top20['_ppt'] = top20['_total_plays'] / top20['_unique_tracks']
    avg_ppt           = top20['_ppt'].mean()
    avg_unique_tracks = top20['_unique_tracks'].mean()

    exploration_s = min(avg_unique_tracks / 40, 1.0)
    loop_penalty  = max(0, (avg_ppt - 10) / 40)
    depth_raw     = exploration_s - loop_penalty
    depth_score   = round(max(min(depth_raw, 1.0), 0.0) * 100)

    # ── 2. Exploration vs Loyalty — O(n) ─────────────────────────────────
    seen        = set()
    new_counts  = []
    for yr in sorted(df_c['year'].unique()):
        yr_artists = set(df_c.loc[df_c['year'] == yr, 'artistName'])
        new_counts.append(len(yr_artists - seen))
        seen |= yr_artists
    new_per_year  = sum(new_counts) / max(len(new_counts), 1)
    art_per_100h  = (df_c['artistName'].nunique() / my_h * 100) if my_h > 0 else 0
    exploration_score = round(min(
        (new_per_year / 380 * 0.6 + art_per_100h / 120 * 0.4), 1.0
    ) * 100)

    # ── 3. Intentionality ─────────────────────────────────────────────────
    skip_rate    = dfm['skipped'].mean() * 100 if 'skipped' in dfm.columns else 20
    shuffle_pct  = dfm['shuffle'].mean() * 100  if 'shuffle' in dfm.columns else 30
    track_counts = dfm.groupby('trackName').size()
    repeat_rate  = (track_counts > 1).sum() / max(len(track_counts), 1) * 100
    intent_raw   = ((1 - skip_rate / 100) * 0.45
                    + (1 - shuffle_pct / 100) * 0.35
                    + repeat_rate / 100 * 0.20)
    intentionality_score = round(min(intent_raw / 0.75, 1.0) * 100)

    # ── 4. Emotional Volatility — no .copy() ─────────────────────────────
    if 'ym' in dfm.columns:
        monthly = dfm.groupby('ym')['ms'].sum() / 3_600_000
        avg_m   = monthly.mean()
        std_m   = monthly.std()
        cv      = std_m / avg_m if avg_m > 0 else 0
    else:
        cv = 0

    df_sorted  = dfm.sort_values('ts')
    gaps_sec   = df_sorted['ts'].diff().dt.total_seconds().fillna(9999)
    sid        = (gaps_sec > 1800).cumsum()
    session_ms = df_sorted['ms'].groupby(sid).sum()
    binge_sessions = int((session_ms >= 7_200_000).sum())
    binge_rate     = binge_sessions / max(len(session_ms), 1)
    volatility_raw   = cv * 0.6 + binge_rate * 0.4
    volatility_score = round(min(volatility_raw / 0.8, 1.0) * 100)

    # ── 5. Mainstream Alignment (Last.fm, non-blocking) ───────────────────
    mainstream_score = 50
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
        "depth_score":          depth_score,
        "exploration_score":    exploration_score,
        "intentionality_score": intentionality_score,
        "volatility_score":     volatility_score,
        "mainstream_score":     mainstream_score,
        "avg_ppt":              round(avg_ppt, 1),
        "avg_unique_tracks":    round(avg_unique_tracks, 1),
        "new_per_year":         int(new_per_year),
        "art_per_100h":         round(art_per_100h, 1),
        "skip_rate":            round(skip_rate, 1),
        "shuffle_pct":          round(shuffle_pct, 1),
        "binge_sessions":       binge_sessions,
        "cv":                   round(cv, 2),
        "avg_listeners":        avg_listeners,
        "n_years":              n_years,
        "yr_min":               yr_min,
        "yr_max":               yr_max,
    }


def _percentile_label(score):
    if score >= 92: return "Top 5%",    GREEN
    if score >= 80: return "Top 20%",   VIOLET_LIGHT
    if score >= 55: return "Above avg", VIOLET_LIGHT
    if score >= 40: return "Average",   "#888"
    return "Below avg", AMBER


# ── Archetype block ───────────────────────────────────────────────────────────

def _render_archetype(arch, s):
    """
    Full archetype card — curse / gift / prediction.
    Replaces the compact data_line shown in the score card.
    """
    def _fmt(t):
        try:
            return t.format_map({k: (round(v, 1) if isinstance(v, float) else v)
                                 for k, v in s.items()})
        except KeyError:
            return t

    color_map = {
        "infiltrated_parent":  "#f472b6",
        "one_track_mind":      RED,
        "nostalgia_prisoner":  AMBER,
        "radio_head":          "#888",
        "playlist_mummy":      "#555",
        "spotify_sheep":       "#94a3b8",
        "fake_eclectic":       VIOLET_LIGHT,
        "algorithm_tourist":   BLUE,
        "underground_snob":    GREEN,
        "obsessive":           RED,
        "passive_loyalist":    "#555",
        "binge_escaper":       "#818cf8",
        "the_looper":          VIOLET_LIGHT,
        "deliberate_listener": GREEN,
    }
    color = color_map.get(arch.get("key", ""), VIOLET_LIGHT)

    rows = [
        ("The Curse",      arch.get("curse", ""),      "#f87171"),
        ("The Gift",       arch.get("gift", ""),       GREEN),
        ("The Prediction", arch.get("prediction", ""), VIOLET_LIGHT),
    ]

    inner = ""
    for label, text, lcolor in rows:
        inner += (
            "<div style='margin-bottom:14px;'>"
            "<div style='font-size:.65em;font-weight:800;color:" + lcolor + ";"
            "text-transform:uppercase;letter-spacing:.1em;margin-bottom:4px;'>"
            + label + "</div>"
            "<div style='color:#bbb;font-size:.88em;line-height:1.7;'>"
            + _fmt(text) + "</div>"
            "</div>"
        )

    st.markdown(
        "<div style='background:linear-gradient(135deg,#08080f,#0d001a);"
        "border:1px solid " + color + "44;border-radius:16px;"
        "padding:24px 28px;margin-bottom:24px;'>"
        "<div style='display:flex;align-items:center;gap:14px;margin-bottom:20px;'>"
        "<span style='font-size:2.2em;'>" + arch.get("emoji", "🎯") + "</span>"
        "<div>"
        "<div style='font-size:.65em;color:#555;text-transform:uppercase;"
        "letter-spacing:.1em;'>Your Archetype</div>"
        "<div style='font-size:1.15em;font-weight:900;color:" + color + ";'>"
        + arch.get("name", "") + "</div>"
        "<div style='color:#444;font-size:.72em;margin-top:2px;'>"
        + _fmt(arch.get("data_line", "")) + "</div>"
        "</div></div>"
        + inner +
        "</div>",
        unsafe_allow_html=True
    )


# ── Key moments ───────────────────────────────────────────────────────────────

def _get_key_moments(dfm, dfd=None):
    moments = []
    df_c = dfm[~dfm['artistName'].apply(_is_kids)]

    # Peak year
    yearly  = dfm.groupby('year')['ms'].sum() / 3_600_000
    peak_yr = int(yearly.idxmax())
    peak_h  = round(yearly.max())
    moments.append({
        "year": peak_yr, "icon": "📈", "color": VIOLET_LIGHT,
        "text": f"{peak_yr} was your peak year — {peak_h}h of music.",
    })

    # Biggest obsession
    track_counts = df_c.groupby(['trackName', 'artistName']).size().reset_index(name='plays')
    if not track_counts.empty:
        top_obs = track_counts.loc[track_counts['plays'].idxmax()]
        if top_obs['plays'] >= 20:
            moments.append({
                "year": None, "icon": "🔁", "color": RED,
                "text": (f'"{top_obs["trackName"]}" — {int(top_obs["plays"])} plays. '
                         "That is not listening. That is something else."),
            })

    # Parenthood signal
    if dfd is not None and not dfd.empty and 'ym' in dfd.columns:
        kids_m = dfd.groupby('ym')['ms'].sum() / 3_600_000
        kids_m = kids_m[kids_m > 1]
        if not kids_m.empty:
            yr = int(kids_m.index.min()[:4])
            moments.append({
                "year": yr, "icon": "👶", "color": "#f472b6",
                "text": (f"{yr} — children's content appeared. "
                         "Your listening split in two. The data saw it before you announced it."),
            })

    # Quietest year
    yearly_clean = df_c.groupby('year')['ms'].sum() / 3_600_000
    if len(yearly_clean) > 1:
        min_yr = int(yearly_clean.idxmin())
        min_h  = round(yearly_clean.min())
        avg_h  = yearly_clean.mean()
        if min_h < avg_h * 0.5:
            moments.append({
                "year": min_yr, "icon": "🔇", "color": "#555",
                "text": f"{min_yr} — your quietest year. {min_h}h total. Something else was louder.",
            })

    return moments[:4]


# ── Genre summary ─────────────────────────────────────────────────────────────

def _get_genre_summary():
    data = st.session_state.get("genre_inline_data")
    if not data:
        return None
    genre_hours = data.get("genre_hours", {})
    total_h     = sum(genre_hours.values())
    if total_h == 0:
        return None
    sorted_g = sorted(genre_hours.items(), key=lambda x: -x[1])
    return [(g, round(h / total_h * 100)) for g, h in sorted_g if h / total_h > 0.03][:5]


# ── Claude narrative ──────────────────────────────────────────────────────────

def _generate_narrative(traits, s):
    """
    Calls Claude API to produce a 5-sentence behavioral portrait.
    Falls back to rule-based text if API unavailable.
    Result is cached in session_state['who_narrative'].
    """
    if 'who_narrative' in st.session_state:
        return st.session_state['who_narrative']

    genres  = _get_genre_summary()
    moments = _get_key_moments_cached(s)

    top_artist   = s.get('top_artist', '—')
    top_artist_h = round(s.get('top_artist_h', 0))
    archetype    = s.get('archetype', {}).get('name', '—')
    genre_str    = ", ".join([g + " (" + str(p) + "%)" for g, p in genres[:3]]) if genres else "not detected"
    moments_str  = " ".join([m["text"] for m in moments[:3]])

    lfm_line = (f"Average Last.fm listeners across top artists: {traits['avg_listeners']:,}."
                if traits['avg_listeners'] > 0 else "Last.fm data not available.")

    prompt = f"""You are analyzing someone's music listening behavior across {traits['n_years']} years of data ({traits['yr_min']}–{traits['yr_max']}).

Behavioral stats:
- Archetype: {archetype}
- Top artist: {top_artist} ({top_artist_h}h)
- Depth: {traits['depth_score']}/100 — {traits['avg_ppt']} plays/track avg, {traits['avg_unique_tracks']} unique tracks per top artist
- Exploration: {traits['exploration_score']}/100 — {traits['new_per_year']} new artists/year, {traits['art_per_100h']} per 100h
- Intentionality: {traits['intentionality_score']}/100 — {traits['skip_rate']}% skip, {traits['shuffle_pct']}% shuffle
- Emotional volatility: {traits['volatility_score']}/100 — {traits['binge_sessions']} binge sessions, monthly CV {traits['cv']}
- Mainstream alignment: {traits['mainstream_score']}/100. {lfm_line}
- Dominant genres: {genre_str}
- Key moments in data: {moments_str}

Write a behavioral portrait in exactly 5 sentences. Rules:
1. Be direct and specific — use actual numbers and artist names
2. Reveal something they probably didn't know about themselves
3. Tone: honest, slightly uncomfortable, never judgmental
4. Don't mention Spotify or music apps by name
5. Don't start every sentence with "you" — vary the structure
6. Each sentence reveals a different behavioral dimension
7. Last sentence: what the data cannot tell us

Return only the 5 sentences, no preamble, no formatting."""

    api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    if api_key:
        try:
            response = requests.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "Content-Type":      "application/json",
                    "x-api-key":         api_key,
                    "anthropic-version": "2023-06-01",
                },
                json={
                    "model":      "claude-sonnet-4-20250514",
                    "max_tokens": 400,
                    "messages":   [{"role": "user", "content": prompt}],
                },
                timeout=30,
            )
            if response.status_code == 200:
                text = response.json()["content"][0]["text"].strip()
                st.session_state['who_narrative'] = text
                return text
        except Exception:
            pass

    # ── Fallback rule-based (no key or API error) ─────────────────────────
    lines = [
        (f"{traits['n_years']} years of data, {traits['new_per_year']} new artists per year. "
         + ("Wide and restless." if traits['exploration_score'] > 60 else "Focused and selective.")),
        (f"{top_artist} — {top_artist_h}h. That is not a favourite. That is a relationship."),
    ]
    if traits['volatility_score'] > 60:
        lines.append(f"{traits['binge_sessions']} sessions over 2 hours. The listening comes in waves.")
    if traits['mainstream_score'] < 35 and traits['avg_listeners'] > 0:
        lines.append(f"Average of {traits['avg_listeners']:,} Last.fm listeners. You are not listening to what most people listen to.")
    lines.append(
        "The data records what you played, when, and how many times. "
        "It does not record why. That part belongs to you."
    )
    result = " ".join(lines)
    st.session_state['who_narrative'] = result
    return result


def _get_key_moments_cached(s):
    """Moments derived from score data — no dfm re-access needed."""
    return st.session_state.get('who_moments', [])


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

    if dfd is None:
        dfd = pd.DataFrame()

    # ── Read from prefetch cache — no recompute ───────────────────────────
    s      = st.session_state.get('score')
    traits = st.session_state.get('who_traits')

    if not s or not traits:
        # Fallback: compute on first render if prefetch missed
        import score as score_mod
        if not s:
            s = score_mod.compute_score(dfm, dfd, lib, playlists)
            if s:
                st.session_state['score'] = s
        if not traits:
            traits = _compute_traits(dfm, dfd)
            st.session_state['who_traits'] = traits
        if not s or not traits:
            return

    arch    = s.get('archetype', {})
    moments = _get_key_moments(dfm, dfd)
    st.session_state['who_moments'] = moments

    # ── Section 0 — Archetype (full) ──────────────────────────────────────
    _render_archetype(arch, s)

    # ── Section 1 — Narrative ─────────────────────────────────────────────
    st.markdown(
        "<div style='color:#A78BFA;font-size:.72em;font-weight:700;"
        "text-transform:uppercase;letter-spacing:.1em;margin-bottom:12px;'>"
        "The Reading</div>",
        unsafe_allow_html=True
    )

    with st.spinner("Generating your behavioral portrait..."):
        narrative = _generate_narrative(traits, s)

    sentences = [x.strip() for x in narrative.replace("...", "…").split(". ") if x.strip()]
    narr_html = ""
    for i, sent in enumerate(sentences):
        if not sent.endswith((".", "!", "?", "…")):
            sent += "."
        opacity   = str(round(max(1 - i * 0.08, 0.55), 2))
        narr_html += (
            "<div style='color:#ccc;font-size:.95em;line-height:1.9;"
            "margin-bottom:8px;opacity:" + opacity + ";'>" + sent + "</div>"
        )

    st.markdown(
        "<div style='background:linear-gradient(135deg,#06060f,#0a001a);"
        "border:1px solid #7C3AED33;border-radius:16px;padding:28px 32px;"
        "margin-bottom:24px;'>" + narr_html + "</div>",
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
            "name":   "Depth",
            "icon":   "🔬",
            "score":  traits["depth_score"],
            "detail": f"{traits['avg_unique_tracks']} unique tracks · {traits['avg_ppt']}x plays/track on top artists",
            "low":    "Surface consumer — you sample, rarely dive deep.",
            "high":   "Deep listener — you know catalogues, not just hits.",
        },
        {
            "name":   "Exploration",
            "icon":   "🌍",
            "score":  traits["exploration_score"],
            "detail": f"{traits['new_per_year']} new artists/year · {traits['art_per_100h']} per 100h",
            "low":    "Loyal — you return to what you know.",
            "high":   "Explorer — always looking for what's next.",
        },
        {
            "name":   "Intentionality",
            "icon":   "🎯",
            "score":  traits["intentionality_score"],
            "detail": f"{traits['skip_rate']}% skip · {traits['shuffle_pct']}% shuffle",
            "low":    "Passive — music as background, algorithm decides.",
            "high":   "Deliberate — every play is a choice.",
        },
        {
            "name":   "Emotional Volatility",
            "icon":   "🌊",
            "score":  traits["volatility_score"],
            "detail": f"{traits['binge_sessions']} binge sessions · variation index {traits['cv']}",
            "low":    "Stable — regular, consistent listening patterns.",
            "high":   "Volatile — intense bursts followed by silence.",
        },
        {
            "name":   "Mainstream Alignment",
            "icon":   "📡",
            "score":  traits["mainstream_score"],
            "detail": (f"avg {traits['avg_listeners']:,} Last.fm listeners"
                       if traits["avg_listeners"] > 0 else "Last.fm not loaded"),
            "low":    "Underground — you listen to what most people never find.",
            "high":   "Mainstream — you move with the crowd.",
        },
    ]

    for trait in trait_defs:
        score     = trait["score"]
        pl, pc    = _percentile_label(score)
        bar_color = GREEN if score >= 70 else VIOLET_LIGHT if score >= 45 else AMBER
        desc      = trait["high"] if score >= 55 else trait["low"]
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
            "<span style='font-size:.72em;font-weight:700;color:" + pc + ";"
            "background:" + pc + "22;padding:2px 8px;border-radius:8px;'>" + pl + "</span>"
            "<span style='font-size:.88em;font-weight:900;color:" + bar_color + ";'>"
            + str(score) + "/100</span>"
            "</div></div>"
            "<div style='background:#1a1a1a;border-radius:4px;height:6px;margin-bottom:8px;'>"
            "<div style='background:" + bar_color + ";width:" + str(score) + "%;"
            "height:6px;border-radius:4px;'></div>"
            "</div>"
            "<div style='color:#555;font-size:.78em;font-style:italic;'>" + desc + "</div>"
            "</div>",
            unsafe_allow_html=True
        )

    st.markdown("---")

    # ── Section 3 — Where You Stand ───────────────────────────────────────
    st.markdown(
        "<div style='color:#A78BFA;font-size:.72em;font-weight:700;"
        "text-transform:uppercase;letter-spacing:.1em;margin-bottom:16px;'>"
        "Where You Stand</div>",
        unsafe_allow_html=True
    )
    st.caption("Compared to the average Spotify user — based on published benchmarks.")

    n_years      = max(s.get('n_years', 1), 1)
    total_h_year = round(dfm['ms'].sum() / 3_600_000 / n_years)
    benchmarks   = [
        ("Unique artists lifetime", s.get('unique_artists', 0), 500,
         f"{s.get('unique_artists', 0)} vs avg 500"),
        ("New artists per year",    traits["new_per_year"],     80,
         f"{traits['new_per_year']} vs avg 80"),
        ("Skip rate",               100 - traits["skip_rate"],  75,
         f"{traits['skip_rate']}% skip vs avg 25%"),
        ("Hours per year",          total_h_year,               400,
         f"{total_h_year}h/year vs avg 400h"),
    ]

    cols = st.columns(2)
    for i, (label, user_val, bench_val, detail) in enumerate(benchmarks):
        ratio = user_val / bench_val if bench_val > 0 else 1
        if ratio >= 3:     pct_str, color = "Top 5%",    GREEN
        elif ratio >= 2:   pct_str, color = "Top 15%",   VIOLET_LIGHT
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

    # ── Section 4 — Key Moments ───────────────────────────────────────────
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
    genres = _get_genre_summary()
    GENRE_COLORS = {
        "Hip-Hop / Rap": "#f87171", "R&B / Soul": "#A78BFA",
        "Jazz / Folk": "#60a5fa", "Reggae / Dancehall": "#1DB954",
        "Afro": "#f59e0b", "Caribbean": "#f472b6", "Brazilian": "#34d399",
        "Pop": "#888", "Electronic": "#818cf8", "Rock / Indie": "#fb923c",
        "Classical / World": "#94a3b8", "Other": "#444",
    }
    if genres:
        parts = []
        for genre, pct in genres:
            c = GENRE_COLORS.get(genre, "#888")
            parts.append(
                "<span style='color:" + c + ";font-size:.82em;font-weight:700;"
                "background:" + c + "22;padding:5px 14px;border-radius:20px;'>"
                + genre + " · " + str(pct) + "%</span>"
            )
        st.markdown(
            "<div style='display:flex;flex-wrap:wrap;gap:8px;'>"
            + "".join(parts) + "</div>",
            unsafe_allow_html=True
        )
        st.markdown(
            "<div style='color:#444;font-size:.75em;margin-top:8px;'>"
            "Open Musical Horoscope → Your Genres tab for the full breakdown.</div>",
            unsafe_allow_html=True
        )
    else:
        st.markdown(
            "<div style='color:#555;font-size:.82em;'>"
            "Go to Musical Horoscope → Your Genres tab to load your genre profile first.</div>",
            unsafe_allow_html=True
        )

    # ── Refresh ───────────────────────────────────────────────────────────
    st.markdown("---")
    col_a, _ = st.columns([1, 3])
    with col_a:
        if st.button("Refresh analysis"):
            for k in ['who_traits', 'who_narrative', 'who_moments']:
                st.session_state.pop(k, None)
            st.rerun()
