import streamlit as st
import pandas as pd, random

ROASTS = {
    # Track-specific roasts
    "bug a boo": "Bug a Boo — Destiny's Child. {plays} plays. It's 2025. You know what you did.",
    "hips don't lie": "Hips Don't Lie — {plays} plays. 'For your daughters.' Sure. We all believe you.",
    "momma, i think i married a hoe": "Momma, I Think I Married A Hoe — {plays} plays. The title says it all. We'll leave it there.",
    "waka waka": "Waka Waka — {plays} plays. This time for Africa. Every time. Apparently.",
    "some guys have all the luck": "Some Guys Have All the Luck — {plays} times. Narrator: he did not, in fact, have all the luck.",
    "papa was a rollin' stone": "Papa Was A Rollin' Stone — {plays} plays. Aspirational or autobiographical?",
    "leftovers": "Leftovers — Millie Jackson — {plays} plays. Your most played track. We respect the commitment. We question everything else.",
    "antología": "Antología — Shakira — {plays} plays. 'It's for my daughters.' Also for the daughters. Got it.",
    "soltera": "Soltera — {plays} plays. A married man. Playing 'Single Woman'. {plays} times.",
}

GENERIC_ROASTS = [
    "#{rank}. {track} — {artist}. {plays} plays. No comment. Actually, many comments. We're keeping them.",
    "#{rank}. {track} by {artist}. {plays} times. This is your most-played music. Think about that.",
    "#{rank}. {plays}x {track}. The algorithm sees you. The algorithm judges you.",
    "#{rank}. {track} — {artist}. {plays} plays and zero likes saved. You know it's wrong. You keep going.",
    "#{rank}. {track} — {plays} plays in secret. Spotify is not a confessional. But here we are.",
]

def get_roast(track, artist, plays, rank):
    key = track.lower()
    for k, template in ROASTS.items():
        if k in key:
            return template.format(plays=plays, artist=artist, track=track, rank=rank)
    t = random.choice(GENERIC_ROASTS)
    return t.format(track=track, artist=artist, plays=plays, rank=rank)

def render(dfm, lib):
    st.title("😳 Hall of Shame")
    st.markdown("*Your guilty pleasures. Identified. Exposed. Judged.*")
    st.caption("Methodology: tracks played repeatedly that contradict your stated musical identity. "
               "Based on play count, artist profile mismatch, and late-night listening patterns.")

    track_stats = dfm.groupby(['trackName','artistName']).agg(
        plays=('ms','count'),
        hours=('ms', lambda x: x.sum()/3600000),
        skips=('skipped','sum'),
        late_plays=('hour', lambda x: ((x >= 22) | (x <= 4)).sum()),
    ).reset_index().sort_values('plays', ascending=False)

    # Top artists for profile comparison
    top_artists = set(dfm.groupby('artistName')['ms'].sum().sort_values(ascending=False).head(20).index)

    # Detect shame candidates: high plays, late night, not in top artist profile
    shame_df = track_stats[
        (track_stats['plays'] >= 5) &
        (~track_stats['artistName'].isin(top_artists))
    ].head(30)

    liked_tracks = set()
    if lib.get('tracks'):
        liked_tracks = {t['track'].lower() for t in lib['tracks']}

    shame_df = shame_df.copy()
    shame_df['shame_score'] = (
        shame_df['plays'] * 2 +
        shame_df['late_plays'] * 5 +
        shame_df['trackName'].str.lower().apply(lambda x: 10 if x not in liked_tracks else 0)
    )
    shame_df = shame_df.sort_values('shame_score', ascending=False).head(10)

    # Also add very-repeated tracks even from known artists
    heavy = track_stats[track_stats['plays'] >= 10].head(5)
    shame_candidates = pd.concat([shame_df, heavy]).drop_duplicates(
        subset=['trackName','artistName']).sort_values('shame_score', ascending=False).head(10)

    st.markdown("---")
    for rank, (_, row) in enumerate(shame_candidates.iterrows(), 1):
        roast = get_roast(row['trackName'], row['artistName'], int(row['plays']), rank)
        late_note = f" 🌙 Including {int(row['late_plays'])}x after 10pm." if row['late_plays'] > 0 else ""
        st.markdown(f"<div class='shame'>😳 {roast}{late_note}</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🏆 Your Unliked Obsessions")
    st.caption("Tracks you played 10+ times but never liked. The denial is palpable.")
    unliked_obsessions = track_stats[
        (track_stats['plays'] >= 10) &
        (~track_stats['trackName'].str.lower().isin(liked_tracks))
    ].head(10)
    for _, row in unliked_obsessions.iterrows():
        st.markdown(f"- **{row['trackName']}** — {row['artistName']} · "
                    f"{int(row['plays'])} plays · 0 likes · pure denial")

    st.markdown("---")
    shame_top = shame_candidates.iloc[0] if not shame_candidates.empty else None
    if shame_top is not None:
        share = (f"My Music DNA app just exposed me: '{shame_top['trackName']}' "
                 f"by {shame_top['artistName']} — {int(shame_top['plays'])} plays "
                 f"and I never even liked it. 😳🎵")
        st.markdown("**📤 Share your shame:**")
        st.code(share)
