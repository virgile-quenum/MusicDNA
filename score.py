import streamlit as st
import pandas as pd

VIOLET       = "#7C3AED"
VIOLET_LIGHT = "#A78BFA"
GREEN        = "#1DB954"
AMBER        = "#f59e0b"
RED          = "#f87171"

def get_archetype(dims, stats):
    u = stats

    if u.get("kids_pct", 0) > 25:
        return {"key":"infiltrated_parent","name":"The Infiltrated Parent","emoji":"👶",
            "curse":"A quarter of your Spotify history is children's content. {kids_pct:.0f}%. That is not a phase — that is a colonisation. Spotify's algorithm has given up trying to understand you.",
            "gift":"You kept listening through the chaos. {kids_h:.0f} hours of children's content later, your own taste survived. That is not nothing.",
            "prediction":"The curve is declining. Your account is slowly returning to you. Full reclamation by 2027. Probably.",
            "data_line":"{kids_pct:.0f}% children's content · {kids_h:.0f}h total · peak {kids_peak_year}."}

    if u.get("top_artist_pct", 0) > 15:
        return {"key":"one_track_mind","name":"The One-Track Mind","emoji":"🔁",
            "curse":"Your #1 artist is {top_artist_pct:.0f}% of your entire listening history. {top_artist_h:.0f} hours. Everyone around you has heard enough. You have not.",
            "gift":"You found something real. Most people skim the surface their entire lives. You went deep. That knowledge is yours.",
            "prediction":"You will discover someone new who sounds like them. You will play them once. You will go back to {top_artist} within 48 hours.",
            "data_line":"{top_artist}: {top_artist_h:.0f}h — {top_artist_pct:.0f}% of your Spotify life."}

    if u.get("old_music_pct", 0) > 65:
        return {"key":"nostalgia_prisoner","name":"The Nostalgia Prisoner","emoji":"⏳",
            "curse":"{old_music_pct:.0f}% of your listening is artists you discovered over 5 years ago. You are not exploring. You are maintaining a relationship with a version of yourself that no longer exists.",
            "gift":"You know what you love. The artists that survived 5 years with you are the real ones. Everything else was noise you correctly filtered out.",
            "prediction":"You will discover one artist this year who earns a permanent spot. It will remind you of something from {oldest_year}. You will pretend that is a coincidence.",
            "data_line":"{old_music_pct:.0f}% plays from artists discovered 5+ years ago."}

    if u.get("shuffle_pct", 0) > 65 and u.get("skip_rate", 0) > 25:
        return {"key":"radio_head","name":"The Radio Head","emoji":"📻",
            "curse":"{shuffle_pct:.0f}% shuffle. You are not curating a music experience — you are outsourcing it. Spotify is your background noise and you have made peace with that.",
            "gift":"Passive listening is still listening. Some of your best discoveries were accidents you would never have made intentionally.",
            "prediction":"Your next favourite track will arrive unannounced during a shuffle you almost skipped. You will not remember how you found it.",
            "data_line":"{shuffle_pct:.0f}% shuffle · {skip_rate:.0f}% skip rate · {total_plays:,} plays."}

    if u.get("playlist_staleness", 0) > 0.7 and u.get("playlist_concentration", 0) > 0.5:
        return {"key":"playlist_mummy","name":"The Playlist Mummy","emoji":"🪦",
            "curse":"You built your playlists years ago and you have not touched them since. They are a museum of who you were. You visit them daily. You never update them.",
            "gift":"Those playlists represent real curation work. Most people delete and rebuild every year. You committed to something.",
            "prediction":"You will create one new playlist this year. It will have 8 tracks. You will add nothing to it for 14 months.",
            "data_line":"{stale_playlist_pct:.0f}% of playlists untouched for 2+ years."}

    if u.get("mainstream_pct", 0) > 65 and u.get("avg_artist_popularity", 0) > 72:
        return {"key":"spotify_sheep","name":"The Spotify Sheep","emoji":"🐑",
            "curse":"Average artist popularity: {avg_artist_popularity:.0f}/100. You are not discovering music — you are consuming what the algorithm decided you should hear.",
            "gift":"Popular music is popular for a reason. You have impeccable commercial taste and you are never embarrassed by what you play at parties.",
            "prediction":"You will hear a song on an editorial playlist, add it to your library, and forget where you found it. This will happen multiple times this year.",
            "data_line":"Avg popularity {avg_artist_popularity:.0f}/100 · {mainstream_pct:.0f}% mainstream artists."}

    if u.get("unique_artists", 0) > 4000 and u.get("tracks_per_artist", 0) < 2.0:
        return {"key":"fake_eclectic","name":"The Fake Eclectic","emoji":"🎭",
            "curse":"{unique_artists:,} artists. {tracks_per_artist:.1f} tracks per artist on average. You collect first impressions. You say you like everything. What you mean is you have heard everything once and committed to almost nothing.",
            "gift":"Your map of music is wider than almost anyone's. When something finally earns repeat listens, it is genuinely exceptional.",
            "prediction":"Someone will ask for music recommendations. You will give 12 artists. None of them will be someone you have listened to in the last 3 months.",
            "data_line":"{unique_artists:,} artists · {tracks_per_artist:.1f} avg tracks/artist."}

    if u.get("art_per_year", 0) > 300 and u.get("skip_rate", 0) > 30 and u.get("top50_hours", 0) < 5:
        return {"key":"algorithm_tourist","name":"The Algorithm Tourist","emoji":"✈️",
            "curse":"You discover {art_per_year:.0f} new artists per year and remember none of them. You are always looking for the next one. The artist you found last Tuesday is already a stranger.",
            "gift":"You find things 2 years before everyone else. You just never stay long enough to get credit.",
            "prediction":"You will discover something extraordinary this year and move on before anyone else hears it. You will rediscover it 3 years later when it is famous and feel nothing.",
            "data_line":"{art_per_year:.0f} new artists/year · {skip_rate:.0f}% skip · {top50_hours:.0f}h avg on top 50."}

    if u.get("avg_artist_popularity", 100) < 35 and u.get("unique_artists", 0) > 500:
        return {"key":"underground_snob","name":"The Underground Snob","emoji":"🕶️",
            "curse":"Your artists average {avg_artist_popularity:.0f}/100 popularity. You are not just avoiding mainstream — you are allergic to it. If more than 1,000 people have heard it, something is probably wrong.",
            "gift":"Your taste is genuinely original. The underground artists you support actually need the streams.",
            "prediction":"One of your obscure favourites will blow up this year. You will have complicated feelings about this.",
            "data_line":"Avg popularity {avg_artist_popularity:.0f}/100 · {unique_artists:,} artists."}

    if u.get("binge_sessions", 0) > 25 and u.get("top_artist_pct", 0) > 8:
        return {"key":"obsessive","name":"The Obsessive","emoji":"🌀",
            "curse":"{binge_sessions} sessions over 2 hours. You do not listen to music — you disappear into it. You find something, exhaust it completely, then move on like it never existed.",
            "gift":"You are capable of total immersion. Most people never experience music the way you do.",
            "prediction":"Your next obsession is already forming. You have listened to one track 3 times this week and have not noticed yet.",
            "data_line":"{binge_sessions} binge sessions · {top_artist_pct:.0f}% on top artist."}

    if u.get("old_music_pct", 0) > 45 and u.get("skip_rate", 0) > 28:
        return {"key":"passive_loyalist","name":"The Passive Loyalist","emoji":"💤",
            "curse":"You keep coming back to the same artists but skip {skip_rate:.0f}% of what you play. You are loyal to the idea of them more than the actual music.",
            "gift":"Your artists are not background noise — they are anchors. You just have a complicated relationship with them.",
            "prediction":"You will add a new artist to your regular rotation this year. It will take 6 months before you admit you actually like them.",
            "data_line":"{old_music_pct:.0f}% old artists · {skip_rate:.0f}% skip · {loyalty_years:.1f}yr avg loyalty."}

    if u.get("binge_sessions", 0) > 15 and u.get("night_pct", 0) > 22:
        return {"key":"binge_escaper","name":"The Binge Escaper","emoji":"🌙",
            "curse":"{night_pct:.0f}% of your listening is after 10pm. {binge_sessions} sessions over 2 hours. Music is not entertainment — it is a place you go when you need to disappear.",
            "gift":"What you play at 1am is your most authentic musical self. No performance, no context, just what you actually need.",
            "prediction":"Your listening will intensify before it stabilises. Something is unresolved. Music knows before you do.",
            "data_line":"{night_pct:.0f}% after 10pm · {binge_sessions} binge sessions · peak {peak_hour:02d}h."}

    return {"key":"deliberate_listener","name":"The Deliberate Listener","emoji":"🎯",
        "curse":"No single pathology dominates your listening. {unique_artists:,} artists, {n_years} years, no obvious obsession or avoidance. This is either extremely healthy or extremely boring. Probably both.",
        "gift":"Genuine balance is rarer than any extreme. The algorithm has no idea what to do with you.",
        "prediction":"You will continue to surprise yourself. This is the best possible outcome and also the least interesting story.",
        "data_line":"{unique_artists:,} artists · {n_years} years · no dominant pattern."}

ALL_ARCHETYPES = [
    {"key":"infiltrated_parent",  "name":"The Infiltrated Parent",  "emoji":"👶", "desc":"25%+ of history is children's content."},
    {"key":"one_track_mind",      "name":"The One-Track Mind",       "emoji":"🔁", "desc":"One artist dominates everything."},
    {"key":"nostalgia_prisoner",  "name":"The Nostalgia Prisoner",   "emoji":"⏳", "desc":"Living in the musical past."},
    {"key":"radio_head",          "name":"The Radio Head",           "emoji":"📻", "desc":"Spotify as background noise."},
    {"key":"playlist_mummy",      "name":"The Playlist Mummy",       "emoji":"🪦", "desc":"Playlists frozen in time."},
    {"key":"spotify_sheep",       "name":"The Spotify Sheep",        "emoji":"🐑", "desc":"Algorithm decides everything."},
    {"key":"fake_eclectic",       "name":"The Fake Eclectic",        "emoji":"🎭", "desc":"5000 artists, same 50 on repeat."},
    {"key":"algorithm_tourist",   "name":"The Algorithm Tourist",    "emoji":"✈️", "desc":"Explores everything, remembers nothing."},
    {"key":"underground_snob",    "name":"The Underground Snob",     "emoji":"🕶️", "desc":"If it's popular, it's suspect."},
    {"key":"obsessive",           "name":"The Obsessive",            "emoji":"🌀", "desc":"Binge, exhaust, move on."},
    {"key":"passive_loyalist",    "name":"The Passive Loyalist",     "emoji":"💤", "desc":"Loyal but not really listening."},
    {"key":"binge_escaper",       "name":"The Binge Escaper",        "emoji":"🌙", "desc":"Music as a place to disappear."},
    {"key":"deliberate_listener", "name":"The Deliberate Listener",  "emoji":"🎯", "desc":"No dominant pattern. Rare."},
]

def compute_score(dfm, dfd=None, lib=None, playlists=None):
    if dfm is None or dfm.empty:
        return None

    yr_min     = int(dfm['year'].min())
    yr_max     = int(dfm['year'].max())
    n_years    = max(yr_max - yr_min + 1, 1)
    my_h       = dfm['ms'].sum() / 3600000
    my_art     = dfm['artistName'].nunique()
    total_all  = my_h + ((dfd['ms'].sum() / 3600000) if dfd is not None and not dfd.empty else 0)
    kids_ms    = dfd['ms'].sum() if dfd is not None and not dfd.empty else 0
    kids_h     = kids_ms / 3600000
    kids_pct   = kids_h / total_all * 100 if total_all > 0 else 0

    artist_ms      = dfm.groupby('artistName')['ms'].sum()
    top_artist     = artist_ms.idxmax() if not artist_ms.empty else "—"
    top_artist_ms  = artist_ms.max() if not artist_ms.empty else 0
    top_artist_pct = top_artist_ms / dfm['ms'].sum() * 100 if dfm['ms'].sum() > 0 else 0
    top_artist_h   = top_artist_ms / 3600000

    skip_rate      = dfm['skipped'].mean() * 100 if 'skipped' in dfm.columns else 20
    shuffle_pct    = dfm['shuffle'].mean() * 100 if 'shuffle' in dfm.columns else 0
    track_counts   = dfm.groupby('trackName').size()
    repeat_rate    = (track_counts > 1).sum() / max(len(track_counts), 1)

    top50_hours = dfm.groupby('artistName')['ms'].sum().nlargest(50).mean() / 3600000
    art_per_100h = (my_art / my_h * 100) if my_h > 0 else 0

    new_per_year = dfm.groupby('year')['artistName'].apply(
        lambda x: x[~x.isin(dfm[dfm['year'] < x.name]['artistName'])].nunique()
        if x.name > yr_min else x.nunique()
    ).mean()

    artist_years     = dfm.groupby('artistName')['year'].nunique()
    loyalty_weighted = (artist_years * artist_ms).sum() / max(artist_ms.sum(), 1)

    first_seen    = dfm.groupby('artistName')['year'].min()
    old_artists   = set(first_seen[first_seen <= yr_max - 5].index)
    old_music_pct = dfm[dfm['artistName'].isin(old_artists)]['ms'].sum() / dfm['ms'].sum() * 100

    tracks_per_artist = dfm['trackName'].nunique() / max(my_art, 1)
    binge_sessions = 0
    df_s = dfm.sort_values('ts').copy()
    df_s['gap'] = df_s['ts'].diff().dt.total_seconds().fillna(0)
    df_s['sid'] = (df_s['gap'] > 1800).cumsum()
    sessions = df_s.groupby('sid')['ms'].sum() / 3600000
    binge_sessions = int((sessions >= 2).sum())

    night_ms  = dfm[dfm['hour'] >= 22]['ms'].sum()
    night_pct = night_ms / dfm['ms'].sum() * 100

    peak_year = int(dfm.groupby('year')['ms'].sum().idxmax())
    peak_hour = int(dfm.groupby('hour')['ms'].sum().idxmax())

    kids_peak_year = yr_max
    if dfd is not None and not dfd.empty and 'year' in dfd.columns:
        k = dfd.groupby('year')['ms'].sum()
        kids_peak_year = int(k.idxmax()) if not k.empty else yr_max

    # avg artist popularity proxy (tracks_per_artist inverse as rough signal)
    avg_artist_popularity = 50  # default — real value needs Spotify API
    mainstream_pct = 0

    # playlist staleness
    playlist_staleness = 0.0
    playlist_concentration = 0.0
    stale_playlist_pct = 0.0
    if playlists:
        try:
            import datetime
            now_year = yr_max
            stale = 0
            for pl in playlists:
                tracks = pl.get('items', [])
                if not tracks: continue
                last_added = max(
                    (t.get('addedDate', '') or '' for t in tracks),
                    default=''
                )
                if last_added and int(last_added[:4]) < now_year - 2:
                    stale += 1
            playlist_staleness = stale / max(len(playlists), 1)
            stale_playlist_pct = round(playlist_staleness * 100)
            # concentration: % plays from top 3 playlists (approximate)
            playlist_concentration = min(playlist_staleness, 1.0)
        except:
            pass

    # ── 5 dimension scores ──────────────────────────────────────────────
    diversity      = round(min(art_per_100h / 120, 1.0) * 20)
    depth          = round(min(top50_hours / 25, 1.0) * 20)
    intent_raw     = (1 - skip_rate/100) * 0.55 + repeat_rate * 0.45
    intentionality = round(min(intent_raw / 0.75, 1.0) * 20)
    discovery      = round(min(new_per_year / 380, 1.0) * 20)
    loyalty        = round(min(loyalty_weighted / 5.0, 1.0) * 20)
    total          = diversity + depth + intentionality + discovery + loyalty

    dims = {'diversity': diversity, 'depth': depth, 'intentionality': intentionality,
            'discovery': discovery, 'loyalty': loyalty}

    stats = {
        'unique_artists': my_art, 'n_years': n_years, 'oldest_year': yr_min,
        'peak_year': peak_year, 'peak_hour': peak_hour,
        'art_per_year': my_art / n_years, 'art_per_100h': round(art_per_100h, 1),
        'top50_hours': round(top50_hours, 1),
        'top_artist': top_artist, 'top_artist_pct': top_artist_pct, 'top_artist_h': top_artist_h,
        'skip_rate': round(skip_rate, 1), 'shuffle_pct': round(shuffle_pct, 1),
        'repeat_rate': round(repeat_rate * 100, 1),
        'binge_sessions': binge_sessions, 'night_pct': round(night_pct, 1),
        'old_music_pct': round(old_music_pct, 1), 'tracks_per_artist': round(tracks_per_artist, 1),
        'loyalty_years': round(loyalty_weighted, 1), 'avg_new': int(new_per_year),
        'total_plays': len(dfm), 'kids_pct': round(kids_pct, 1), 'kids_h': round(kids_h, 1),
        'kids_peak_year': kids_peak_year,
        'avg_artist_popularity': avg_artist_popularity, 'mainstream_pct': mainstream_pct,
        'playlist_staleness': playlist_staleness, 'playlist_concentration': playlist_concentration,
        'stale_playlist_pct': stale_playlist_pct, 'proj_new': int(my_art / n_years),
    }

    archetype = get_archetype(dims, stats)

    return {**stats, **dims, 'total': total,
            'archetype': archetype, 'dims': dims}

def score_label(total):
    if total >= 85: return "Legendary", GREEN
    if total >= 70: return "Expert",    VIOLET_LIGHT
    if total >= 55: return "Advanced",  VIOLET_LIGHT
    if total >= 40: return "Active",    AMBER
    return "Casual", "#888"

def _dim_bars(s):
    dims = [
        ("Diversity",      s['diversity'],      "🌍", str(s['art_per_100h']) + " artists/100h"),
        ("Depth",          s['depth'],          "🔬", str(s['top50_hours']) + "h avg on top artists"),
        ("Intentionality", s['intentionality'], "🎯", str(s['skip_rate']) + "% skip · " + str(s['repeat_rate']) + "% repeat"),
        ("Discovery",      s['discovery'],      "🔭", str(s['avg_new']) + " new artists/year"),
        ("Loyalty",        s['loyalty'],        "❤️",  str(s['loyalty_years']) + "yr weighted avg"),
    ]
    html = ""
    for name, val, icon, detail in dims:
        pct = int(val / 20 * 100)
        bar_color = GREEN if pct >= 80 else VIOLET_LIGHT if pct >= 50 else AMBER if pct >= 30 else "#444"
        html += (
            "<div style='margin-bottom:11px;'>"
            "<div style='display:flex;justify-content:space-between;margin-bottom:3px;'>"
            "<span style='font-size:.8em;color:#aaa;font-weight:600;'>" + icon + " " + name + "</span>"
            "<span style='font-size:.75em;color:#555;'>" + detail + "</span>"
            "</div>"
            "<div style='background:#1a1a1a;border-radius:4px;height:7px;'>"
            "<div style='background:" + bar_color + ";border-radius:4px;height:7px;width:" + str(pct) + "%;'></div>"
            "</div></div>"
        )
    return html

def _fmt(template, stats):
    try: return template.format(**stats)
    except: return template

def render(dfm, dfd=None, lib=None, playlists=None):
    s = compute_score(dfm, dfd, lib, playlists)
    if not s: return

    lbl, color = score_label(s['total'])
    arch = s['archetype']

    st.markdown(
        "<div style='background:linear-gradient(135deg,#060610,#0d0020);"
        "border:2px solid " + color + "33;border-radius:20px;padding:28px 32px;margin-bottom:6px;'>"
        "<div style='display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:24px;margin-bottom:20px;'>"
        "<div>"
        "<div style='font-size:.68em;color:#444;text-transform:uppercase;letter-spacing:.14em;margin-bottom:6px;'>MusicDNA Score</div>"
        "<div style='font-size:4.5em;font-weight:900;color:" + color + ";line-height:1;'>" + str(s['total']) + "</div>"
        "<div style='color:#555;font-size:.8em;margin-top:3px;'>/100</div>"
        "<div style='margin-top:10px;'>"
        "<span style='background:" + color + "22;color:" + color + ";font-weight:800;font-size:.82em;padding:4px 14px;border-radius:20px;'>" + lbl + " Listener</span>"
        "</div></div>"
        "<div style='flex:1;min-width:220px;background:#0a0a0a;border:1px solid #1e1e1e;border-radius:14px;padding:18px;'>"
        "<div style='font-size:.68em;color:#444;text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px;'>Your Archetype</div>"
        "<div style='font-size:2em;margin-bottom:4px;'>" + arch['emoji'] + "</div>"
        "<div style='font-size:1.1em;font-weight:900;color:#fff;margin-bottom:8px;'>" + arch['name'] + "</div>"
        "<div style='color:#555;font-size:.8em;line-height:1.6;font-style:italic;'>" + _fmt(arch['data_line'], s) + "</div>"
        "</div></div>"
        "<div>" + _dim_bars(s) + "</div>"
        "</div>",
        unsafe_allow_html=True
    )

    dims = s['dims']
    strongest = max(dims, key=dims.get)
    weakest   = min(dims, key=dims.get)
    labels = {'diversity':'breadth of taste','depth':'depth per artist',
              'intentionality':'intentional listening','discovery':'discovery rate','loyalty':'long-term loyalty'}
    total = s['total']
    if total >= 85:   verdict = "Top 1% listener globally. " + labels[strongest].capitalize() + " is your defining edge."
    elif total >= 70: verdict = "Expert listener. " + labels[strongest].capitalize() + " is exceptional. " + labels[weakest].capitalize() + " is the only gap."
    elif total >= 55: verdict = "Above average. Strong " + labels[strongest] + ". " + labels[weakest].capitalize() + " has room to grow."
    elif total >= 40: verdict = "Active listener. Your " + labels[strongest] + " sets you apart."
    else:             verdict = "Casual listener. Your strongest asset is " + labels[strongest] + "."

    st.markdown(
        "<div style='color:#444;font-size:.82em;font-style:italic;text-align:center;margin-bottom:20px;padding:0 20px;'>"
        + verdict + "</div>",
        unsafe_allow_html=True
    )
