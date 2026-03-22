import streamlit as st
import pandas as pd

VIOLET = "#7C3AED"
VIOLET_LIGHT = "#A78BFA"
GREEN = "#1DB954"

def compute_score(dfm):
    if dfm is None or dfm.empty:
        return None

    yr_min = int(dfm['year'].min())
    yr_max = int(dfm['year'].max())
    n_years = max(yr_max - yr_min + 1, 1)
    my_h = dfm['ms'].sum() / 3600000
    my_art = dfm['artistName'].nunique()
    skip = dfm['skipped'].mean() * 100 if 'skipped' in dfm.columns else 20

    art_per_100h = (my_art / my_h * 100) if my_h > 0 else 0
    diversity = round(min(art_per_100h / 150, 1.0) * 20)

    top50_hours = (
        dfm.groupby('artistName')['ms'].sum()
        .nlargest(50).mean() / 3600000
    )
    depth = round(min(top50_hours / 30, 1.0) * 20)

    intent_raw = max(0, min((30 - skip) / 30, 1.0))
    intentionality = round(intent_raw * 20)

    new_per_year_s = dfm.sort_values('ts').groupby('artistName')['year'].min()
    avg_new = new_per_year_s.groupby(new_per_year_s).size().mean()
    discovery = round(min(avg_new / 400, 1.0) * 20)

    artist_years = dfm.groupby('artistName')['year'].nunique()
    loyal_pct = (artist_years >= 3).sum() / max(len(artist_years), 1) * 100
    loyalty = round(min(loyal_pct / 35, 1.0) * 20)

    total = diversity + depth + intentionality + discovery + loyalty

    return {
        'total': total,
        'diversity':      diversity,
        'depth':          depth,
        'intentionality': intentionality,
        'discovery':      discovery,
        'loyalty':        loyalty,
        'art_per_100h':   round(art_per_100h, 1),
        'top50_hours':    round(top50_hours, 1),
        'skip_rate':      round(skip, 1),
        'avg_new':        int(avg_new),
        'loyal_pct':      round(loyal_pct, 1),
    }

def score_label(total):
    if total >= 85: return "Legendary", "#1DB954"
    if total >= 70: return "Expert",    "#A78BFA"
    if total >= 55: return "Advanced",  "#A78BFA"
    if total >= 40: return "Active",    "#f59e0b"
    return "Casual", "#888"

def _dim_bars(s):
    dims = [
        ("Diversity",      s['diversity'],      "🌍", str(s['art_per_100h']) + " artists/100h"),
        ("Depth",          s['depth'],          "🔬", str(s['top50_hours']) + "h avg on top artists"),
        ("Intentionality", s['intentionality'], "🎯", str(s['skip_rate']) + "% skip rate"),
        ("Discovery",      s['discovery'],      "🔭", str(s['avg_new']) + " new artists/year"),
        ("Loyalty",        s['loyalty'],        "❤️",  str(s['loyal_pct']) + "% artists 3+ years"),
    ]
    html = ""
    for name, val, icon, detail in dims:
        pct = int(val / 20 * 100)
        bar_color = "#1DB954" if pct >= 80 else "#A78BFA" if pct >= 50 else "#f59e0b" if pct >= 30 else "#555"
        html += (
            "<div style='margin-bottom:10px;'>"
            "<div style='display:flex;justify-content:space-between;margin-bottom:3px;'>"
            "<span style='font-size:.78em;color:#aaa;'>" + icon + " " + name + "</span>"
            "<span style='font-size:.75em;color:#555;'>" + detail + "</span>"
            "</div>"
            "<div style='background:#1a1a1a;border-radius:4px;height:6px;'>"
            "<div style='background:" + bar_color + ";border-radius:4px;"
            "height:6px;width:" + str(pct) + "%;'></div>"
            "</div>"
            "</div>"
        )
    return html

def _verdict(s):
    dims = {
        'diversity': s['diversity'], 'depth': s['depth'],
        'intentionality': s['intentionality'], 'discovery': s['discovery'],
        'loyalty': s['loyalty']
    }
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
        return "You are in the top 1% of listeners globally. " + labels[strongest].capitalize() + " is your defining trait."
    if total >= 70:
        return "Expert listener. Your " + labels[strongest] + " is exceptional. " + labels[weakest].capitalize() + " is the only gap."
    if total >= 55:
        return "Above average across the board. Strong on " + labels[strongest] + ", room to grow on " + labels[weakest] + "."
    if total >= 40:
        return "Active listener with a clear identity. Your " + labels[strongest] + " sets you apart."
    return "Casual listener. Your " + labels[strongest] + " is your best asset. Start there."

def render(dfm):
    s = compute_score(dfm)
    if not s:
        return

    lbl, color = score_label(s['total'])

    st.markdown(
        "<div style='background:linear-gradient(135deg,#0a0a0a,#0d0020);"
        "border:2px solid " + color + "44;border-radius:20px;"
        "padding:32px;margin-bottom:8px;'>"
        "<div style='display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:20px;'>"
        "<div>"
        "<div style='font-size:.72em;color:#555;text-transform:uppercase;"
        "letter-spacing:.12em;margin-bottom:4px;'>MusicDNA Listener Score</div>"
        "<div style='font-size:5em;font-weight:900;color:" + color + ";line-height:1;'>"
        + str(s['total']) + "</div>"
        "<div style='font-size:1em;color:#888;margin-top:4px;'>/100</div>"
        "<div style='margin-top:10px;'>"
        "<span style='background:" + color + "22;color:" + color + ";"
        "font-weight:800;font-size:.85em;padding:4px 14px;border-radius:20px;'>"
        + lbl + " Listener</span>"
        "</div>"
        "</div>"
        "<div style='flex:1;min-width:260px;'>" + _dim_bars(s) + "</div>"
        "</div>"
        "</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<div style='color:#555;font-size:.85em;font-style:italic;"
        "text-align:center;margin-bottom:24px;'>" + _verdict(s) + "</div>",
        unsafe_allow_html=True
    )
