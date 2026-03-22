import streamlit as st
import pandas as pd
from collections import Counter

CELEBRITY_PROFILES = [
    {
        "name": "Barack Obama",
        "emoji": "🇺🇸",
        "desc": "Soul, R&B, Hip-Hop, eclectic taste, comfort with complexity",
        "markers": ["Stevie Wonder","Marvin Gaye","Kanye West","Jay-Z","Kendrick Lamar",
                    "Miles Davis","Aretha Franklin","The Roots","John Coltrane","Curtis Mayfield"],
        "genres": ["soul","r&b","hip hop","jazz","funk"],
        "peak_eras": [1970, 1980, 2010],
    },
    {
        "name": "Idris Elba",
        "emoji": "🎧",
        "desc": "Afrobeat, Dancehall, House — serious digger, DJ in real life",
        "markers": ["Burna Boy","Vybz Kartel","Capleton","P-Square","Morgan Heritage",
                    "Richie Spice","Davido","Fela Kuti","Wizkid","Tiwa Savage"],
        "genres": ["afrobeats","dancehall","reggae","afropop","house"],
        "peak_eras": [2010, 2000, 1990],
    },
    {
        "name": "Questlove",
        "emoji": "🥁",
        "desc": "Deepest crate-digger alive. Soul, Funk, obscure R&B, vinyl obsessive",
        "markers": ["Terry Callier","Donny Hathaway","Millie Jackson","O.V. Wright",
                    "James Brown","Bobby Womack","Ann Peebles","Syl Johnson",
                    "Gil Scott-Heron","Shuggie Otis"],
        "genres": ["soul","funk","r&b","blues","jazz"],
        "peak_eras": [1970, 1960, 1980],
    },
    {
        "name": "Youssou N'Dour",
        "emoji": "🌍",
        "desc": "World music, African rhythms, roots and diaspora — the global listener",
        "markers": ["Manu Dibango","Alpha Blondy","Davido","Burna Boy","P-Square",
                    "Big Nuz","Tiken Jah Fakoly","Salif Keita","Baaba Maal","Angelique Kidjo"],
        "genres": ["afrobeats","world","reggae","afropop","mbalax"],
        "peak_eras": [2010, 2000, 1990, 1980],
    },
    {
        "name": "Quentin Tarantino",
        "emoji": "🎬",
        "desc": "Soul, Funk, cinematic curation — nothing after 1980 if he can help it",
        "markers": ["James Brown","Ike & Tina Turner","Bobby Womack","The Beatles",
                    "Derek & The Dominos","The Staple Singers","Manu Dibango",
                    "Nancy Sinatra","Al Green"],
        "genres": ["soul","funk","classic rock","blues","r&b"],
        "peak_eras": [1970, 1960, 1950],
    },
    {
        "name": "LeBron James",
        "emoji": "🏀",
        "desc": "Hip-Hop, trap, Drake, pump-up energy — mainstream done right",
        "markers": ["Drake","Kanye West","Jay-Z","Chris Brown","Future",
                    "The Weeknd","A$AP Rocky","Lil Wayne","Meek Mill","21 Savage"],
        "genres": ["hip hop","trap","r&b","rap"],
        "peak_eras": [2020, 2010, 2000],
    },
    {
        "name": "Stromae",
        "emoji": "🇧🇪",
        "desc": "Electronic, French urban, Afropop, Congolese roots — Europe meets Africa",
        "markers": ["MHD","Aya Nakamura","Dadju","Burna Boy","Youssoupha",
                    "Gradur","Niska","Lomepal","Fally Ipupa","Maitre Gims"],
        "genres": ["french rap","afropop","electronic","r&b","congolese"],
        "peak_eras": [2020, 2010],
    },
    {
        "name": "Virgil Abloh",
        "emoji": "🖤",
        "desc": "Hip-Hop meets high culture — Kanye-adjacent, global streetwear taste",
        "markers": ["Kanye West","Jay-Z","Tyler, The Creator","The Weeknd",
                    "A$AP Rocky","Pharrell Williams","Frank Ocean","Childish Gambino"],
        "genres": ["hip hop","r&b","experimental","electronic"],
        "peak_eras": [2020, 2010],
    },
]

GENRE_NORMALIZE = {
    "afrobeat": "afrobeats", "afro": "afrobeats", "afropop": "afrobeats",
    "r&b": "r&b", "rnb": "r&b", "soul": "soul", "funk": "funk",
    "hip hop": "hip hop", "hip-hop": "hip hop", "rap": "hip hop", "trap": "hip hop",
    "jazz": "jazz", "blues": "blues", "classic rock": "classic rock",
    "dancehall": "dancehall", "reggae": "reggae",
    "world": "world", "french rap": "french rap", "electronic": "electronic",
}

def _normalize_genre(g):
    g = g.lower().strip()
    for k, v in GENRE_NORMALIZE.items():
        if k in g:
            return v
    return g

def _get_user_genres(dfm):
    """Estimate genres from artist names using simple keyword matching."""
    text = " ".join(dfm["artistName"].str.lower().unique())
    genre_signals = {
        "afrobeats":   ["burna","davido","wizkid","afrobeat","fela","p-square","psquare","tiken","gradur","youssoupha","ninho"],
        "soul":        ["terry callier","donny hathaway","marvin gaye","stevie","aretha","otis","sam cooke","al green"],
        "funk":        ["james brown","parliament","funkadelic","sly stone","bobby womack"],
        "hip hop":     ["jay-z","kanye","drake","kendrick","nas","biggie","tupac","wu-tang","lil wayne"],
        "reggae":      ["capleton","morgan heritage","richie spice","alpha blondy","buju","sizzla","damian marley"],
        "dancehall":   ["vybz kartel","dancehall","popcaan","alkaline","mavado"],
        "r&b":         ["usher","chris brown","beyonce","rihanna","the weeknd","frank ocean"],
        "jazz":        ["miles davis","coltrane","bill evans","herbie hancock","charlie parker"],
        "world":       ["youssou","manu dibango","salif keita","angelique kidjo","baaba maal"],
        "french rap":  ["mhd","aya nakamura","dadju","niska","lomepal","nekfeu","iam","ninho"],
    }
    user_genres = Counter()
    for genre, keywords in genre_signals.items():
        for kw in keywords:
            if kw in text:
                user_genres[genre] += 1
    return user_genres

def _get_user_eras(dfm):
    """Get distribution of listening years."""
    year_ms = dfm.groupby("year")["ms"].sum()
    total   = year_ms.sum()
    if total == 0:
        return {}
    decade_ms = {}
    for yr, ms in year_ms.items():
        decade = (int(yr) // 10) * 10
        decade_ms[decade] = decade_ms.get(decade, 0) + ms / total
    return decade_ms

def compute_match(dfm, profile, user_genres, user_eras):
    artist_ms = dfm.groupby("artistName")["ms"].sum()
    total_ms  = artist_ms.sum()

    # 1. Artist overlap score (50%)
    artist_score = 0.0
    matched = []
    for marker in profile["markers"]:
        if marker in artist_ms.index:
            share = artist_ms[marker] / total_ms
            pts   = min(share * 600, 12)
            artist_score += pts
            matched.append(marker)
    artist_score = min(artist_score, 50)

    # 2. Genre overlap score (30%)
    genre_score = 0.0
    profile_genres = set(profile["genres"])
    for g, count in user_genres.items():
        if g in profile_genres:
            genre_score += min(count * 5, 10)
    genre_score = min(genre_score, 30)

    # 3. Era overlap score (20%)
    era_score = 0.0
    for era in profile["peak_eras"]:
        decade = (era // 10) * 10
        era_score += user_eras.get(decade, 0) * 30
    era_score = min(era_score, 20)

    total = round(artist_score + genre_score + era_score, 1)
    return total, matched

def render(dfm):
    st.title("Celebrity Music Twin")
    st.markdown("*Who shares your musical DNA — based on artists, genres and listening eras.*")

    user_genres = _get_user_genres(dfm)
    user_eras   = _get_user_eras(dfm)

    results = []
    for profile in CELEBRITY_PROFILES:
        score, matched = compute_match(dfm, profile, user_genres, user_eras)
        results.append({**profile, "score": score, "matched": matched})
    results.sort(key=lambda x: -x["score"])

    top = results[0]

    st.markdown(
        "<div style='background:linear-gradient(135deg,#071a0e,#0a1525);"
        "border:1px solid #7C3AED;border-radius:16px;padding:28px;"
        "text-align:center;margin-bottom:20px;'>"
        "<div style='font-size:3em;'>" + top["emoji"] + "</div>"
        "<div style='font-size:2em;font-weight:900;color:#A78BFA;'>" + top["name"] + "</div>"
        "<div style='color:#888;margin:8px 0;font-size:.9em;'>" + top["desc"] + "</div>"
        "<div style='font-size:1.4em;font-weight:700;color:#fff;margin-top:12px;'>"
        + str(int(top["score"])) + "% match</div>"
        + ("<div style='color:#555;font-size:.8em;margin-top:6px;'>Shared artists: "
           + ", ".join(top["matched"][:5]) + "</div>" if top["matched"] else "") +
        "</div>",
        unsafe_allow_html=True
    )

    # score breakdown
    st.markdown(
        "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
        "border-radius:10px;padding:14px;margin-bottom:20px;'>"
        "<div style='color:#555;font-size:.75em;text-transform:uppercase;"
        "letter-spacing:.08em;margin-bottom:10px;'>How the score is calculated</div>"
        "<div style='color:#888;font-size:.82em;line-height:1.8;'>"
        "50% — shared artists weighted by listening hours<br>"
        "30% — genre overlap (afrobeats, soul, hip-hop, reggae, etc.)<br>"
        "20% — listening era alignment (which decades you spend most time in)"
        "</div>"
        "</div>",
        unsafe_allow_html=True
    )

    st.markdown("### All profiles")
    cols = st.columns(2)
    for i, r in enumerate(results):
        color = "#7C3AED" if i == 0 else "#A78BFA" if r["score"] > 30 else "#555"
        with cols[i % 2]:
            st.markdown(
                "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
                "border-radius:10px;padding:14px;margin-bottom:10px;'>"
                "<div style='display:flex;justify-content:space-between;align-items:center;'>"
                "<span style='font-weight:700;color:#fff;'>"
                + r["emoji"] + " " + r["name"] + "</span>"
                "<span style='color:" + color + ";font-weight:900;font-size:1.1em;'>"
                + str(int(r["score"])) + "%</span>"
                "</div>"
                "<div style='background:#1e1e1e;border-radius:3px;height:5px;margin:8px 0;'>"
                "<div style='width:" + str(min(int(r["score"]), 100)) + "%;"
                "height:100%;background:" + color + ";border-radius:3px;'></div>"
                "</div>"
                "<div style='color:#555;font-size:.78em;'>" + r["desc"] + "</div>"
                + ("<div style='color:#888;font-size:.75em;margin-top:5px;'>Shared: "
                   + ", ".join(r["matched"][:3]) + "</div>" if r["matched"] else "") +
                "</div>",
                unsafe_allow_html=True
            )

    st.markdown("---")
    share = (top["emoji"] + " My music taste matches " + top["name"] +
             " at " + str(int(top["score"])) + "% — "
             "based on artists, genres and listening eras from 12 years of Spotify data. "
             "musicdna-dhalsimq.up.railway.app")
    st.markdown("**Share your twin:**")
    st.code(share)
