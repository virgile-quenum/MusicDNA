import streamlit as st
import pandas as pd

VIOLET = "#7C3AED"
VIOLET_LIGHT = "#A78BFA"

TRACK_ROASTS = {
    "bug a boo":              "Destinys Child called. They want their 2001 back. You said keep it.",
    "hips dont lie":          "For your daughters. The daughters are 6. This was at 11pm.",
    "waka waka":              "This time for Africa. Every time. Apparently Africa needed 14 visits.",
    "antologia":              "A married man. Playing Anthology of Lost Love. Repeatedly. Interesting.",
    "soltera":                "Soltera means Single Woman. You are not. {plays}x.",
    "momma, i think i married a hoe": "The title. Is the comment. {plays} plays.",
    "some guys have all the luck":    "Narrator: he was, statistically, doing fine.",
    "leftovers":              "Your number 1 most played track is called Leftovers. Millie Jackson knew.",
    "papa was a rollin stone":        "Aspirational or autobiographical? {plays} listens and still deciding.",
    "reseaux":                "Niska. In your top tracks. All-time. The algorithm has your address.",
    "sexy ladies":            "{plays} plays of Sexy Ladies by Timaya. Zero likes. Pure cognitive dissonance.",
    "kotch":                  "Kotch. {plays} times. You sat down for this. Willingly.",
    "this kind luv":          "{plays} plays of This Kind Luv. You know every word. Just admit it.",
    "walahi":                 "Walahi {plays} times. By God indeed. Even He is surprised.",
    "skelewu":                "Skelewu {plays}x. The whole body was involved. Every single time.",
    "personally":             "Personally by P-Square. {plays} times. You took it very personally.",
    "collabo":                "Collabo {plays}x. P-Square again. You have a type.",
    "alingo":                 "Alingo. {plays} plays. You know the dance. Do not deny it.",
}

ARTIST_ROASTS = {
    "niska":       "Niska is in your top plays. You have a Blues playlist AND Niska. Pick a lane.",
    "patoranking": "{plays}x Patoranking. Not a guilty pleasure — but not something you would lead with at a dinner party.",
    "timaya":      "Timaya. {plays} plays. Sexy Ladies specifically. We checked.",
    "runtown":     "Runtown {plays}x. Walahi is basically your national anthem at this point.",
    "rdx":         "RDX Kotch. {plays} times. Dancehalls most chaotic song. You chose it. Repeatedly.",
    "davido":      "Skelewu {plays}x. The whole body was involved. Every time.",
    "chris brown": "Chris Brown. {plays} plays. We are not going to say it. You already know.",
    "drake":       "Drake. In your top artists. All-time. You and every other person on Spotify.",
    "dadju":       "Dadju {plays}x. French R&B. Candles were probably involved.",
    "kanye west":  "{plays} plays, 0 likes saved. Even you cannot commit to Kanye.",
    "p-square":    "P-Square {plays}x total. Personally, Collabo, Alingo. The Holy Trinity of your shame.",
    "luciano":     "Luciano {plays}x. German trap. In French. You are a complex man.",
}

GENERIC = [
    "#{rank} -- {track} by {artist}. {plays} plays. The algorithm saw everything.",
    "#{rank} -- {track}. {plays}x. Not in your liked tracks. You play it anyway. Make it make sense.",
    "#{rank} -- {artist} -- {track}. {plays} times. This is your listening history. Own it.",
    "#{rank} -- {plays}x {track}. No comment. Actually {plays} comments. We are saving them.",
    "#{rank} -- {track} by {artist}. Played {plays} times. Never liked. The definition of complicated.",
]

def get_roast(track, artist, plays, rank):
    import random
    tl = track.lower().replace("'","").replace("é","e").replace("è","e").replace("ñ","n")
    al = artist.lower()
    for k, tmpl in TRACK_ROASTS.items():
        if k in tl:
            return tmpl.format(plays=plays, artist=artist, track=track, rank=rank)
    for k, tmpl in ARTIST_ROASTS.items():
        if k in al:
            return tmpl.format(plays=plays, artist=artist, track=track, rank=rank)
    t = GENERIC[rank % len(GENERIC)]
    return t.format(track=track, artist=artist, plays=plays, rank=rank)

def render(dfm, lib):
    st.title("Hall of Shame")
    st.markdown("*Your most-played tracks — identified, exposed, judged. Without mercy.*")

    track_stats = dfm.groupby(['trackName','artistName']).agg(
        plays=('ms','count'),
        hours=('ms', lambda x: round(x.sum()/3600000,2)),
        late_plays=('hour', lambda x: ((x >= 22) | (x <= 4)).sum()),
        skip_rate=('skipped', lambda x: round(x.mean()*100,1)),
    ).reset_index()

    liked_tracks = set()
    if lib.get('tracks'):
        liked_tracks = {t['track'].lower().strip() for t in lib['tracks']}

    track_stats['shame_score'] = (
        track_stats['plays'] * 1.0 +
        track_stats['late_plays'] * 3.0 +
        track_stats['trackName'].str.lower().str.strip().apply(
            lambda x: 8 if x not in liked_tracks else 0)
    )

    shame = track_stats.sort_values('shame_score', ascending=False).head(12)

    st.markdown("---")

    st.markdown("""
    <div style='display:grid;grid-template-columns:2.5fr 0.7fr 0.7fr 3fr;
                gap:0;margin-bottom:6px;padding:0 4px;'>
      <div style='color:#444;font-size:.7em;text-transform:uppercase;
                  letter-spacing:.08em;'>Track and Artist</div>
      <div style='color:#444;font-size:.7em;text-transform:uppercase;
                  letter-spacing:.08em;'>Plays</div>
      <div style='color:#444;font-size:.7em;text-transform:uppercase;
                  letter-spacing:.08em;'>Late night</div>
      <div style='color:#444;font-size:.7em;text-transform:uppercase;
                  letter-spacing:.08em;'>Verdict</div>
    </div>""", unsafe_allow_html=True)

    for rank, (_, row) in enumerate(shame.iterrows(), 1):
        roast = get_roast(row['trackName'], row['artistName'],
                          int(row['plays']), rank)
        liked = "liked" if row['trackName'].lower().strip() in liked_tracks else "not liked"
        late  = f"{int(row['late_plays'])}x" if row['late_plays'] > 0 else "--"
        bg    = "#110008" if rank <= 3 else "#0a0a0a"
        border= "#7C3AED" if rank <= 3 else "#1e1e1e"

        st.markdown(f"""
        <div style='display:grid;grid-template-columns:2.5fr 0.7fr 0.7fr 3fr;
                    background:{bg};border:1px solid {border};
                    border-radius:8px;margin-bottom:5px;'>
          <div style='padding:11px 14px;'>
            <div style='font-weight:700;color:#fff;font-size:.88em;'>
              {row['trackName'][:42]}</div>
            <div style='color:#444;font-size:.76em;margin-top:2px;'>
              {row['artistName']} &middot; {liked}</div>
          </div>
          <div style='padding:11px 14px;color:{VIOLET_LIGHT};font-weight:800;
                      font-size:1.05em;display:flex;align-items:center;'>
            {int(row['plays'])}x
          </div>
          <div style='padding:11px 14px;color:#f59e0b;
                      display:flex;align-items:center;font-size:.88em;'>
            {late}
          </div>
          <div style='padding:11px 14px;color:#888;font-size:.82em;
                      line-height:1.55;display:flex;align-items:center;
                      font-style:italic;'>
            {roast}
          </div>
        </div>""", unsafe_allow_html=True)

    if liked_tracks:
        st.markdown("---")
        st.markdown("### Played 10+ Times, Never Liked")
        st.caption("You know every word. You never saved it. Impressive commitment to denial.")
        unloved = track_stats[
            (track_stats['plays'] >= 10) &
            (~track_stats['trackName'].str.lower().str.strip().isin(liked_tracks))
        ].sort_values('plays', ascending=False).head(8)
        for _, r in unloved.iterrows():
            st.markdown(
                f"- **{r['trackName']}** -- {r['artistName']} -- "
                f"*{int(r['plays'])} plays* -- never saved"
            )

    st.markdown("---")
    if not shame.empty:
        top = shame.iloc[0]
        roast_share = get_roast(top['trackName'], top['artistName'],
                                int(top['plays']), 1)
        st.markdown("**Share your shame:**")
        st.code(f"MusicDNA just exposed me -- {roast_share} musicdna.streamlit.app")
