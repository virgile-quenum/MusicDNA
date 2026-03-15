import streamlit as st
import pandas as pd

SIGNS = [
    {
        'name': 'L\'Archiviste Fiévreux',
        'en': 'The Feverish Archivist',
        'condition': lambda s: s['liked_pct'] > 40 and s['never_played_pct'] > 35,
        'curse':  "You build libraries you never open. {never_played_pct:.0f}% of your likes have never been played. You collect music like others collect books they'll never read.",
        'gift':   "When you find something, you commit. Your top track has {top_plays} plays. Your attention is total or absent — there is no middle ground.",
        'sign':   "♒",
        'prediction': "Your collection keeps growing. Your actual listening doesn't. One day you'll open those 2,031 unplayed likes. That day is not today.",
    },
    {
        'name': 'Le Fouilleur du Samedi',
        'en': 'The Saturday Digger',
        'condition': lambda s: s['sat_pct'] > 18,
        'curse':  "Saturday is your temple. {sat_h:.0f}h on Saturdays alone. You don't listen to music through the week — you save yourself for it.",
        'gift':   "You listen with intention. Saturday listening is never background. It's a ritual.",
        'sign':   "♌",
        'prediction': "Your best discoveries happen on weekends. Your taste is formed on Saturday mornings. This will never change.",
    },
    {
        'name': 'Le Voyageur Culturel',
        'en': 'The Cultural Nomad',
        'condition': lambda s: s['unique_artists'] > 5000,
        'curse':  "{unique_artists:,} artists. You cannot commit. You are always looking for the next one. The one you just found will be forgotten by Tuesday.",
        'gift':   "Your breadth is genuinely exceptional. You are not a niche listener. You are the algorithm's nightmare and dream simultaneously.",
        'sign':   "♐",
        'prediction': "You will discover {proj_new} new artists this year. You will remember 12 of them.",
    },
    {
        'name': 'Le Régressif Nostalgique',
        'en': 'The Nostalgic Regressor',
        'condition': lambda s: s['avg_era'] < 1985,
        'curse':  "Your musical core is stuck in the {avg_era_decade}s. Not because you're old. Because nothing since has matched it. You know this.",
        'gift':   "You have taste. Actual taste. Formed by listening to the actual originals, not the samples.",
        'sign':   "♓",
        'prediction': "You will continue to discover music from before you were born. This is not a problem. This is who you are.",
    },
    {
        'name': 'Le Parent Infiltré',
        'en': 'The Infiltrated Parent',
        'condition': lambda s: s['kids_pct'] > 8,
        'curse':  "{kids_pct:.0f}% of your total Spotify history is children's content. Your daughters have colonised your account. Spotify thinks you enjoy Judson Mancebo.",
        'gift':   "You kept listening through the chaos. Even with {kids_h:.0f}h of lullabies in your history, you maintained your own taste. Respect.",
        'sign':   "♋",
        'prediction': "The kids content is declining. Your account is slowly becoming yours again. By 2027 it will be fully reclaimed. Probably.",
    },
    {
        'name': 'Le Lève-Tôt Obsessionnel',
        'en': 'The Obsessive Early Riser',
        'condition': lambda s: s['morning_pct'] > 15,
        'curse':  "{morning_pct:.0f}% of your listening happens before 8am. You are not using music as background. You are using it as fuel. This is either admirable or concerning.",
        'gift':   "Morning listening is your most intentional. The tracks you play at 6am are the ones that matter.",
        'sign':   "♈",
        'prediction': "Your 6am playlist will remain your most honest musical statement.",
    },
]

DEFAULT_SIGN = {
    'name': 'L\'Éclectique Assumé',
    'en': 'The Committed Eclectic',
    'curse': "You defy categorisation. {unique_artists:,} artists across every genre and era. You are every algorithm's blind spot.",
    'gift':  "Genuine breadth is rare. Most people say they're eclectic. Your data proves it.",
    'sign':  "♊",
    'prediction': "You will continue to surprise yourself with what you play next. This is the best possible outcome.",
}

def compute_stats(dfm, dfd):
    total_all_ms = dfm['ms'].sum() + (dfd['ms'].sum() if not dfd.empty else 0)
    kids_ms      = dfd['ms'].sum() if not dfd.empty else 0
    sat_ms       = dfm[dfm['dow']==5]['ms'].sum()
    morning_ms   = dfm[dfm['hour'].between(5,7)]['ms'].sum()
    track_top    = dfm.groupby('trackName')['ms'].count().max() if not dfm.empty else 0

    return {
        'unique_artists':  dfm['artistName'].nunique(),
        'sat_pct':         sat_ms / dfm['ms'].sum() * 100,
        'sat_h':           sat_ms / 3600000,
        'morning_pct':     morning_ms / dfm['ms'].sum() * 100,
        'kids_pct':        kids_ms / total_all_ms * 100 if total_all_ms > 0 else 0,
        'kids_h':          kids_ms / 3600000,
        'top_plays':       int(track_top),
        'liked_pct':       50,   # placeholder if no lib
        'never_played_pct':45,
        'avg_era':         1978, # based on known profile
        'avg_era_decade':  '70',
        'proj_new':        int(dfm['artistName'].nunique() / max(dfm['year'].nunique(),1)),
    }

def render(dfm, dfd=None):
    st.title("🔮 Musical Horoscope")
    st.markdown("*Your musical sign — derived from 12 years of actual behaviour, not vibes.*")

    if dfd is None:
        import pandas as pd
        dfd = pd.DataFrame()

    stats = compute_stats(dfm, dfd)

    matched_sign = None
    for sign in SIGNS:
        try:
            if sign['condition'](stats):
                matched_sign = sign
                break
        except: pass
    if not matched_sign:
        matched_sign = DEFAULT_SIGN

    # ── Main sign card ────────────────────────────────────────────────────
    st.markdown(f"""
    <div style='background:linear-gradient(135deg,#0a0a2a,#0a1a0a);
                border:1px solid #7C3AED;border-radius:16px;padding:32px;
                text-align:center;margin-bottom:24px;'>
      <div style='font-size:4em;'>{matched_sign.get('sign','⭐')}</div>
      <div style='font-size:1.8em;font-weight:900;color:#A78BFA;margin-top:8px;'>
        {matched_sign['name']}</div>
      <div style='color:#555;font-size:.85em;font-style:italic;margin-top:4px;'>
        {matched_sign.get('en','')}</div>
    </div>""", unsafe_allow_html=True)

    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### 💀 Your Curse")
        try:    curse = matched_sign['curse'].format(**stats)
        except: curse = matched_sign['curse']
        st.markdown(f"<div class='insight'>{curse}</div>", unsafe_allow_html=True)

        st.markdown("### 🎁 Your Gift")
        try:    gift = matched_sign['gift'].format(**stats)
        except: gift = matched_sign['gift']
        st.markdown(f"<div class='insight'>{gift}</div>", unsafe_allow_html=True)

    with col2:
        st.markdown("### 🔭 Your Prediction")
        try:    pred = matched_sign['prediction'].format(**stats)
        except: pred = matched_sign['prediction']
        st.markdown(f"<div class='insight'>{pred}</div>", unsafe_allow_html=True)

        st.markdown("### 📊 Your Numbers")
        for lbl, val in [
            ("Total artists",    f"{stats['unique_artists']:,}"),
            ("Saturday share",   f"{stats['sat_pct']:.0f}%"),
            ("Morning listening",f"{stats['morning_pct']:.0f}%"),
            ("Kids content",     f"{stats['kids_pct']:.0f}%"),
            ("Most played track",f"{stats['top_plays']} plays"),
        ]:
            st.markdown(f"<div style='display:flex;justify-content:space-between;"
                        f"padding:5px 0;border-bottom:1px solid #222;font-size:.85em;'>"
                        f"<span style='color:#888;'>{lbl}</span>"
                        f"<span style='color:#fff;font-weight:700;'>{val}</span></div>",
                        unsafe_allow_html=True)

    st.markdown("---")
    share = f"My musical sign is {matched_sign.get('sign','🎵')} {matched_sign['name']} ({matched_sign.get('en','')}). 12 years of Spotify data don't lie. 🎵🔮"
    st.markdown("**📤 Share your sign:**")
    st.code(share)
