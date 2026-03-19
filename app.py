import streamlit as st

st.set_page_config(page_title="MusicDNA", page_icon="🎵")
st.title("MusicDNA — Test")
st.write("App is running.")

try:
    from filters import split
    st.success("filters.py OK")
except Exception as e:
    st.error("filters.py FAILED: " + str(e))

try:
    from spotify_auth import handle_callback, is_authenticated, get_auth_url
    st.success("spotify_auth.py OK")
except Exception as e:
    st.error("spotify_auth.py FAILED: " + str(e))

try:
    import landing
    st.success("landing.py OK")
except Exception as e:
    st.error("landing.py FAILED: " + str(e))
