import streamlit as st
import pandas as pd

CELEBRITY_PROFILES = [
    {
        'name': 'Barack Obama',
        'emoji': '🇺🇸',
        'desc': 'Soul, R&B, Hip-Hop, eclectic taste, comfort with complexity',
        'markers': ['Stevie Wonder','Marvin Gaye','Kanye West','Jay-Z','Kendrick Lamar',
                    'Miles Davis','Aretha Franklin','The Roots','John Coltrane'],
        'genres': ['soul','rnb','hiphop','jazz'],
        'era_weight': {2010: 0.3, 2000: 0.2, 1970: 0.3, 1960: 0.2},
    },
    {
        'name': 'Idris Elba',
        'emoji': '🎧',
        'desc': 'Afrobeat, Dancehall, House, DJs in real life — serious digger',
        'markers': ['Burna Boy','Vybz Kartel','Capleton','P-Square','Morgan Heritage',
                    'Richie Spice','Davido','Afrobeats','Fela Kuti'],
        'genres': ['afrobeat','dancehall','reggae','afropop'],
        'era_weight': {2010: 0.4, 2000: 0.3, 1990: 0.2, 1980: 0.1},
    },
    {
        'name': 'Questlove',
        'emoji': '🥁',
        'desc': 'Deepest crate-digger alive. Soul, Funk, obscure R&B, vinyl obsessive',
        'markers': ['Terry Callier','Donny Hathaway','Millie Jackson','O.V. Wright',
                    'Ike & Tina Turner','James Brown','The Dramatics','Bobby Womack',
                    'Ann Peebles','Syl Johnson'],
        'genres': ['soul','funk','rnb','blues'],
        'era_weight': {1970: 0.5, 1960: 0.3, 1980: 0.2},
    },
    {
        'name': 'LeBron James',
        'emoji': '🏀',
        'desc': 'Hip-Hop, trap, Drake, pump-up energy, mainstream with taste',
        'markers': ['Drake','Kanye West','Jay-Z','Chris Brown','USHER','Future',
                    'The Weeknd','A$AP Rocky','Busta Rhymes'],
        'genres': ['hiphop','trap','rnb'],
        'era_weight': {2020: 0.3, 2010: 0.5, 2000: 0.2},
    },
    {
        'name': 'Quentin Tarantino',
        'emoji': '🎬',
        'desc': 'Soul, Funk, surf rock, Italian film, eclectic cinematic curation',
        'markers': ['The Beatles','Derek & The Dominos','James Brown','Ike & Tina Turner',
                    'Bobby Womack','The Staple Singers','Manu Dibango'],
        'genres': ['soul','funk','classic rock','blues'],
        'era_weight': {1970: 0.4, 1960: 0.4, 1980: 0.2},
    },
    {
        'name': 'Youssou N\'Dour',
        'emoji': '🌍',
        'desc': 'World music, African rhythms, global sounds, roots and diaspora',
        'markers': ['Manu Dibango','Ebo Taylor','Alpha Blondy','Abou Diarra',
                    'Davido','Burna Boy','P-Square','Big Nuz'],
        'genres': ['afrobeat','world','reggae','afropop'],
        'era_weight': {2010: 0.3, 2000: 0.3, 1990: 0.2, 1980: 0.2},
    },
    {
        'name': 'Virgil Abloh',
        'emoji': '🖤',
        'desc': 'Hip-Hop meets high culture. Kanye-adjacent, global streetwear taste',
        'markers': ['Kanye West','Jay-Z','Tyler, The Creator','The Weeknd',
                    'A$AP Rocky','Pharrell Williams'],
        'genres': ['hiphop','rnb','experimental'],
        'era_weight': {2020: 0.3, 2010: 0.5, 2000: 0.2},
    },
    {
        'name': 'Antoine Griezmann',
        'emoji': '⚽',
        'desc': 'French urban music, Afropop, Latin, R&B — the footballer playlist',
        'markers': ['MHD','Dadju','Burna Boy','Niska','Aya Nakamura'],
        'genres': ['afropop','french urban','latin','rnb'],
        'era_weight': {2020: 0.5, 2010: 0.5},
    },
]

def compute_match(dfm, profile):
    artist_ms = dfm.groupby('artistName')['ms'].sum()
    total_ms  = artist_ms.sum()
    score = 0.0
    matched = []
    for marker in profile['markers']:
        if marker in artist_ms.index:
            share = artist_ms[marker] / total_ms
            pts = min(share * 500, 15)
            score += pts
            matched.append(marker)
    score = min(score, 100)
    return round(score, 1), matched

def render(dfm):
    st.title("⭐ Celebrity Music Twin")
    st.markdown("*Artists whose taste most closely matches yours — based on your actual listening.*")

    results = []
    for profile in CELEBRITY_PROFILES:
        score, matched = compute_match(dfm, profile)
        results.append({**profile, 'score': score, 'matched': matched})
    results.sort(key=lambda x: -x['score'])

    # ── Top match ─────────────────────────────────────────────────────────
    top = results[0]
    st.markdown(f"""
    <div style='background:linear-gradient(135deg,#071a0e,#0a1525);border:1px solid #7C3AED;
                border-radius:16px;padding:28px;text-align:center;margin-bottom:20px;'>
      <div style='font-size:3em;'>{top['emoji']}</div>
      <div style='font-size:2em;font-weight:900;color:#A78BFA;'>{top['name']}</div>
      <div style='color:#888;margin:8px 0;'>{top['desc']}</div>
      <div style='font-size:1.4em;font-weight:700;color:#fff;margin-top:12px;'>
        {top['score']:.0f}% match</div>
      <div style='color:#555;font-size:.8em;margin-top:6px;'>
        Shared artists: {', '.join(top['matched'][:5]) or 'Style match'}</div>
    </div>""", unsafe_allow_html=True)

    # ── All matches ───────────────────────────────────────────────────────
    st.markdown("## All Profiles")
    cols = st.columns(2)
    for i, r in enumerate(results):
        with cols[i % 2]:
            bar = int(r['score']/5)
            color = '#7C3AED' if i==0 else '#A78BFA' if r['score']>30 else '#555'
            st.markdown(f"""
            <div style='background:#1a1a1a;border:1px solid #2a2a2a;border-radius:10px;
                        padding:14px;margin-bottom:10px;'>
              <div style='display:flex;justify-content:space-between;align-items:center;'>
                <span>{r['emoji']} <b>{r['name']}</b></span>
                <span style='color:{color};font-weight:800;'>{r['score']:.0f}%</span>
              </div>
              <div style='background:#222;border-radius:3px;height:5px;margin:8px 0;'>
                <div style='width:{r['score']}%;height:100%;background:{color};border-radius:3px;'></div>
              </div>
              <div style='color:#666;font-size:.78em;'>{r['desc']}</div>
              {'<div style="color:#888;font-size:.75em;margin-top:5px;">Shared: ' + ', '.join(r['matched'][:3]) + '</div>' if r['matched'] else ''}
            </div>""", unsafe_allow_html=True)

    # ── Share card ────────────────────────────────────────────────────────
    st.markdown("---")
    st.markdown("**📤 Share your twin:**")
    share = (f"My music taste matches {top['emoji']} {top['name']} at {top['score']:.0f}% "
             f"according to 12 years of Spotify data. "
             f"Shared artists: {', '.join(top['matched'][:3])}. 🎵")
    st.code(share)
