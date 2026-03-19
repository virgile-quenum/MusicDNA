import streamlit as st
import requests
import urllib.parse
import base64
from datetime import datetime, timedelta

SCOPES = " ".join([
    "user-read-private",
    "user-read-email",
    "user-top-read",
    "user-read-recently-played",
    "playlist-read-private",
    "playlist-read-collaborative",
    "playlist-modify-public",
    "playlist-modify-private",
    "user-library-read",
])

def get_config():
    try:
        return (
            st.secrets["SPOTIFY_CLIENT_ID"],
            st.secrets["SPOTIFY_CLIENT_SECRET"],
            st.secrets["REDIRECT_URI"],
        )
    except Exception:
        return None, None, None

def get_auth_url():
    client_id, _, redirect_uri = get_config()
    if not client_id:
        return "#"
    params = {
        "client_id":     client_id,
        "response_type": "code",
        "redirect_uri":  redirect_uri,
        "scope":         SCOPES,
        "show_dialog":   "true",
    }
    return "https://accounts.spotify.com/authorize?" + urllib.parse.urlencode(params)

def exchange_code(code):
    client_id, client_secret, redirect_uri = get_config()
    if not client_id:
        return None
    creds = base64.b64encode((client_id + ":" + client_secret).encode()).decode()
    resp = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={"Authorization": "Basic " + creds,
                 "Content-Type": "application/x-www-form-urlencoded"},
        data={"grant_type": "authorization_code",
              "code": code, "redirect_uri": redirect_uri}
    )
    if resp.status_code == 200:
        data = resp.json()
        data['expires_at'] = (datetime.now() + timedelta(seconds=data['expires_in'])).isoformat()
        return data
    return None

def refresh_token(refresh_tok):
    client_id, client_secret, _ = get_config()
    if not client_id:
        return None
    creds = base64.b64encode((client_id + ":" + client_secret).encode()).decode()
    resp = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={"Authorization": "Basic " + creds,
                 "Content-Type": "application/x-www-form-urlencoded"},
        data={"grant_type": "refresh_token", "refresh_token": refresh_tok}
    )
    if resp.status_code == 200:
        data = resp.json()
        data['expires_at'] = (datetime.now() + timedelta(seconds=data['expires_in'])).isoformat()
        data['refresh_token'] = refresh_tok
        return data
    return None

def get_valid_token():
    if 'spotify_token' not in st.session_state:
        return None
    tok = st.session_state.spotify_token
    try:
        expires_at = datetime.fromisoformat(tok['expires_at'])
        if datetime.now() >= expires_at - timedelta(minutes=5):
            new_tok = refresh_token(tok.get('refresh_token'))
            if new_tok:
                st.session_state.spotify_token = new_tok
                return new_tok['access_token']
            return None
        return tok['access_token']
    except Exception:
        return None

def api_get(endpoint, params=None):
    token = get_valid_token()
    if not token:
        return None
    try:
        resp = requests.get(
            "https://api.spotify.com/v1/" + endpoint,
            headers={"Authorization": "Bearer " + token},
            params=params or {}
        )
        if resp.status_code == 200:
            return resp.json()
    except Exception:
        pass
    return None

def is_authenticated():
    return get_valid_token() is not None

def handle_callback():
    try:
        params = st.query_params
        if 'code' in params and 'spotify_token' not in st.session_state:
            code = params['code']
            token_data = exchange_code(code)
            if token_data:
                st.
