import streamlit as st
import pandas as pd
import numpy as np

FEATURES = ["danceability", "energy", "valence", "acousticness",
            "instrumentalness", "tempo"]

def render_recommendations(df):
    st.markdown("# 💡 Recommendations")
    st.markdown("*New artists and songs based on your DNA — and tracks worth rediscovering.*")

    st.markdown("""
    <div class='insight-box'>
    Recommendations use the Spotify API with your audio DNA as seed parameters.
    Click a button below to fetch live suggestions.
    </div>""", unsafe_allow_html=True)

    feat_df = df.dropna(subset=["energy", "valence", "danceability"])
    if feat_df.empty:
        st.warning("Run pipeline.py first.")
        return

    means = feat_df[FEATURES].mean()

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("<div class='section-header'>🎯 Based on Your DNA</div>", unsafe_allow_html=True)

        if st.button("🔀 Get New Track Recommendations", use_container_width=True):
            with st.spinner("Fetching recommendations from Spotify..."):
                try:
                    import spotipy
                    from spotipy.oauth2 import SpotifyClientCredentials
                    from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

                    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
                        client_id=SPOTIFY_CLIENT_ID,
                        client_secret=SPOTIFY_CLIENT_SECRET
                    ))

                    # Use top 3 artists as seeds
                    top_artists_raw = df.groupby("artist_name")["ms_played"].sum().sort_values(ascending=False).head(3)
                    seed_artist_ids = []
                    for artist in top_artists_raw.index:
                        try:
                            res = sp.search(q=f"artist:{artist}", type="artist", limit=1)
                            items = res["artists"]["items"]
                            if items:
                                seed_artist_ids.append(items[0]["id"])
                        except:
                            pass

                    if not seed_artist_ids:
                        st.error("Could not find seed artists. Check your API credentials.")
                    else:
                        recs = sp.recommendations(
                            seed_artists=seed_artist_ids[:3],
                            limit=20,
                            target_energy=float(means["energy"]),
                            target_valence=float(means["valence"]),
                            target_danceability=float(means["danceability"]),
                            target_acousticness=float(means["acousticness"]),
                        )

                        known_tracks = set(df["track_name"].str.lower().dropna())
                        recs_list = []
                        for t in recs["tracks"]:
                            if t["name"].lower() not in known_tracks:
                                recs_list.append({
                                    "Track": t["name"],
                                    "Artist": t["artists"][0]["name"],
                                    "Popularity": t["popularity"],
                                    "Preview": t.get("external_urls", {}).get("spotify", ""),
                                })

                        recs_df = pd.DataFrame(recs_list).sort_values("Popularity", ascending=False)
                        st.dataframe(recs_df[["Track", "Artist", "Popularity"]],
                                     use_container_width=True, hide_index=True)

                        st.markdown("*Open in Spotify:*")
                        for _, row in recs_df.head(5).iterrows():
                            if row["Preview"]:
                                st.markdown(f"→ [{row['Track']} — {row['Artist']}]({row['Preview']})")

                except Exception as e:
                    st.error(f"Spotify API error: {e}")

    with col2:
        st.markdown("<div class='section-header'>🔍 New Artist Suggestions</div>", unsafe_allow_html=True)

        if st.button("🎤 Discover New Artists", use_container_width=True):
            with st.spinner("Finding similar artists..."):
                try:
                    import spotipy
                    from spotipy.oauth2 import SpotifyClientCredentials
                    from config import SPOTIFY_CLIENT_ID, SPOTIFY_CLIENT_SECRET

                    sp = spotipy.Spotify(auth_manager=SpotifyClientCredentials(
                        client_id=SPOTIFY_CLIENT_ID,
                        client_secret=SPOTIFY_CLIENT_SECRET
                    ))

                    top_artists = df.groupby("artist_name")["ms_played"].sum().sort_values(ascending=False).head(5)
                    known_artists = set(df["artist_name"].str.lower().dropna())

                    new_artists = {}
                    for artist in top_artists.index:
                        try:
                            res = sp.search(q=f"artist:{artist}", type="artist", limit=1)
                            items = res["artists"]["items"]
                            if items:
                                related = sp.artist_related_artists(items[0]["id"])
                                for ra in related["artists"]:
                                    if ra["name"].lower() not in known_artists:
                                        new_artists[ra["name"]] = {
                                            "Artist": ra["name"],
                                            "Genres": ", ".join(ra["genres"][:3]),
                                            "Popularity": ra["popularity"],
                                            "Spotify": ra["external_urls"].get("spotify", ""),
                                            "Because you like": artist,
                                        }
                        except:
                            pass

                    if new_artists:
                        new_df = pd.DataFrame(new_artists.values()).sort_values("Popularity", ascending=False).head(20)
                        st.dataframe(new_df[["Artist", "Genres", "Popularity", "Because you like"]],
                                     use_container_width=True, hide_index=True)
                    else:
                        st.info("No new artists found. Check your API credentials.")

                except Exception as e:
                    st.error(f"Error: {e}")

    # ── Rediscovery picks ────────────────────────────────────────────────────
    st.markdown("<div class='section-header'>💀 Top 5 Forgotten Gems to Revisit Now</div>", unsafe_allow_html=True)

    track_stats = df.groupby(["track_name", "artist_name"]).agg(
        play_count=("ms_played", "count"),
        last_play=("ts", "max"),
        avg_ratio=("listen_ratio", "mean"),
    ).reset_index()
    track_stats["last_play"] = pd.to_datetime(track_stats["last_play"])
    track_stats["days_since"] = (pd.Timestamp.now() - track_stats["last_play"]).dt.days

    revisit = track_stats[
        (track_stats["play_count"] >= 5) &
        (track_stats["days_since"] >= 365) &
        (track_stats["avg_ratio"] >= 0.60)
    ].sort_values(["play_count", "days_since"], ascending=[False, False]).head(5)

    for _, row in revisit.iterrows():
        years_ago = row["days_since"] / 365
        st.markdown(f"""
        <div class='insight-box'>
        🎵 <strong>{row['track_name']}</strong> — {row['artist_name']}<br>
        <span style='color:#888;font-size:0.85em;'>
        Played {row['play_count']}x · Last heard {years_ago:.1f} years ago · {row['avg_ratio']*100:.0f}% avg completion
        </span>
        </div>""", unsafe_allow_html=True)
