import streamlit as st
import pandas as pd
from collections import defaultdict
import time

VIOLET       = "#7C3AED"
VIOLET_LIGHT = "#A78BFA"
GREEN        = "#1DB954"
AMBER        = "#f59e0b"
RED          = "#f87171"

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

GENRE_MAP = {
    "hip-hop": "Hip-Hop / Rap", "hip hop": "Hip-Hop / Rap", "rap": "Hip-Hop / Rap",
    "rap français": "Hip-Hop / Rap", "french rap": "Hip-Hop / Rap", "trap": "Hip-Hop / Rap",
    "gangsta rap": "Hip-Hop / Rap", "east coast rap": "Hip-Hop / Rap",
    "west coast rap": "Hip-Hop / Rap", "conscious hip hop": "Hip-Hop / Rap",
    "r&b": "R&B / Soul", "rnb": "R&B / Soul", "soul": "R&B / Soul",
    "neo soul": "R&B / Soul", "contemporary r&b": "R&B / Soul",
    "motown": "R&B / Soul", "funk": "R&B / Soul",
    "jazz": "Jazz / Folk", "folk": "Jazz / Folk", "folk jazz": "Jazz / Folk",
    "acoustic": "Jazz / Folk", "singer-songwriter": "Jazz / Folk",
    "blues": "Jazz / Folk", "delta blues": "Jazz / Folk",
    "electric blues": "Jazz / Folk", "chicago blues": "Jazz / Folk",
    "reggae": "Reggae / Dancehall", "dancehall": "Reggae / Dancehall",
    "roots reggae": "Reggae / Dancehall", "lovers rock": "Reggae / Dancehall",
    "ragga": "Reggae / Dancehall", "ska": "Reggae / Dancehall", "dub": "Reggae / Dancehall",
    "afrobeats": "Afro", "afropop": "Afro", "afro pop": "Afro",
    "afrobeat": "Afro", "african": "Afro", "afro": "Afro",
    "highlife": "Afro", "afro-beat": "Afro", "naija": "Afro", "nigerian pop": "Afro",
    "kompa": "Caribbean", "zouk": "Caribbean", "haitian": "Caribbean",
    "caribbean": "Caribbean", "soca": "Caribbean", "bouyon": "Caribbean",
    "gwoka": "Caribbean", "biguine": "Caribbean",
    "brazilian": "Brazilian", "samba": "Brazilian", "pagode": "Brazilian",
    "axé": "Brazilian", "forró": "Brazilian", "bossa nova": "Brazilian",
    "mpb": "Brazilian", "sertanejo": "Brazilian",
    "pop": "Pop", "dance pop": "Pop", "electropop": "Pop",
    "synthpop": "Pop", "teen pop": "Pop",
    "electronic": "Electronic", "house": "Electronic", "techno": "Electronic",
    "edm": "Electronic", "dance": "Electronic", "club": "Electronic",
    "rock": "Rock / Indie", "indie": "Rock / Indie", "indie rock": "Rock / Indie",
    "alternative": "Rock / Indie", "classic rock": "Rock / Indie", "britpop": "Rock / Indie",
    "classical": "Classical / World", "world": "Classical / World",
    "world music": "Classical / World", "latin": "Classical / World",
    "salsa": "Classical / World", "cumbia": "Classical / World",
}

def _map_tags(tags):
    for tag in tags:
        t = tag.lower().strip()
        if t in GENRE_MAP:
            return GENRE_MAP[t]
        for key, genre in GENRE_MAP.items():
            if key in t or t in key:
                return genre
    return "Other"

def _fmt(template, stats):
    try: return template.format(**stats)
    except: return template

def _card_block(label, color, content, bg):
    st.markdown(
        "<div style='color:" + color + ";font-size:.72em;font-weight:700;"
        "text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px;'>" + label + "</div>"
        "<div style='background:" + bg + ";border-left:3px solid " + color + ";"
        "border-radius:6px;padding:14px 16px;color:#ccc;font-size:.88em;"
        "line-height:1.7;margin-bottom:16px;'>" + content + "</div>",
        unsafe_allow_html=True
    )

def _quiz():
    st.markdown(
        "<div style='background:#0a0a0a;border:1px solid #1e1e1e;border-radius:14px;"
        "padding:20px;margin-bottom:20px;'>"
        "<div style='color:#A78BFA;font-size:.72em;font-weight:700;text-transform:uppercase;"
        "letter-spacing:.1em;margin-bottom:12px;'>Before you see your sign — 3 questions</div>"
        "<div style='color:#888;font-size:.82em;'>Answer honestly. We will compare with your actual data.</div>"
        "</div>",
        unsafe_allow_html=True
    )
    q1 = st.text_input(
        "Your #1 artist all-time according to you:",
        placeholder="e.g. Taylor Swift",
        key="quiz_artist_input"
    )
    q2 = st.selectbox(
        "How would you describe your listening style?",
        ["— pick one —",
         "Explorer — I'm always finding new things",
         "Loyalist — I know what I like and I go deep",
         "Passive — Music is mostly background for me",
         "Eclectic — I genuinely listen to everything"],
        key="quiz_style_input"
    )
    q3 = st.selectbox(
        "When do you listen most?",
        ["— pick one —", "Morning (before 9am)", "Daytime (9am-6pm)",
         "Evening (6pm-10pm)", "Night (after 10pm)"],
        key="quiz_time_input"
    )
    if st.button("Reveal my sign →", type="primary", use_container_width=True):
        if q2 == "— pick one —" or q3 == "— pick one —":
            st.warning("Answer all 3 questions first.")
            return
        st.session_state['quiz_done']        = True
        st.session_state['quiz_artist_save'] = q1
        st.session_state['quiz_style_save']  = q2
        st.session_state['quiz_time_save']   = q3
        st.rerun()

def _gap_analysis(s):
    quiz_artist = st.session_state.get('quiz_artist_save', '')
    quiz_style  = st.session_state.get('quiz_style_save', '')
    quiz_time   = st.session_state.get('quiz_time_save', '')
    gaps = []

    real_artist = str(s.get('top_artist', ''))
    confirmed   = quiz_artist.strip().lower() == real_artist.lower() if quiz_artist.strip() else False
    gaps.append({
        "label": "Your #1 artist",
        "you_said": quiz_artist.strip() or "—",
        "data_says": real_artist + " (" + str(round(s.get('top_artist_h', 0))) + "h)",
        "verdict": "You know yourself. Rare." if confirmed else
                   "You said one name. Your data said another. That gap is the whole point of this app.",
        "ok": confirmed,
    })

    style_map = {
        "Explorer — I'm always finding new things":    ("explorer", s.get('art_per_year', 0) > 150),
        "Loyalist — I know what I like and I go deep": ("loyalist", s.get('old_music_pct', 0) > 50),
        "Passive — Music is mostly background for me": ("passive",  s.get('shuffle_pct', 0) > 50),
        "Eclectic — I genuinely listen to everything": ("eclectic",
            s.get('unique_artists', 0) > 3000 and s.get('tracks_per_artist', 10) > 3),
    }
    sel = style_map.get(quiz_style, ("unknown", False))
    style_key, style_ok = sel
    style_reality = {
        "explorer": str(int(s.get('art_per_year', 0))) + " new artists/year. " +
                    ("Data confirms this." if s.get('art_per_year', 0) > 150 else "But you explore less than you think."),
        "loyalist": str(round(s.get('old_music_pct', 0))) + "% old music. " +
                    ("Confirmed." if s.get('old_music_pct', 0) > 50 else "But you discover more than you admit."),
        "passive":  str(round(s.get('shuffle_pct', 0))) + "% shuffle. " +
                    ("At least you're honest." if s.get('shuffle_pct', 0) > 50 else "You're more active than you think."),
        "eclectic": str(s.get('unique_artists', 0)) + " artists · " +
                    str(round(s.get('tracks_per_artist', 0), 1)) + " tracks/artist. " +
                    ("Genuinely eclectic." if style_ok else "Wide but shallow. The Fake Eclectic is calling."),
    }
    gaps.append({
        "label": "Your listening style",
        "you_said": quiz_style.split(" — ")[0] if " — " in quiz_style else quiz_style,
        "data_says": style_reality.get(style_key, "Data says it's complicated."),
        "verdict": "Confirmed." if style_ok else "Your data disagrees.",
        "ok": style_ok,
    })

    peak_h   = s.get('peak_hour', 18)
    time_map = {
        "Morning (before 9am)": 5 <= peak_h <= 8,
        "Daytime (9am-6pm)":    9 <= peak_h <= 17,
        "Evening (6pm-10pm)":   18 <= peak_h <= 21,
        "Night (after 10pm)":   peak_h >= 22 or peak_h <= 4,
    }
    time_key = quiz_time.split(" (")[0] if " (" in quiz_time else quiz_time
    time_ok  = time_map.get(quiz_time, False)
    gaps.append({
        "label": "When you listen",
        "you_said": time_key,
        "data_says": str(peak_h).zfill(2) + "h is your actual peak hour.",
        "verdict": "Confirmed." if time_ok else "Your peak hour tells a different story.",
        "ok": time_ok,
    })

    st.markdown(
        "<div style='color:#A78BFA;font-size:.72em;font-weight:700;"
        "text-transform:uppercase;letter-spacing:.1em;margin:20px 0 12px;'>"
        "What you said vs what your data says</div>",
        unsafe_allow_html=True
    )
    for gap in gaps:
        color = GREEN if gap['ok'] else RED
        st.markdown(
            "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
            "border-left:3px solid " + color + ";border-radius:8px;padding:14px;margin-bottom:8px;'>"
            "<div style='font-size:.72em;color:#888;font-weight:700;text-transform:uppercase;"
            "letter-spacing:.08em;margin-bottom:8px;'>" + gap['label'] + "</div>"
            "<div style='display:flex;gap:16px;flex-wrap:wrap;margin-bottom:8px;'>"
            "<div style='flex:1;min-width:120px;'>"
            "<div style='font-size:.72em;color:#888;margin-bottom:3px;'>You said</div>"
            "<div style='color:#fff;font-weight:700;font-size:.9em;'>" + gap['you_said'] + "</div>"
            "</div>"
            "<div style='flex:1;min-width:120px;'>"
            "<div style='font-size:.72em;color:#888;margin-bottom:3px;'>Data says</div>"
            "<div style='color:" + color + ";font-weight:700;font-size:.9em;'>" + gap['data_says'] + "</div>"
            "</div></div>"
            "<div style='color:#888;font-size:.78em;font-style:italic;'>" + gap['verdict'] + "</div>"
            "</div>",
            unsafe_allow_html=True
        )

# ── Genre tab ─────────────────────────────────────────────────────────────────

def _render_genres(dfm):
    """Inline genre profile for the Horoscope tab."""

    try:
        import lastfm
        if not lastfm.is_available():
            st.markdown(
                "<div style='background:#0f0f0f;border:1px solid #f59e0b33;"
                "border-left:3px solid #f59e0b;border-radius:8px;padding:14px;'>"
                "<div style='color:#f59e0b;font-size:.78em;font-weight:700;"
                "margin-bottom:6px;'>Last.fm not configured</div>"
                "<div style='color:#888;font-size:.82em;'>"
                "Add LASTFM_API_KEY to your Railway environment variables to enable genre detection."
                "</div></div>",
                unsafe_allow_html=True
            )
            return
    except ImportError:
        st.error("lastfm.py not found.")
        return

    cache_key = "genre_inline_data"
    if cache_key not in st.session_state:
        kids_kw = ['bébé','baby','lullaby','titounis','mancebo','bernardo','celesti',
                   'mclaughlin','moons','kiboomers','teddy','wonderland','comptines',
                   'petit ours','ainsi font','percussioney','batukem','tukada',
                   'música para bebés','alain royer','miracle tones']
        def is_kids(n): return any(k in n.lower() for k in kids_kw)
        df_c = dfm[~dfm['artistName'].apply(is_kids)]

        top_artists = (
            df_c.groupby('artistName')['ms'].sum() / 3600000
        ).nlargest(150)

        genre_hours   = defaultdict(float)
        artist_genres = {}
        yearly_genres = defaultdict(lambda: defaultdict(float))

        bar = st.progress(0, text="Detecting genres via Last.fm...")
        for i, (artist, hours) in enumerate(top_artists.items()):
            info  = lastfm.get_artist_info(artist)
            genre = _map_tags(info.get("tags", [])) or "Other"
            artist_genres[artist] = genre
            genre_hours[genre]   += hours

            sub = df_c[df_c['artistName'] == artist]
            for yr, grp in sub.groupby('year'):
                yearly_genres[yr][genre] += grp['ms'].sum() / 3600000

            bar.progress((i + 1) / len(top_artists),
                         text=f"Last.fm — {artist[:30]}...")
            time.sleep(0.12)
        bar.empty()

        st.session_state[cache_key] = {
            "genre_hours":   dict(genre_hours),
            "artist_genres": artist_genres,
            "yearly_genres": {yr: dict(v) for yr, v in yearly_genres.items()},
        }

    data          = st.session_state[cache_key]
    genre_hours   = data["genre_hours"]
    artist_genres = data["artist_genres"]
    yearly_genres = data["yearly_genres"]

    total_h       = sum(genre_hours.values())
    if total_h == 0:
        st.info("No genre data detected.")
        return

    sorted_genres = sorted(genre_hours.items(), key=lambda x: -x[1])
    top_genres    = [g for g, h in sorted_genres if g != "Other"][:6]

    # ── Top genres hero ───────────────────────────────────────────────────
    st.markdown(
        "<div style='color:#A78BFA;font-size:.72em;font-weight:700;"
        "text-transform:uppercase;letter-spacing:.1em;margin-bottom:12px;'>"
        "Your dominant genres</div>",
        unsafe_allow_html=True
    )

    cols = st.columns(min(len(sorted_genres[:4]), 4))
    for col, (genre, hours) in zip(cols, sorted_genres[:4]):
        pct   = round(hours / total_h * 100)
        color = GENRE_COLORS.get(genre, "#888")
        with col:
            st.markdown(
                "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
                "border-left:3px solid " + color + ";border-radius:10px;"
                "padding:14px;text-align:center;'>"
                "<div style='font-size:1.4em;font-weight:900;color:" + color + ";'>"
                + str(pct) + "%</div>"
                "<div style='font-size:.75em;color:#fff;font-weight:700;margin:4px 0;'>"
                + genre + "</div>"
                "<div style='font-size:.68em;color:#555;'>" + str(round(hours)) + "h</div>"
                "</div>",
                unsafe_allow_html=True
            )

    st.markdown("<div style='margin:16px 0 8px;'></div>", unsafe_allow_html=True)

    # ── All genres bar ────────────────────────────────────────────────────
    for genre, hours in sorted_genres:
        if hours < 1: continue
        pct   = round(hours / total_h * 100)
        bar_w = min(pct * 2, 100)
        color = GENRE_COLORS.get(genre, "#444")
        st.markdown(
            "<div style='margin-bottom:8px;'>"
            "<div style='display:flex;justify-content:space-between;"
            "align-items:center;margin-bottom:3px;'>"
            "<span style='font-size:.82em;color:#ccc;font-weight:600;'>" + genre + "</span>"
            "<span style='font-size:.78em;color:" + color + ";font-weight:700;'>"
            + str(round(hours)) + "h · " + str(pct) + "%</span>"
            "</div>"
            "<div style='background:#1a1a1a;border-radius:3px;height:5px;'>"
            "<div style='background:" + color + ";width:" + str(bar_w) + "%;"
            "height:5px;border-radius:3px;'></div>"
            "</div></div>",
            unsafe_allow_html=True
        )

    st.markdown("---")

    # ── Evolution by year ─────────────────────────────────────────────────
    st.markdown(
        "<div style='color:#A78BFA;font-size:.72em;font-weight:700;"
        "text-transform:uppercase;letter-spacing:.1em;margin-bottom:12px;'>"
        "Evolution by year</div>",
        unsafe_allow_html=True
    )

    years_desc = sorted(yearly_genres.keys(), reverse=True)
    for yr in years_desc:
        yr_data  = yearly_genres[yr]
        yr_total = sum(yr_data.values())
        if yr_total < 10: continue

        top3_yr = sorted(yr_data.items(), key=lambda x: -x[1])[:3]
        badges  = ""
        for genre, hours in top3_yr:
            pct   = round(hours / yr_total * 100)
            if pct < 5: continue
            color = GENRE_COLORS.get(genre, "#444")
            badges += (
                "<span style='color:" + color + ";font-size:.72em;font-weight:700;"
                "background:" + color + "22;padding:2px 8px;border-radius:8px;"
                "margin-right:5px;'>" + genre + " " + str(pct) + "%</span>"
            )

        st.markdown(
            "<div style='display:flex;align-items:center;gap:12px;"
            "padding:8px 0;border-bottom:1px solid #1a1a1a;'>"
            "<span style='font-size:.85em;font-weight:900;color:#fff;"
            "min-width:36px;'>" + str(yr) + "</span>"
            "<div style='flex:1;'>" + badges + "</div>"
            "<span style='color:#444;font-size:.72em;'>"
            + str(round(yr_total)) + "h</span>"
            "</div>",
            unsafe_allow_html=True
        )

    st.markdown("<div style='margin-top:12px;'></div>", unsafe_allow_html=True)
    if st.button("Refresh genre data", key="refresh_genres"):
        if cache_key in st.session_state:
            del st.session_state[cache_key]
        st.rerun()

# ── Main render ───────────────────────────────────────────────────────────────

def render(dfm, dfd=None, lib=None, playlists=None):
    st.title("🔮 Musical Horoscope")
    st.markdown("*Your musical sign — derived from actual behaviour, not vibes.*")

    if dfd is None: dfd = pd.DataFrame()

    import score as score_mod
    s = score_mod.compute_score(dfm, dfd, lib, playlists)
    if not s: return

    arch = s['archetype']

    if not st.session_state.get('quiz_done', False):
        _quiz()
        st.stop()

    if not st.session_state.get('gap_shown', False):
        _gap_analysis(s)
        st.session_state['gap_shown'] = True
        st.markdown("---")

    tab1, tab2, tab3 = st.tabs(["Your Sign", "All Signs", "🎼 Your Genres"])

    with tab1:
        st.markdown(
            "<div style='background:linear-gradient(135deg,#06060f,#0a001a);"
            "border:1px solid #7C3AED55;border-radius:20px;padding:36px;"
            "text-align:center;margin-bottom:28px;'>"
            "<div style='font-size:3.5em;margin-bottom:8px;'>" + arch.get('emoji', '🎵') + "</div>"
            "<div style='font-size:.7em;color:#888;text-transform:uppercase;"
            "letter-spacing:.14em;margin-bottom:6px;'>Your Musical Sign</div>"
            "<div style='font-size:2em;font-weight:900;color:#A78BFA;'>" + arch['name'] + "</div>"
            "<div style='color:#555;font-size:.82em;margin-top:10px;font-style:italic;'>"
            + _fmt(arch.get('data_line', ''), s) + "</div>"
            "</div>",
            unsafe_allow_html=True
        )

        col1, col2 = st.columns(2)
        with col1:
            _card_block("Your Curse",      RED,          _fmt(arch['curse'], s),      "#0f0505")
            _card_block("Your Gift",       GREEN,        _fmt(arch['gift'], s),       "#050f05")
        with col2:
            _card_block("Your Prediction", VIOLET_LIGHT, _fmt(arch['prediction'], s), "#0a0520")

            st.markdown(
                "<div style='color:#888;font-size:.72em;font-weight:700;"
                "text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px;'>"
                "Your Numbers</div>",
                unsafe_allow_html=True
            )
            rows = [
                ("Artists",         f"{s['unique_artists']:,}"),
                ("Years",           str(s['n_years'])),
                ("Skip rate",       f"{s['skip_rate']:.0f}%"),
                ("Shuffle rate",    f"{s['shuffle_pct']:.0f}%"),
                ("Binge sessions",  str(s['binge_sessions']) + " ≥2h"),
                ("Top artist",      f"{s['top_artist_pct']:.0f}% → {s['top_artist']}"),
                ("Old music",       f"{s['old_music_pct']:.0f}%"),
                ("Night listening", f"{s['night_pct']:.0f}%"),
            ]
            if s['kids_pct'] > 1:
                rows.append(("Kids content", f"{s['kids_pct']:.0f}%"))
            html = "<div style='background:#0f0f0f;border:1px solid #1e1e1e;border-radius:10px;padding:14px;'>"
            for lbl, val in rows:
                html += (
                    "<div style='display:flex;justify-content:space-between;padding:5px 0;"
                    "border-bottom:1px solid #1a1a1a;font-size:.82em;'>"
                    "<span style='color:#888;'>" + lbl + "</span>"
                    "<span style='color:#fff;font-weight:700;'>" + val + "</span></div>"
                )
            html += "</div>"
            st.markdown(html, unsafe_allow_html=True)

        st.markdown("---")
        col_a, col_b = st.columns([1, 3])
        with col_a:
            if st.button("Retake quiz"):
                st.session_state['quiz_done'] = False
                st.session_state['gap_shown'] = False
                st.rerun()
        st.markdown("**Share your sign:**")
        st.code(
            arch.get('emoji', '🎵') + " I am " + arch['name'] +
            " — my musical sign from " + str(s['n_years']) + " years of Spotify data. "
            "Powered by MusicDNA. musicdna-dhalsimq.up.railway.app"
        )

    with tab2:
        from score import ALL_ARCHETYPES
        st.markdown("### All 14 Musical Signs")
        st.caption("Which ones are close to you?")
        cols = st.columns(2)
        for i, a in enumerate(ALL_ARCHETYPES):
            is_yours = a['key'] == arch['key']
            border   = "#A78BFA" if is_yours else "#1e1e1e"
            badge    = (" <span style='color:#A78BFA;font-size:.7em;"
                        "background:#7C3AED22;padding:2px 8px;border-radius:10px;'>"
                        "← yours</span>") if is_yours else ""
            with cols[i % 2]:
                st.markdown(
                    "<div style='background:#0f0f0f;border:1px solid " + border + ";"
                    "border-left:3px solid " + border + ";border-radius:10px;"
                    "padding:14px;margin-bottom:10px;'>"
                    "<div style='font-size:1.4em;margin-bottom:4px;'>" + a['emoji'] + "</div>"
                    "<div style='font-weight:800;color:#fff;font-size:.92em;'>"
                    + a['name'] + badge + "</div>"
                    "<div style='color:#888;font-size:.78em;margin-top:6px;line-height:1.5;'>"
                    + a['desc'] + "</div>"
                    "</div>",
                    unsafe_allow_html=True
                )

    with tab3:
        st.markdown(
            "<div style='color:#888;font-size:.82em;margin-bottom:16px;line-height:1.6;'>"
            "Your dominant genres — detected from Last.fm tags on your top 150 artists. "
            "Takes ~20 seconds on first load. Cached for the rest of the session."
            "</div>",
            unsafe_allow_html=True
        )
        _render_genres(dfm)
