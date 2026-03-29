import streamlit as st

def render(get_auth_url_fn, data_loaded=False):
    auth_url = get_auth_url_fn()

    # ── Hero ──────────────────────────────────────────────────────────────
    st.markdown(
        "<div style='text-align:center;padding:60px 0 32px;'>"
        "<div style='font-size:3em;margin-bottom:12px;'>🎵</div>"
        "<h1 style='font-size:3.2em;font-weight:900;margin:0 0 8px;letter-spacing:-.02em;'>"
        "Music<span style='color:#A78BFA;'>DNA</span></h1>"
        "<p style='color:#555;font-size:.82em;margin:0 0 20px;letter-spacing:.08em;'>"
        "POWERED BY DHALSIMSTREAM</p>"
        "<p style='color:#aaa;font-size:1.05em;line-height:1.9;max-width:560px;margin:0 auto 12px;'>"
        "Spotify Wrapped tells you what you listened to.<br>"
        "<b style='color:#fff;'>MusicDNA tells you who you are.</b><br>"
        "<span style='color:#555;font-size:.9em;'>"
        "12 years of data. No algorithm. No curation. Just the truth."
        "</span>"
        "</p>"
        "</div>",
        unsafe_allow_html=True
    )

    # ── CTA ───────────────────────────────────────────────────────────────
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown(
            "<div style='text-align:center;margin-bottom:8px;'>"
            "<a href='" + auth_url + "' target='_top' "
            "style='background:#1DB954;color:#000;font-weight:900;"
            "padding:16px 48px;border-radius:30px;text-decoration:none;"
            "font-size:1em;display:inline-block;letter-spacing:.02em;'>"
            "Connect Spotify — start here</a>"
            "</div>"
            "<div style='text-align:center;'>"
            "<span style='color:#333;font-size:.78em;'>"
            "No Spotify? Upload your export directly in the sidebar."
            "</span>"
            "</div>",
            unsafe_allow_html=True
        )

    st.markdown("<div style='margin:32px 0 24px;border-top:1px solid #1a1a1a;'></div>",
                unsafe_allow_html=True)

    # ── The hook — 4 data shocks ──────────────────────────────────────────
    st.markdown(
        "<div style='text-align:center;margin-bottom:20px;'>"
        "<div style='color:#A78BFA;font-size:.72em;font-weight:700;"
        "text-transform:uppercase;letter-spacing:.12em;'>"
        "What your data reveals about you</div>"
        "</div>",
        unsafe_allow_html=True
    )

    shocks = [
        ("45%",    "of liked tracks have never been played",
                   "You collect music like books you'll never read."),
        ("93×",    "the same O.V. Wright track played in one year",
                   "That's not listening. That's something else."),
        ("July 2020", "first children's content detected",
                   "Spotify knew before you announced it anywhere."),
        ("2018",   "peak listening year for most users",
                   "Life was different then. The data agrees."),
    ]
    cols = st.columns(4)
    for col, (val, lbl, sub) in zip(cols, shocks):
        with col:
            st.markdown(
                "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
                "border-radius:12px;padding:18px 14px;text-align:center;height:100%;'>"
                "<div style='font-size:1.7em;font-weight:900;color:#A78BFA;margin-bottom:8px;'>"
                + val + "</div>"
                "<div style='font-size:.76em;color:#aaa;margin-bottom:8px;line-height:1.5;'>"
                + lbl + "</div>"
                "<div style='font-size:.72em;color:#555;font-style:italic;line-height:1.5;'>"
                + sub + "</div>"
                "</div>",
                unsafe_allow_html=True
            )

    st.markdown("<div style='margin:32px 0 24px;border-top:1px solid #1a1a1a;'></div>",
                unsafe_allow_html=True)

    # ── Feature grid ─────────────────────────────────────────────────────
    st.markdown(
        "<div style='text-align:center;margin-bottom:20px;'>"
        "<div style='color:#A78BFA;font-size:.72em;font-weight:700;"
        "text-transform:uppercase;letter-spacing:.12em;margin-bottom:8px;'>"
        "12 analyses — none of them are in Wrapped</div>"
        "</div>",
        unsafe_allow_html=True
    )

    features = [
        ("🔮", "Musical Horoscope",
         "Your sign, curse, gift and prediction — from 12 years of real behaviour. "
         "Not vibes. Data."),
        ("👁",  "The Witness",
         "Obsessions, silences, time shifts, parenthood signals — "
         "the moments your data remembers that you forgot."),
        ("💔", "Likes Autopsy",
         "45% of what you saved has never been played. "
         "The gap between who you think you are and who you actually are."),
        ("😳", "Hall of Shame",
         "Tracks you play constantly — never liked, never saved. "
         "Your most honest musical self."),
        ("👶", "Parent Mode",
         "The exact month parenthood arrived in your Spotify. "
         "Detected automatically from your data."),
        ("📋", "Playlist Autopsy",
         "Which playlists you actually use vs. the ones you built and forgot."),
        ("🎤", "Artists and Tracks",
         "Your all-time top artists and tracks with period filters "
         "and discography depth analysis."),
        ("⭐", "Celebrity Twin",
         "Which public figures share your exact musical taste — "
         "based on your actual listening history."),
        ("🕵", "Taste Drift",
         "Spotify thinks it knows you. Your history says otherwise. "
         "Side-by-side comparison."),
        ("🕳", "Forgotten",
         "Tracks you used to love. Obsessions you dropped. "
         "Time capsules from a specific month of your life."),
        ("🔭", "Explore",
         "Artists you tried and left. Friction artists you kept skipping. "
         "What's worth revisiting."),
        ("🏠", "Musical Profile",
         "Your full DNA score across 5 dimensions. "
         "Your eras, your archetype, your numbers."),
    ]

    cols = st.columns(3)
    for i, (icon, title, desc) in enumerate(features):
        with cols[i % 3]:
            st.markdown(
                "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
                "border-left:3px solid #7C3AED;border-radius:8px;"
                "padding:14px;margin-bottom:10px;'>"
                "<div style='font-weight:700;color:#fff;margin-bottom:5px;'>"
                + icon + " " + title + "</div>"
                "<div style='color:#888;font-size:.78em;line-height:1.6;'>"
                + desc + "</div>"
                "</div>",
                unsafe_allow_html=True
            )

    st.markdown("<div style='margin:32px 0 24px;border-top:1px solid #1a1a1a;'></div>",
                unsafe_allow_html=True)

    # ── How to get your data ──────────────────────────────────────────────
    st.markdown(
        "<div style='background:#0f0f0f;border:1px solid #A78BFA33;"
        "border-radius:14px;padding:24px;margin-bottom:20px;'>"
        "<div style='color:#A78BFA;font-weight:700;font-size:.78em;"
        "text-transform:uppercase;letter-spacing:.08em;margin-bottom:16px;'>"
        "How to unlock your full 12-year history</div>"
        "<div style='display:grid;grid-template-columns:1fr 1fr;gap:12px;'>"

        "<div style='background:#0a0a0a;border-radius:8px;padding:14px;'>"
        "<div style='color:#1DB954;font-size:.72em;font-weight:700;"
        "text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px;'>Step 1 — instant</div>"
        "<div style='color:#ccc;font-size:.85em;font-weight:700;margin-bottom:4px;'>"
        "Connect Spotify above</div>"
        "<div style='color:#555;font-size:.78em;line-height:1.6;'>"
        "Immediate access to your recent listening. No waiting."
        "</div></div>"

        "<div style='background:#0a0a0a;border-radius:8px;padding:14px;'>"
        "<div style='color:#A78BFA;font-size:.72em;font-weight:700;"
        "text-transform:uppercase;letter-spacing:.06em;margin-bottom:6px;'>"
        "Step 2 — up to 30 days</div>"
        "<div style='color:#ccc;font-size:.85em;font-weight:700;margin-bottom:4px;'>"
        "Request your Extended History</div>"
        "<div style='color:#555;font-size:.78em;line-height:1.6;'>"
        "Go to <b style='color:#aaa;'>spotify.com/account/privacy</b> → "
        "request Extended streaming history → wait for the email → "
        "upload the zip in the sidebar."
        "</div></div>"

        "</div></div>",
        unsafe_allow_html=True
    )

    # ── Privacy note ──────────────────────────────────────────────────────
    st.markdown(
        "<div style='background:#0a0a0a;border:1px solid #1e1e1e;"
        "border-radius:10px;padding:16px;margin-bottom:24px;'>"
        "<div style='display:flex;align-items:center;gap:10px;'>"
        "<span style='font-size:1.2em;'>🔒</span>"
        "<div style='color:#555;font-size:.78em;line-height:1.6;'>"
        "Your data never leaves your browser. "
        "MusicDNA does not store, share or transmit any of your Spotify data. "
        "All analysis runs locally in your session and is deleted when you close the tab."
        "</div></div></div>",
        unsafe_allow_html=True
    )

    # ── Final CTA ─────────────────────────────────────────────────────────
    col_l, col_c, col_r = st.columns([1, 2, 1])
    with col_c:
        st.markdown(
            "<div style='text-align:center;padding:8px 0 32px;'>"
            "<a href='" + auth_url + "' target='_top' "
            "style='background:#7C3AED;color:#fff;font-weight:900;"
            "padding:16px 48px;border-radius:30px;text-decoration:none;"
            "font-size:1em;display:inline-block;'>"
            "Connect Spotify — free, no account needed</a>"
            "</div>",
            unsafe_allow_html=True
        )

    if data_loaded:
        st.warning(
            "Connecting Spotify will reload the page — "
            "your uploaded files will need to be re-uploaded. "
            "Connect Spotify first, then upload your files."
        )
