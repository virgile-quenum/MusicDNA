import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
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
    'música para bebés','musique pour bébé','alain royer','miracle tones',
    'monde des titounis','comptines tv','arlen ness','carmen campagne',
]

def _is_kids(n): return any(k in n.lower() for k in KIDS_KW)

# ── Event detection ───────────────────────────────────────────────────────────

def _detect_binge_anomalies(df):
    monthly = df.groupby('ym')['ms'].sum() / 3600000
    avg = monthly.mean()
    std = monthly.std()
    events = []
    for ym, h in monthly.items():
        if h > avg + 1.8 * std:
            yr = int(ym[:4])
            mo = int(ym[5:7])
            month_name = pd.Timestamp(year=yr, month=mo, day=1).strftime('%B %Y')
            pct = int((h - avg) / avg * 100)
            top3 = (df[df['ym'] == ym]
                    .groupby('artistName')['ms'].sum()
                    .nlargest(3).index.tolist())
            top3_str = ", ".join(top3[:2])
            events.append({
                'date': ym, 'year': yr, 'type': 'binge',
                'color': VIOLET_LIGHT, 'icon': '🌊',
                'title': month_name + " — " + str(int(h)) + "h",
                'body': (
                    str(int(h)) + "h in a single month. Your average is " + str(int(avg)) + "h. "
                    "That is " + str(pct) + "% above normal. "
                    "Mostly " + top3_str + ". "
                    "Something created that much space for music."
                ),
                'intensity': h / avg,
            })
    return sorted(events, key=lambda x: -x['intensity'])[:4]

def _detect_silence(df):
    monthly = df.groupby('ym')['ms'].sum() / 3600000
    avg = monthly.mean()
    std = monthly.std()
    events = []
    low_months = monthly[monthly < avg - std]
    if len(low_months) == 0:
        return events
    periods = []
    current = []
    all_months = sorted(monthly.index.tolist())
    for ym in all_months:
        if ym in low_months.index:
            current.append(ym)
        else:
            if len(current) >= 2:
                periods.append(current)
            current = []
    if len(current) >= 2:
        periods.append(current)
    for period in periods[:2]:
        yr = int(period[0][:4])
        total_h = sum(monthly.get(m, 0) for m in period)
        avg_h_period = total_h / len(period)
        drop_pct = int((avg - avg_h_period) / avg * 100)
        events.append({
            'date': period[0], 'year': yr, 'type': 'silence',
            'color': '#888', 'icon': '🔇',
            'title': period[0][:7] + " to " + period[-1][:7] + " — silence",
            'body': (
                str(int(avg_h_period)) + "h/month over " + str(len(period)) + " months. "
                "Your average is " + str(int(avg)) + "h. "
                "A " + str(drop_pct) + "% drop. "
                "Music went quiet. Something else took the space."
            ),
            'intensity': drop_pct / 100,
        })
    return events

def _detect_artist_abandonment(df):
    df_c = df[~df['artistName'].apply(_is_kids)]
    yr_max = int(df_c['year'].max())
    artist_years = df_c.groupby('artistName')['year'].agg(['min','max'])
    artist_h = df_c.groupby('artistName')['ms'].sum() / 3600000
    events = []
    for artist, row in artist_years.iterrows():
        h = artist_h.get(artist, 0)
        if h < 8: continue
        last_yr = int(row['max'])
        if yr_max - last_yr >= 2:
            peak_yr = int(df_c[df_c['artistName'] == artist]
                          .groupby('year')['ms'].sum().idxmax())
            events.append({
                'date': str(last_yr) + '-06', 'year': last_yr,
                'type': 'abandonment', 'color': AMBER, 'icon': '👋',
                'title': artist + " — last heard " + str(last_yr),
                'body': (
                    str(int(h)) + " hours with " + artist + ". "
                    "Peak in " + str(peak_yr) + ". "
                    "Then silence. "
                    "Some artists stay attached to a specific time. "
                    "You could not go back."
                ),
                'intensity': h / 10,
            })
    return sorted(events, key=lambda x: -x['intensity'])[:3]

def _detect_repeat_obsessions(df):
    df_s = df.sort_values('ts')
    events = []
    checked = set()
    for (track, artist), grp in df_s.groupby(['trackName','artistName']):
        if len(grp) < 15: continue
        if artist in checked: continue
        grp = grp.sort_values('ts')
        for i in range(len(grp)):
            window_end = grp['ts'].iloc[i] + pd.Timedelta(days=30)
            window = grp[(grp['ts'] >= grp['ts'].iloc[i]) & (grp['ts'] <= window_end)]
            if len(window) >= 15:
                ym = grp['ts'].iloc[i].strftime('%Y-%m')
                yr = int(ym[:4])
                period = grp['ts'].iloc[i].strftime('%B %Y')
                events.append({
                    'date': ym, 'year': yr,
                    'type': 'obsession', 'color': RED, 'icon': '🔁',
                    'title': '"' + track + '" — ' + str(len(window)) + "x in 30 days",
                    'body': (
                        str(len(window)) + " times in a single month. "
                        + period + ". "
                        "That is not listening — that is searching. "
                        "You were looking for something in this song. "
                        "Only you know if you found it."
                    ),
                    'intensity': len(window) / 20,
                })
                checked.add(artist)
                break
    return sorted(events, key=lambda x: -x['intensity'])[:5]

def _detect_time_shift(df):
    events = []
    yearly_peak = {}
    for yr in sorted(df['year'].unique()):
        grp = df[df['year'] == yr]
        if len(grp) < 200: continue
        peak = int(grp.groupby('hour')['ms'].sum().idxmax())
        yearly_peak[yr] = peak
    years = sorted(yearly_peak.keys())
    for i in range(2, len(years)):
        prev2    = [yearly_peak[years[i-2]], yearly_peak[years[i-1]]]
        curr     = yearly_peak[years[i]]
        avg_prev = sum(prev2) / 2
        if abs(curr - avg_prev) >= 4:
            direction = "earlier" if curr < avg_prev else "later"
            events.append({
                'date': str(years[i]) + '-01', 'year': years[i],
                'type': 'timeshift', 'color': BLUE, 'icon': '🕐',
                'title': str(years[i]) + " — peak moved to " + str(curr).zfill(2) + "h",
                'body': (
                    "Your peak listening hour shifted from " + str(int(avg_prev)).zfill(2) + "h "
                    "to " + str(curr).zfill(2) + "h. "
                    "That is " + str(abs(int(curr - avg_prev))) + " hours " + direction + ". "
                    "A shift this large means your daily rhythm changed. "
                    "Something reorganised your life."
                ),
                'intensity': abs(curr - avg_prev) / 4,
            })
    return events[:2]

def _detect_style_shift(df):
    df_c = df[~df['artistName'].apply(_is_kids)]
    events = []
    prev_top = None
    for yr in sorted(df_c['year'].unique()):
        grp = df_c[df_c['year'] == yr]
        if grp['ms'].sum() < 50_000_000: continue
        top      = grp.groupby('artistName')['ms'].sum().nlargest(1)
        curr_top = top.index[0]
        curr_h   = round(top.iloc[0] / 3600000, 0)
        if prev_top and curr_top != prev_top:
            prev_h = round(
                df_c[(df_c['year'] == yr-1) & (df_c['artistName'] == prev_top)]['ms'].sum() / 3600000, 0
            )
            if curr_h > 10 and prev_h > 5:
                events.append({
                    'date': str(yr) + '-01', 'year': yr,
                    'type': 'styleshift', 'color': GREEN, 'icon': '🎵',
                    'title': str(yr) + " — " + curr_top + " takes over",
                    'body': (
                        curr_top + " becomes your #1 artist. "
                        + str(int(curr_h)) + "h this year. "
                        "The year before it was " + str(prev_top) + ". "
                        "A new sound entered your life — or an old one disappeared."
                    ),
                    'intensity': curr_h / 20,
                })
        prev_top = curr_top
    return events[:3]

def _detect_parenthood(df, dfd):
    if dfd is None or dfd.empty: return []
    if 'ym' not in dfd.columns: return []
    kids_monthly = dfd.groupby('ym')['ms'].sum() / 3600000
    if kids_monthly.empty: return []
    first_month = kids_monthly[kids_monthly > 1].index.min()
    if not first_month: return []
    yr = int(first_month[:4])
    mo = int(first_month[5:7])
    month_name   = pd.Timestamp(year=yr, month=mo, day=1).strftime('%B %Y')
    total_kids_h = round(kids_monthly.sum())
    peak_ym = kids_monthly.idxmax()
    peak_h  = round(kids_monthly.max())
    peak_mo = pd.Timestamp(year=int(peak_ym[:4]), month=int(peak_ym[5:7]), day=1).strftime('%B %Y')
    return [{
        'date': first_month, 'year': yr,
        'type': 'parenthood', 'color': '#f472b6', 'icon': '👶',
        'title': month_name + " — everything changed",
        'body': (
            "The first children's tracks appeared in " + month_name + ". "
            + str(total_kids_h) + " hours of children's content followed. "
            "Peak in " + peak_mo + " at " + str(int(peak_h)) + "h/month. "
            "Your listening didn't stop — it split in two."
        ),
        'intensity': 5,
    }]

# ── Timeline HTML verticale ───────────────────────────────────────────────────

def _render_timeline_html(events_sorted, df):
    """Vertical HTML timeline — replaces the unreadable Plotly version."""
    yearly = df.groupby('year')['ms'].sum() / 3600000
    yearly_dict = dict(yearly)

    type_labels = {
        'binge':       ('🌊', 'Binge',       VIOLET_LIGHT),
        'silence':     ('🔇', 'Silence',     '#888'),
        'obsession':   ('🔁', 'Obsession',   RED),
        'abandonment': ('👋', 'Abandonment', AMBER),
        'timeshift':   ('🕐', 'Time shift',  BLUE),
        'styleshift':  ('🎵', 'Style shift', GREEN),
        'parenthood':  ('👶', 'Parenthood',  '#f472b6'),
    }

    # Group events by year
    by_year = defaultdict(list)
    for e in events_sorted:
        by_year[e['year']].append(e)

    all_years = sorted(set(list(yearly_dict.keys()) + list(by_year.keys())))

    html = "<div style='position:relative;padding-left:0;'>"

    for yr in sorted(all_years, reverse=True):
        h = yearly_dict.get(yr, 0)
        evs = by_year.get(yr, [])

        # Year row
        bar_w = min(int(h / 20), 100)  # scale: 2000h = 100%
        bar_color = VIOLET if evs else '#1e1e1e'

        html += (
            "<div style='display:flex;align-items:flex-start;gap:12px;"
            "margin-bottom:" + ("4px" if not evs else "0") + ";'>"
            # Year label
            "<div style='min-width:40px;font-size:.85em;font-weight:900;"
            "color:" + ("#fff" if evs else "#444") + ";padding-top:2px;'>"
            + str(yr) + "</div>"
            # Bar
            "<div style='flex:1;padding-top:6px;'>"
            "<div style='background:#111;border-radius:3px;height:6px;'>"
            "<div style='background:" + bar_color + ";width:" + str(bar_w) + "%;"
            "height:6px;border-radius:3px;'></div>"
            "</div>"
            "<div style='color:#555;font-size:.72em;margin-top:2px;'>" + str(int(h)) + "h</div>"
            "</div>"
            "</div>"
        )

        # Event cards for this year
        for e in evs:
            icon, label, color = type_labels.get(e['type'], ('•', e['type'], '#888'))
            html += (
                "<div style='display:flex;gap:12px;margin:6px 0 10px 52px;'>"
                "<div style='width:3px;background:" + color + ";border-radius:3px;"
                "flex-shrink:0;'></div>"
                "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
                "border-radius:8px;padding:12px 14px;flex:1;'>"
                "<div style='display:flex;align-items:center;gap:6px;margin-bottom:6px;'>"
                "<span style='font-size:1em;'>" + icon + "</span>"
                "<span style='font-size:.75em;font-weight:700;color:" + color + ";'>"
                + label.upper() + "</span>"
                "<span style='font-size:.78em;color:#ccc;font-weight:600;'>"
                + e['title'] + "</span>"
                "</div>"
                "<div style='color:#888;font-size:.8em;line-height:1.6;'>"
                + e['body'] + "</div>"
                "</div></div>"
            )

    html += "</div>"
    st.markdown(html, unsafe_allow_html=True)

# ── Main render ───────────────────────────────────────────────────────────────

def render(dfm, dfd=None):
    st.markdown(
        "<span style='color:#A78BFA;font-size:.75em;font-weight:700;"
        "text-transform:uppercase;letter-spacing:.1em;'>12 years observed</span>",
        unsafe_allow_html=True
    )
    st.title("The Witness")
    st.markdown(
        "<div style='color:#888;font-size:.88em;font-style:italic;margin-bottom:20px;'>"
        "The Witness doesn't know what happened in your life. "
        "It only knows what you played, when, and how many times."
        "</div>",
        unsafe_allow_html=True
    )

    if dfm is None or dfm.empty:
        st.warning("Upload your Extended History zip to enable this analysis.")
        return

    if dfd is None: dfd = pd.DataFrame()

    with st.spinner("Analysing signals..."):
        events  = []
        events += _detect_binge_anomalies(dfm)
        events += _detect_silence(dfm)
        events += _detect_repeat_obsessions(dfm)
        events += _detect_artist_abandonment(dfm)
        events += _detect_time_shift(dfm)
        events += _detect_style_shift(dfm)
        events += _detect_parenthood(dfm, dfd)
        events_sorted = sorted(events, key=lambda x: x['date'])

    # ── Timeline HTML ─────────────────────────────────────────────────────
    st.markdown("### The Timeline")
    st.caption("Each year with a detected signal is expanded. Bars = listening volume.")
    _render_timeline_html(events_sorted, dfm)

    st.markdown("---")

    # ── Your Sound per year ───────────────────────────────────────────────
    st.markdown("### Your Sound — #1 Artist Per Year")
    df_c = dfm[~dfm['artistName'].apply(_is_kids)]
    era_rows = []
    for yr, grp in df_c.groupby('year'):
        if grp['ms'].sum() < 20_000_000: continue
        top        = grp.groupby('artistName')['ms'].sum()
        top_artist = top.idxmax()
        top_h      = round(top.max() / 3600000, 0)
        total_h    = round(grp['ms'].sum() / 3600000, 0)
        era_rows.append({'year': yr, 'artist': top_artist,
                         'hours': top_h, 'total': total_h})

    era_df = pd.DataFrame(era_rows).sort_values('year', ascending=False)
    for _, row in era_df.iterrows():
        pct   = round(row['hours'] / row['total'] * 100) if row['total'] > 0 else 0
        bar_w = min(pct * 3, 100)
        st.markdown(
            "<div style='display:flex;align-items:center;gap:12px;"
            "padding:7px 0;border-bottom:1px solid #1a1a1a;'>"
            "<span style='font-size:.8em;color:#555;min-width:36px;'>"
            + str(int(row['year'])) + "</span>"
            "<div style='flex:1;'>"
            "<div style='font-size:.85em;color:#fff;font-weight:600;margin-bottom:3px;'>"
            + str(row['artist']) + "</div>"
            "<div style='background:#1a1a1a;border-radius:3px;height:4px;'>"
            "<div style='background:" + VIOLET_LIGHT + ";width:" + str(bar_w) + "%;"
            "height:4px;border-radius:3px;'></div>"
            "</div></div>"
            "<span style='font-size:.78em;color:#555;min-width:60px;text-align:right;'>"
            + str(int(row['hours'])) + "h (" + str(pct) + "%)</span>"
            "</div>",
            unsafe_allow_html=True
        )

    st.markdown("---")

    # ── The Full Picture ──────────────────────────────────────────────────
    st.markdown("### The Full Picture")
    df_c2      = dfm[~dfm['artistName'].apply(_is_kids)]
    yr_min     = int(dfm['year'].min())
    yr_max     = int(dfm['year'].max())
    total_h    = round(df_c2['ms'].sum() / 3600000)
    top_artist = df_c2.groupby('artistName')['ms'].sum().idxmax()
    top_h      = round(df_c2.groupby('artistName')['ms'].sum().max() / 3600000)

    obsessions = [e for e in events if e['type'] == 'obsession']
    parenthood = [e for e in events if e['type'] == 'parenthood']
    silence_ev = [e for e in events if e['type'] == 'silence']
    binges     = [e for e in events if e['type'] == 'binge']

    sentences = []
    sentences.append(
        str(yr_max - yr_min + 1) + " years. " + str(total_h) + " hours of music "
        "that The Witness recorded without judgment."
    )
    sentences.append(
        top_artist + " is your anchor — " + str(top_h) + "h total. "
        "Not a phase. A relationship."
    )
    if obsessions:
        o = obsessions[0]
        title_parts = o['title'].split(' — ')
        track_name  = title_parts[0]
        play_count  = title_parts[1].split(' ')[0] if len(title_parts) > 1 else "dozens of"
        sentences.append(
            "There were moments of obsession — "
            + track_name + " played "
            + play_count + " times in a month. "
            "That is not listening. That is something else."
        )
    if parenthood:
        sentences.append(
            "In " + str(parenthood[0]['year']) + ", the data split in two. "
            "Your music did not disappear — it made room."
        )
    if silence_ev:
        sentences.append(
            "There were periods of near-silence. "
            "Months where music barely existed. "
            "Something was louder."
        )
    if binges:
        b = max(binges, key=lambda x: x['intensity'])
        sentences.append(
            "And there were the binges — " + b['title'] + ". "
            "Music as refuge. Music as the only thing that made sense."
        )
    sentences.append(
        "The Witness does not know what happened. "
        "It only knows what you played."
    )

    st.markdown(
        "<div style='background:#0a0a0a;border:1px solid #1e1e1e;"
        "border-radius:14px;padding:24px;line-height:2.2;'>"
        + " ".join([
            "<span style='color:#aaa;font-size:.9em;'>" + s + " </span>"
            for s in sentences
        ]) +
        "</div>",
        unsafe_allow_html=True
    )
