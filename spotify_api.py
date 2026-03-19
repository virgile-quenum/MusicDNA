import streamlit as st
import pandas as pd
from spotify_auth import api_get

def get_user_profile():
    return api_get("me")

def get_top_artists(time_range="medium_term", limit=20):
    data = api_get("me/top/artists", {"time_range": time_range, "limit": limit})
    if not data: return []
    return data.get('items', [])

def get_top_tracks(time_range="medium_term", limit=20):
    data = api_get("me/top/tracks", {"time_range": time_range, "limit": limit})
    if not data: return []
    return data.get('items', [])

def get_recently_played(limit=50):
    data = api_get("me/player/recently-played", {"limit": limit})
    if not data: return []
    return data.get('items', [])

def get_recommendations(seed_artists=None, seed_tracks=None, limit=20,
                        min_popularity=0, max_popularity=100):
    params = {"limit": limit,
              "min_popularity": min_popularity,
              "max_popularity": max_popularity}
    if seed_artists: params["seed_artists"] = ",".join(seed_artists[:5])
    if seed_tracks:  params["seed_tracks"]  = ",".join(seed_tracks[:5])
    data = api_get("recommendations", params)
    if not data: return []
    return data.get('tracks', [])

def get_audio_features(track_ids):
    if not track_ids: return []
    ids = ",".join(track_ids[:100])
    data = api_get("audio-features", {"ids": ids})
    if not data: return []
    return [f for f in data.get('audio_features', []) if f]

def create_playlist(user_id, name, track_uris):
    token = st.session_state.get('spotify_token', {}).get('access_token')
    if not token: return None
    import requests, json
    headers = {"Authorization": "Bearer " + token,
               "Content-Type": "application/json"}
    resp = requests.post(
        "https://api.spotify.com/v1/users/" + user_id + "/playlists",
        headers=headers,
        data=json.dumps({"name": name, "public": False,
                         "description": "Created by MusicDNA"})
    )
    if resp.status_code != 201: return None
    pl_id = resp.json()['id']
    requests.post(
        "https://api.spotify.com/v1/playlists/" + pl_id + "/tracks",
        headers=headers,
        data=json.dumps({"uris": track_uris[:100]})
    )
    return resp.json().get('external_urls', {}).get('spotify')

def build_api_profile():
    profile = {}
    profile['user']               = get_user_profile()
    profile['top_artists_short']  = get_top_artists('short_term',  20)
    profile['top_artists_medium'] = get_top_artists('medium_term', 20)
    profile['top_artists_long']   = get_top_artists('long_term',   20)
    profile['top_tracks_medium']  = get_top_tracks('medium_term',  20)
    profile['recent']             = get_recently_played(50)
    return profile
