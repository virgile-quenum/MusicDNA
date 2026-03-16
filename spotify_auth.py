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
        client_id     = st.secrets["SPOTIFY_CLIENT_ID"]
        client_secret = st.secrets["SPOTIFY_CLIENT_SECRET"]
        redirect_uri  = st.secrets["REDIRECT_URI"]
        return client_id, client_secret, redirect_uri
    except Exception:
        st.error("Spotify credentials not found. Add them in Streamlit Secrets.")
        st.stop()

def get_auth_url():
    client_id, _, redirect_uri = get_config()
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
    creds = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    resp = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={"Authorization": f"Basic {creds}",
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
    creds = base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()
    resp = requests.post(
        "https://accounts.spotify.com/api/token",
        headers={"Authorization": f"Basic {creds}",
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
    expires_at = datetime.fromisoformat(tok['expires_at'])
    if datetime.now() >= expires_at - timedelta(minutes=5):
        new_tok = refresh_token(tok['refresh_token'])
        if new_tok:
            st.session_state.spotify_token = new_tok
            return new_tok['access_token']
        return None
    return tok['access_token']

def api_get(endpoint, params=None):
    token = get_valid_token()
    if not token: return None
    resp = requests.get(
        f"https://api.spotify.com/v1/{endpoint}",
        headers={"Authorization": f"Bearer {token}"},
        params=params or {}
    )
    if resp.status_code == 200:
        return resp.json()
    return None

def is_authenticated():
    return get_valid_token() is not None

def handle_callback():
    params = st.query_params
    if 'code' in params and 'spotify_token' not in st.session_state:
        code = params['code']
        token_data = exchange_code(code)
        if token_data:
            st.session_state.spotify_token = token_data
            st.query_params.clear()
            st.rerun()

def render_login():
    VIOLET_LIGHT = "#A78BFA"
    auth_url = get_auth_url()
    st.markdown(f"""
    <div style='text-align:center;padding:40px 0;'>
      <div style='font-size:3em;margin-bottom:16px;'>🎵</div>
      <div style='font-size:1.4em;font-weight:800;color:#fff;margin-bottom:8px;'>
        Connect your Spotify</div>
      <div style='color:#666;font-size:.9em;margin-bottom:28px;'>
        No zip needed. Login and get your analysis instantly.
      </div>
      <a href='{auth_url}' target='_self'
         style='background:#1DB954;color:#000;font-weight:800;
                padding:14px 32px;border-radius:30px;text-decoration:none;
                font-size:1em;display:inline-block;'>
        Connect with Spotify
      </a>
    </div>""", unsafe_allow_html=True)
