import streamlit as st
import pandas as pd

SIGNS = [
    {
        "name": "The Feverish Archivist",
        "fr": "L'Archiviste Fiévreux",
        "condition": lambda s: s["liked_pct"] > 40 and s["never_played_pct"] > 35,
        "curse":  "You build libraries you never open. {never_played_pct:.0f}% of your likes have never been played. You collect music like others collect books they'll never read.",
        "gift":   "When you find something, you commit. Your top track has {top_plays} plays. Your attention is total or absent — there is no middle ground.",
        "sign":   "♒",
        "prediction": "Your collection keeps growing. Your actual listening does not. One day you will open those unplayed likes. That day is not today.",
    },
    {
        "name": "The Saturday Digger",
        "fr": "Le Fouilleur du Samedi",
        "condition": lambda s: s["sat_pct"] > 18,
        "curse":  "Saturday is your temple. {sat_h:.0f}h on Saturdays alone. You do not listen through the week — you save yourself for it.",
        "gift":   "You listen with intention. Saturday listening is never background. It is a ritual.",
        "sign":   "♌",
        "prediction": "Your best discoveries happen on weekends. Your taste is formed on Saturday mornings. This will never change.",
    },
    {
        "name": "The Cultural Nomad",
        "fr": "Le Voyageur Culturel",
        "condition": lambda s: s["unique_artists"] > 5000,
        "curse":  "{unique_artists:,} artists. You cannot commit. You are always looking for the next one. The one you just found will be forgotten by Tuesday.",
        "gift":   "Your breadth is genuinely exceptional. You are not a niche listener. You are the algorithm's nightmare and dream simultaneously.",
        "sign":   "♐",
        "prediction": "You will discover {proj_new} new artists this year. You will remember 12 of them.",
    },
    {
        "name": "The Binge Listener",
        "fr": "L'Écouteur Compulsif",
        "condition": lambda s: s["binge_sessions"] > 20,
        "curse":  "{binge_sessions} sessions over 2 hours. You do not listen to music — you disappear into it. This is not a hobby. It is a coping mechanism.",
        "gift":   "You are capable of total immersion. Most people never experience music the way you do.",
        "sign":   "♏",
        "prediction": "Your next binge session is already scheduled. You just do not know it yet.",
    },
    {
        "name": "The Loyal One",
        "fr": "Le Fidèle Absolu",
        "condition": lambda s: s["top_artist_pct"] > 8,
        "curse":  "Your #1 artist alone accounts for {top_artist_pct:.0f}% of your total listening. You found something. You never left. Everyone around you has heard enough.",
        "gift":   "You go deep. Most people skim. You know every version, every live recording, every b-side. That knowledge is real.",
        "sign":   "♉",
        "prediction": "You will discover someone new who reminds you of them. You will still go back to the original.",
    },
    {
        "name": "The Infiltrated Parent",
        "fr": "Le Parent Infiltré",
        "condition": lambda s: s["kids_pct"] > 8,
        "curse":  "{kids_pct:.0f}% of your total Spotify history is children's content. Your child has colonised your account. Spotify thinks you enjoy lullabies.",
        "gift":   "You kept listening through the chaos. Even with {kids_h:.0f}h of children's music in your history, you maintained your own taste. Respect.",
        "sign":   "♋",
        "prediction": "The children's content is declining. Your account is slowly becoming yours again. By 2027 it will be fully reclaimed. Probably.",
    },
    {
        "name": "The Obsessive Early Riser",
        "fr": "Le Lève-Tôt Obsessionnel",
        "condition": lambda s: s["morning_pct"] > 15,
        "curse":  "{morning_pct:.0f}% of your listening happens before 8am. You are not using music as background. You are using it as fuel. This is either admirable or concerning.",
        "gift":   "Morning listening is your most intentional. The tracks you play at 6am are the ones that matter.",
        "sign":   "♈",
        "prediction": "Your early morning playlist will remain your most honest musical statement.",
    },
    {
        "name": "The Ghost Collector",
        "fr": "Le Collectionneur Fantôme",
        "condition": lambda s: s["skip_rate"] < 5 and s["unique_artists"] > 1000,
        "curse":  "You almost never skip. {unique_artists:,} artists and you sit through all of them. You are either extraordinarily patient or incapable of making decisions.",
        "gift":   "You give everything a chance. Your open-mindedness is statistically rare. Most people skip within 10 seconds.",
        "sign":   "♎",
        "prediction": "You will stumble onto something extraordinary by not skipping something you almost did. This happens more than you think.",
    },
]

DEFAULT_SIGN = {
    "name": "The Committed Eclectic",
    "fr": "L'Éclectique Assumé",
    "curse": "You defy categorisation. {unique_artists:,} artists across every genre and era. You are every algorithm's blind spot.",
    "gift":  "Genuine breadth is rare. Most people say they're eclectic. Your data proves it.",
    "sign":  "♊",
    "prediction": "You will continue to surprise yourself with what you play next. This is the best possible outcome.",
}

def compute_stats(dfm, dfd, lib=None):
    total_all_ms = dfm["ms"].sum() + (dfd["ms"].sum() if dfd is not None and not dfd.empty else 0)
    kids_ms      = dfd["ms"].sum() if dfd is not None and not dfd.empty else 0
    sat_ms       = dfm[dfm["dow"] == 5]["ms"].sum()
    morning_ms   = dfm[dfm["hour"].between(5, 7)]["ms"].sum()
    track_top    = dfm.groupby("trackName")["ms"].count().max() if not dfm.empty else 0

    # top artist share
    artist_ms     = dfm.groupby("artistName")["ms"].sum()
    top_artist_ms = artist_ms.max() if not artist_ms.empty else 0
    top_artist_pct = top_artist_ms / dfm["ms"].sum() * 100 if dfm["ms"].sum() > 0 else 0

    # skip rate
    skip_rate = dfm["skipped"].mean() * 100 if "skipped" in dfm.columns else 15

    # binge sessions (gaps > 30min between plays)
    df_s = dfm.sort_values("ts").copy()
    df_s["gap"] = df_s["ts"].diff().dt.total_seconds().fillna(0)
    df_s["sid"] = (df_s["gap"] > 1800).cumsum()
    sessions    = df_s.groupby("sid")["ms"].sum() / 3600000
    binge_sessions = int((sessions >= 2).sum())

    # liked / never played
    liked_pct       = 50
    never_played_pct = 45
    if lib:
        raw = lib.get("tracks", []) if isinstance(lib, dict) else lib
        if raw:
            played = set(dfm["trackName"].str.lower().str.strip())
            never  = sum(1 for t in raw
                         if str(t.get("track", t.get("trackName", ""))).lower().strip() not in played)
            liked_pct        = min(len(raw) / max(dfm["trackName"].nunique(), 1) * 100, 100)
            never_played_pct = never / len(raw) * 100 if raw else 0

    proj_new = int(dfm["artistName"].nunique() / max(dfm["year"].nunique(), 1))

    return {
        "unique_artists":   dfm["artistName"].nunique(),
        "sat_pct":          sat_ms / dfm["ms"].sum() * 100,
        "sat_h":            sat_ms / 3600000,
        "morning_pct":      morning_ms / dfm["ms"].sum() * 100,
        "kids_pct":         kids_ms / total_all_ms * 100 if total_all_ms > 0 else 0,
        "kids_h":           kids_ms / 3600000,
        "top_plays":        int(track_top),
        "top_artist_pct":   top_artist_pct,
        "skip_rate":        skip_rate,
        "binge_sessions":   binge_sessions,
        "liked_pct":        liked_pct,
        "never_played_pct": never_played_pct,
        "proj_new":         proj_new,
    }

def render(dfm, dfd=None, lib=None):
    st.title("Musical Horoscope")
    st.markdown("*Your musical sign — derived from 12 years of actual behaviour, not vibes.*")

    if dfd is None:
        dfd = pd.DataFrame()

    stats = compute_stats(dfm, dfd, lib)

    matched_sign = None
    for sign in SIGNS:
        try:
            if sign["condition"](stats):
                matched_sign = sign
                break
        except:
            pass
    if not matched_sign:
        matched_sign = DEFAULT_SIGN

    st.markdown(
        "<div style='background:linear-gradient(135deg,#0a0a2a,#0a1a0a);"
        "border:1px solid #7C3AED;border-radius:16px;padding:32px;"
        "text-align:center;margin-bottom:24px;'>"
        "<div style='font-size:4em;'>" + matched_sign.get("sign", "⭐") + "</div>"
        "<div style='font-size:1.8em;font-weight:900;color:#A78BFA;margin-top:8px;'>"
        + matched_sign["name"] + "</div>"
        "<div style='color:#555;font-size:.85em;font-style:italic;margin-top:4px;'>"
        + matched_sign.get("fr", "") + "</div>"
        "</div>",
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Your Curse")
        try:    curse = matched_sign["curse"].format(**stats)
        except: curse = matched_sign["curse"]
        st.markdown("<div class='insight'>" + curse + "</div>", unsafe_allow_html=True)

        st.markdown("### Your Gift")
        try:    gift = matched_sign["gift"].format(**stats)
        except: gift = matched_sign["gift"]
        st.markdown("<div class='insight'>" + gift + "</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("### Your Prediction")
        try:    pred = matched_sign["prediction"].format(**stats)
        except: pred = matched_sign["prediction"]
        st.markdown("<div class='insight'>" + pred + "</div>", unsafe_allow_html=True)

        st.markdown("### Your Numbers")
        rows = [
            ("Total artists",      str(stats["unique_artists"]) + " artists"),
            ("Saturday share",     str(round(stats["sat_pct"])) + "%"),
            ("Morning listening",  str(round(stats["morning_pct"])) + "%"),
            ("Skip rate",          str(round(stats["skip_rate"])) + "%"),
            ("Binge sessions",     str(stats["binge_sessions"]) + " sessions over 2h"),
            ("Top track",          str(stats["top_plays"]) + " plays"),
        ]
        if stats["kids_pct"] > 1:
            rows.append(("Children's content", str(round(stats["kids_pct"])) + "%"))
        for lbl, val in rows:
            st.markdown(
                "<div style='display:flex;justify-content:space-between;"
                "padding:5px 0;border-bottom:1px solid #222;font-size:.85em;'>"
                "<span style='color:#888;'>" + lbl + "</span>"
                "<span style='color:#fff;font-weight:700;'>" + val + "</span></div>",
                unsafe_allow_html=True
            )

    st.markdown("---")
    share = (matched_sign.get("sign", "") + " " + matched_sign["name"] +
             " — my musical sign from 12 years of Spotify data. "
             "Powered by MusicDNA. musicdna-dhalsimq.up.railway.app")
    st.markdown("**Share your sign:**")
    st.code(share)
