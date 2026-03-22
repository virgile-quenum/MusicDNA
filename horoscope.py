import streamlit as st
import pandas as pd

VIOLET       = "#7C3AED"
VIOLET_LIGHT = "#A78BFA"
GREEN        = "#1DB954"
AMBER        = "#f59e0b"
RED          = "#f87171"

SIGNS = [
    {
        "name":  "The Feverish Archivist",
        "emoji": "📚",
        "sign":  "♒",
        "condition": lambda s: s["liked_pct"] > 40 and s["never_played_pct"] > 35,
        "curse":      "You build libraries you never open. {never_played_pct:.0f}% of your likes have never been played. You collect music the way others collect books they intend to read. The shelf looks impressive. It is mostly decorative.",
        "gift":       "When you do commit, it is total. Your top track has {top_plays} plays. Your attention is binary — complete or absent. There is no casual listening in your world.",
        "prediction": "Your collection keeps growing. Your actual listening does not. One day you will open those unplayed likes. That day is not today.",
        "data_line":  "You have liked {liked_n} tracks. {never_played_pct:.0f}% have never been played.",
    },
    {
        "name":  "The Saturday Digger",
        "emoji": "🕯️",
        "sign":  "♌",
        "condition": lambda s: s["sat_pct"] > 18,
        "curse":      "Saturday is your temple. {sat_h:.0f} hours on Saturdays alone across your history. You do not really listen through the week — you queue things up and save yourself for it. This is either discipline or avoidance.",
        "gift":       "Saturday listening is never background. It is a ritual. The tracks you choose on Saturday mornings are the ones that actually matter to you.",
        "prediction": "Your best discoveries happen on weekends. Your taste is formed on Saturday mornings. This will not change.",
        "data_line":  "{sat_pct:.0f}% of your total listening happens on Saturdays.",
    },
    {
        "name":  "The Cultural Nomad",
        "emoji": "🌍",
        "sign":  "♐",
        "condition": lambda s: s["unique_artists"] > 5000,
        "curse":      "{unique_artists:,} artists. You cannot commit. You are always looking for the next one. The artist you discovered last Tuesday is already background noise.",
        "gift":       "Your breadth is genuinely exceptional. You are not a niche listener. You are the algorithm's nightmare and dream simultaneously. No one can predict what you play next.",
        "prediction": "You will discover approximately {proj_new} new artists this year. You will remember about 15 of them.",
        "data_line":  "{unique_artists:,} unique artists across {n_years} years. That is {art_per_year:.0f} per year.",
    },
    {
        "name":  "The Binge Listener",
        "emoji": "🌀",
        "sign":  "♏",
        "condition": lambda s: s["binge_sessions"] > 20,
        "curse":      "{binge_sessions} sessions over 2 hours in your history. You do not listen to music — you disappear into it. This is not a hobby. It is a pressure valve.",
        "gift":       "You are capable of total immersion. Most people never experience music the way you do. Your longest sessions are probably your best memories.",
        "prediction": "Your next binge session is already scheduled. You just do not know it yet. Something will trigger it.",
        "data_line":  "{binge_sessions} sessions over 2h. Your peak listening year was {peak_year}.",
    },
    {
        "name":  "The Loyal One",
        "emoji": "❤️",
        "sign":  "♉",
        "condition": lambda s: s["top_artist_pct"] > 8,
        "curse":      "Your #1 artist accounts for {top_artist_pct:.0f}% of your total listening. {top_artist_h:.0f} hours on one artist. You found something. You never left. Everyone around you has heard enough.",
        "gift":       "You go deep where others skim. You know every version, every live recording, every b-side. That knowledge is real and irreplaceable.",
        "prediction": "You will discover someone new who reminds you of them. You will still go back to the original within 48 hours.",
        "data_line":  "Your #1 artist: {top_artist}. {top_artist_h:.0f}h total — {top_artist_pct:.0f}% of your life.",
    },
    {
        "name":  "The Infiltrated Parent",
        "emoji": "👶",
        "sign":  "♋",
        "condition": lambda s: s["kids_pct"] > 8,
        "curse":      "{kids_pct:.0f}% of your total Spotify history is children's content. {kids_h:.0f} hours of it. Your child has colonised your account. Spotify's algorithm is deeply confused about you.",
        "gift":       "You kept listening through the chaos. Even with {kids_h:.0f}h of children's music, you maintained your own taste. That is harder than it sounds.",
        "prediction": "The children's content is declining. Your account is slowly becoming yours again. Full reclamation estimated by 2027. Probably.",
        "data_line":  "{kids_h:.0f}h of children's content. Peak infiltration: {kids_peak_year}.",
    },
    {
        "name":  "The Ghost Collector",
        "emoji": "👻",
        "sign":  "♎",
        "condition": lambda s: s["skip_rate"] < 5 and s["unique_artists"] > 1000,
        "curse":      "You almost never skip. {unique_artists:,} artists and you sit through all of them. {skip_rate:.0f}% skip rate. You are either extraordinarily patient or constitutionally incapable of making decisions.",
        "gift":       "You give everything a real chance. Your open-mindedness is statistically rare. You have stumbled onto things others would have skipped past in 8 seconds.",
        "prediction": "You will find something extraordinary by not skipping something you almost did. This happens more than you think.",
        "data_line":  "{skip_rate:.0f}% skip rate. You completed {completion_pct:.0f}% of tracks you started.",
    },
    {
        "name":  "The Obsessive Early Riser",
        "emoji": "🌅",
        "sign":  "♈",
        "condition": lambda s: s["morning_pct"] > 15,
        "curse":      "{morning_pct:.0f}% of your listening happens before 8am. You are not using music as background. You are using it as ignition. This is either a superpower or a sign of insomnia.",
        "gift":       "Morning listening is your most intentional. The tracks you play at 6am are the ones that actually matter. Everything after noon is maintenance.",
        "prediction": "Your early morning playlist will remain your most honest musical statement. What you play at 6am is who you really are.",
        "data_line":  "{morning_pct:.0f}% of listening before 8am. Peak hour: {peak_hour:02d}h.",
    },
    {
        "name":  "The Night Shift",
        "emoji": "🌙",
        "sign":  "♓",
        "condition": lambda s: s["night_pct"] > 20,
        "curse":      "{night_pct:.0f}% of your listening happens after 10pm. You are not a daytime listener. You are building the soundtrack to the version of yourself that only exists after midnight.",
        "gift":       "Late night listening is unfiltered. No performance, no context. What you play alone at 1am is your most authentic musical self.",
        "prediction": "Your night listening will intensify before it improves. Something is unresolved. Music knows before you do.",
        "data_line":  "{night_pct:.0f}% of listening after 10pm. {night_h:.0f}h in the dark.",
    },
    {
        "name":  "The Decade Devotee",
        "emoji": "⏳",
        "sign":  "♑",
        "condition": lambda s: s["old_music_pct"] > 40,
        "curse":      "{old_music_pct:.0f}% of your listening is artists you first discovered over 5 years ago. You are not looking for new music. You are maintaining a relationship with the past.",
        "gift":       "You know what you love. The artists that survived 5 years with you are the real ones. Everything else was experimentation.",
        "prediction": "You will discover someone new this year who will join the permanent collection. It will remind you of something from {oldest_year}.",
        "data_line":  "{old_music_pct:.0f}% of plays from artists discovered 5+ years ago.",
    },
    {
        "name":  "The Shuffle Addict",
        "emoji": "🎲",
        "sign":  "♊",
        "condition": lambda s: s["shuffle_pct"] > 60,
        "curse":      "{shuffle_pct:.0f}% of your listening is on shuffle. You have {unique_artists:,} artists but you let the algorithm decide. You built the library. You outsourced the curation.",
        "gift":       "Shuffle listening keeps you open to surprise. Your accidental discoveries are probably more interesting than your intentional ones.",
        "prediction": "Your next favourite track will come from a shuffle play you almost skipped. Pay attention.",
        "data_line":  "{shuffle_pct:.0f}% shuffle rate across {total_plays:,} plays.",
    },
    {
        "name":  "The Depth Diver",
        "emoji": "🔬",
        "sign":  "♍",
        "condition": lambda s: s["tracks_per_artist"] < 2.5 and s["unique_artists"] > 2000,
        "curse":      "{unique_artists:,} artists but only {tracks_per_artist:.1f} tracks per artist on average. You taste everything and commit to nothing. Your library is a museum of first impressions.",
        "gift":       "You have more genuine discoveries than anyone. Your breadth of taste is not a deficiency — it is a different kind of depth.",
        "prediction": "You will find an artist this year that breaks your pattern. You will listen to their entire catalogue. It will feel unfamiliar and right.",
        "data_line":  "{tracks_per_artist:.1f} avg tracks per artist across {unique_artists:,} artists.",
    },
]

DEFAULT_SIGN = {
    "name":  "The Committed Eclectic",
    "emoji": "🎭",
    "sign":  "✦",
    "curse":      "You defy categorisation. {unique_artists:,} artists across every genre and era. You are every algorithm's blind spot. No recommendation engine has a model for you.",
    "gift":       "Genuine breadth is rare. Most people say they are eclectic. Your data proves it across {n_years} years.",
    "prediction": "You will continue to surprise yourself with what you play next. This is the best possible outcome.",
    "data_line":  "{unique_artists:,} artists · {n_years} years · no clear pattern.",
}

def compute_stats(dfm, dfd, lib=None):
    total_ms     = dfm["ms"].sum()
    total_all_ms = total_ms + (dfd["ms"].sum() if dfd is not None and not dfd.empty else 0)
    kids_ms      = dfd["ms"].sum() if dfd is not None and not dfd.empty else 0
    sat_ms       = dfm[dfm["dow"] == 5]["ms"].sum()
    morning_ms   = dfm[dfm["hour"].between(5, 7)]["ms"].sum()
    night_ms     = dfm[dfm["hour"] >= 22]["ms"].sum()

    yr_min    = int(dfm["year"].min())
    yr_max    = int(dfm["year"].max())
    n_years   = max(yr_max - yr_min + 1, 1)
    unique_art = dfm["artistName"].nunique()

    artist_ms     = dfm.groupby("artistName")["ms"].sum()
    top_artist    = artist_ms.idxmax() if not artist_ms.empty else "—"
    top_artist_ms = artist_ms.max() if not artist_ms.empty else 0
    top_artist_pct = top_artist_ms / total_ms * 100 if total_ms > 0 else 0
    top_artist_h   = top_artist_ms / 3600000

    track_top  = dfm.groupby("trackName")["ms"].count().max() if not dfm.empty else 0
    yearly     = dfm.groupby("year")["ms"].sum()
    peak_year  = int(yearly.idxmax()) if not yearly.empty else yr_max
    skip_rate  = dfm["skipped"].mean() * 100 if "skipped" in dfm.columns else 15
    completion_pct = 100 - skip_rate

    df_s = dfm.sort_values("ts").copy()
    df_s["gap"] = df_s["ts"].diff().dt.total_seconds().fillna(0)
    df_s["sid"] = (df_s["gap"] > 1800).cumsum()
    sessions       = df_s.groupby("sid")["ms"].sum() / 3600000
    binge_sessions = int((sessions >= 2).sum())

    shuffle_pct = dfm["shuffle"].mean() * 100 if "shuffle" in dfm.columns else 0

    liked_pct = never_played_pct = liked_n = 0
    if lib:
        raw = lib.get("tracks", []) if isinstance(lib, dict) else lib
        if raw:
            liked_n  = len(raw)
            played   = set(dfm["trackName"].str.lower().str.strip())
            never    = sum(1 for t in raw
                           if str(t.get("track", t.get("trackName", ""))).lower().strip() not in played)
            liked_pct        = min(liked_n / max(dfm["trackName"].nunique(), 1) * 100, 100)
            never_played_pct = never / liked_n * 100 if liked_n > 0 else 0

    first_seen    = dfm.groupby("artistName")["year"].min()
    old_artists   = set(first_seen[first_seen <= yr_max - 5].index)
    old_plays     = dfm[dfm["artistName"].isin(old_artists)]["ms"].sum()
    old_music_pct = old_plays / total_ms * 100 if total_ms > 0 else 0

    tracks_per_artist = dfm["trackName"].nunique() / max(unique_art, 1)

    kids_peak_year = yr_max
    if dfd is not None and not dfd.empty and "year" in dfd.columns:
        kids_yearly    = dfd.groupby("year")["ms"].sum()
        kids_peak_year = int(kids_yearly.idxmax()) if not kids_yearly.empty else yr_max

    peak_hour = int(dfm.groupby("hour")["ms"].sum().idxmax()) if not dfm.empty else 18

    return {
        "unique_artists":    unique_art,
        "n_years":           n_years,
        "oldest_year":       yr_min,
        "peak_year":         peak_year,
        "art_per_year":      unique_art / n_years,
        "sat_pct":           sat_ms / total_ms * 100 if total_ms > 0 else 0,
        "sat_h":             sat_ms / 3600000,
        "morning_pct":       morning_ms / total_ms * 100 if total_ms > 0 else 0,
        "night_pct":         night_ms / total_ms * 100 if total_ms > 0 else 0,
        "night_h":           night_ms / 3600000,
        "peak_hour":         peak_hour,
        "kids_pct":          kids_ms / total_all_ms * 100 if total_all_ms > 0 else 0,
        "kids_h":            kids_ms / 3600000,
        "kids_peak_year":    kids_peak_year,
        "top_plays":         int(track_top),
        "top_artist":        top_artist,
        "top_artist_pct":    top_artist_pct,
        "top_artist_h":      top_artist_h,
        "skip_rate":         skip_rate,
        "completion_pct":    completion_pct,
        "binge_sessions":    binge_sessions,
        "shuffle_pct":       shuffle_pct,
        "liked_pct":         liked_pct,
        "liked_n":           liked_n,
        "never_played_pct":  never_played_pct,
        "proj_new":          int(unique_art / n_years),
        "old_music_pct":     old_music_pct,
        "tracks_per_artist": tracks_per_artist,
        "total_plays":       len(dfm),
    }

def _format(template, stats):
    try:
        return template.format(**stats)
    except:
        return template

def render(dfm, dfd=None, lib=None):
    st.title("🔮 Musical Horoscope")
    st.markdown("*Your musical sign — derived from actual behaviour, not vibes.*")

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

    tab1, tab2 = st.tabs(["Your Sign", "All Signs"])

    with tab1:
        st.markdown(
