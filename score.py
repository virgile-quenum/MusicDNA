import streamlit as st
import pandas as pd

VIOLET = "#7C3AED"
VIOLET_LIGHT = "#A78BFA"
GREEN = "#1DB954"
AMBER = "#f59e0b"
RED = "#f87171"

ARCHETYPES = {
    ("diversity", "discovery"):      ("🌍", "The Explorer",    "You go wide. Always looking for what's next. Your collection is a map of everywhere you've been."),
    ("depth", "loyalty"):            ("❤️", "The Loyalist",    "You go deep. When you find your people, you stay. Your listening history is a love story."),
    ("intentionality", "depth"):     ("🎯", "The Curator",     "Every listen is deliberate. You don't waste plays. Your library is a museum, not a feed."),
    ("discovery", "intentionality"): ("🔭", "The Tastemaker",  "You find things before anyone else, and you know exactly why. Your taste is a statement."),
    ("loyalty", "diversity"):        ("🌀", "The Collector",   "Breadth and commitment. You accumulate artists the way others accumulate experiences."),
    ("diversity", "intentionality"): ("🎨", "The Aesthete",    "You explore with purpose. Wide taste, deliberate choices. Quality over quantity, always."),
    ("depth", "discovery"):          ("🔬", "The Obsessive",   "You go deep AND you keep discovering. When you find something, you exhaust it. Then move on."),
    ("loyalty", "intentionality"):   ("🏛️", "The Devotee",    "Faithful and focused. Your artists grow with you. You don't follow trends — you outlast them."),
    ("discovery", "loyalty"):        ("🧭", "The Wanderer",    "You roam, but you remember. New sounds pull you forward. Old favourites anchor you."),
    ("diversity", "depth"):          ("🎭", "The Generalist",  "You know a lot about a lot. Genre boundaries mean nothing to you. That's a rare kind of intelligence."),
}

def _get_archetype(dims):
    top2 = tuple(sorted(dims, key=dims.get, reverse=True)[:2])
    if top2 in ARCHETYPES:
        return ARCHETYPES[top2]
    top2_rev = (top2[1], top2[0])
    if top2_rev in ARCHETYPES:
        return ARCHETYPES[top2_rev]
    return ("🎵", "The Listener", "Your listening defies easy categorization. That's the most honest thing about you.")

def compute_score(dfm):
    if dfm is None or dfm.empty:
        return None

    yr_min = int(dfm['year'].min())
    yr_max = int(dfm['year'].max())
    n_years = max(yr_max - yr_min + 1, 1)
    my_h = dfm['ms'].sum() / 3600000
    my_art = dfm['artistName'].nunique()

    art_per_100h = (my_art / my_h * 100) if my_h > 0 else 0
    diversity = round(min(art_per_100h / 120, 1.0) * 20)

    top50_hours = (
        dfm.groupby('artistName')['ms'].sum()
        .nlargest(50).mean() / 3600000
    )
    depth = round(min(top50_hours / 25, 1.0) * 20)

    skip_rate = dfm['skipped'].mean() if 'skipped' in dfm.columns else 0.20
    track_counts = dfm.groupby('trackName').size()
    repeat_rate = (track_counts > 1).sum() / max(len(track_counts), 1)
    intent_raw = (1 - skip_rate) * 0.55 + repeat_rate * 0.45
    intentionality = round(min(intent_raw / 0.75, 1.0) * 20)

    new_per_year = dfm.groupby('year')['artistName'].apply(
        lambda x: x[~x.isin(dfm[dfm['year'] < x.name]['artistName'])].nunique()
        if x.name > yr_min else x.nunique()
    ).mean()
    discovery = round(min(new_per_year / 380, 1.0) * 20)

    artist_ms    = dfm.groupby('artistName')['ms'].sum()
    artist_years = dfm.groupby('artistName')['year'].nunique()
    loyalty_weighted = (artist_years * artist_ms).sum() / max(artist_ms.sum(), 1)
    loyalty = round(min(loyalty_weighted / 5.0, 1.0) * 20)

    total = diversity + depth + intentionality + discovery + loyalty

    dims = {
        'diversity':      diversity,
        'depth':          depth,
        'intentionality': intentionality,
        'discovery':      discovery,
        'loyalty':        loyalty,
    }

    icon, archetype_name, archetype_desc = _get_archetype(dims)

    return {
        'total':          total,
        'diversity':      diversity,
        'depth':          depth,
        'intentionality': intentionality,
        'discovery':      discovery,
        'loyalty':        loyalty,
        'art_per_100h':   round(art_per_100h, 1),
        'top50_hours':    round(top50_hours, 1),
        'skip_rate':      round(skip_rate * 100, 1),
        'repeat_rate':    round(repeat_rate * 100, 1),
        'avg_new':        int(new_per_year),
        'loyalty_years':  round(loyalty_weighted, 1),
        'archetype_icon': icon,
        'archetype_name': archetype_name,
        'archetype_desc': archetype_desc,
        'dims':           dims,
    }

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
            "<div style='background:" + bar_color + ";border-radius:4px;"
            "height:7px;width:" + str(pct) + "%;'></div>"
            "</div>"
            "</div>"
        )
    return html

def render(dfm):
    s = compute_score(dfm)
    if not s:
        return

    lbl, color = score_label(s['total'])

    st.markdown(
        "<div style='background:linear-gradient(135deg,#060610,#0d0020);"
        "border:2px solid " + color + "33;border-radius:20px;"
        "padding:28px 32px;margin-bottom:6px;'>"
        "<div style='display:flex;justify-content:space-between;"
        "align-items:flex-start;flex-wrap:wrap;gap:24px;margin-bottom:20px;'>"
        "<div>"
        "<div style='font-size:.68em;color:#444;text-transform:uppercase;"
        "letter-spacing:.14em;margin-bottom:6px;'>MusicDNA Score</div>"
        "<div style='font-size:4.5em;font-weight:900;color:" + color + ";line-height:1;'>"
        + str(s['total']) + "</div>"
        "<div style='color:#555;font-size:.8em;margin-top:3px;'>/100</div>"
        "<div style='margin-top:10px;'>"
        "<span style='background:" + color + "22;color:" + color + ";"
        "font-weight:800;font-size:.82em;padding:4px 14px;border-radius:20px;'>"
        + lbl + " Listener</span>"
        "</div>"
        "</div>"
        "<div style='flex:1;min-width:220px;background:#0a0a0a;"
        "border:1px solid #1e1e1e;border-radius:14px;padding:18px;'>"
        "<div style='font-size:.68em;color:#444;text-transform:uppercase;"
        "letter-spacing:.1em;margin-bottom:8px;'>Your Archetype</div>"
        "<div style='font-size:2em;margin-bottom:4px;'>" + s['archetype_icon'] + "</div>"
        "<div style='font-size:1.1em;font-weight:900;color:#fff;margin-bottom:8px;'>"
        + s['archetype_name'] + "</div>"
        "<div style='color:#555;font-size:.8em;line-height:1.6;font-style:italic;'>"
        + s['archetype_desc'] + "</div>"
        "</div>"
        "</div>"
        "<div>" + _dim_bars(s) + "</div>"
        "</div>",
        unsafe_allow_html=True
    )

    dims = s['dims']
    strongest = max(dims, key=dims.get)
    weakest   = min(dims, key=dims.get)
    labels = {
        'diversity':      'breadth of taste',
        'depth':          'depth per artist',
        'intentionality': 'intentional listening',
        'discovery':      'discovery rate',
        'loyalty':        'long-term loyalty'
    }
    total = s['total']
    if total >= 85:
        verdict = "Top 1% listener globally. " + labels[strongest].capitalize() + " is your defining edge."
    elif total >= 70:
        verdict = "Expert listener. " + labels[strongest].capitalize() + " is exceptional. " + labels[weakest].capitalize() + " is the only gap worth closing."
    elif total >= 55:
        verdict = "Above average across the board. Strong " + labels[strongest] + ". " + labels[weakest].capitalize() + " has room to grow."
    elif total >= 40:
        verdict = "Active listener. Your " + labels[strongest] + " sets you apart from casual users."
    else:
        verdict = "Casual listener. Your strongest dimension is " + labels[strongest] + ". Everything else is upside."

    st.markdown(
        "<div style='color:#444;font-size:.82em;font-style:italic;"
        "text-align:center;margin-bottom:20px;padding:0 20px;'>"
        + verdict + "</div>",
        unsafe_allow_html=True
    )
