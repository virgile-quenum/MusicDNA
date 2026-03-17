import streamlit as st

def render(get_auth_url_fn):
    auth_url = get_auth_url_fn()

    st.markdown(
        "<div style='text-align:center;padding:48px 0 24px;'>"
        "<div style='font-size:3.5em;'>🎵</div>"
        "<h1 style='font-size:3em;font-weight:900;margin:8px 0 4px;'>"
        "Music<span style='color:#A78BFA;'>DNA</span></h1>"
        "<p style='color:#555;font-size:.9em;margin:0 0 12px;'>powered by DhalsimStream</p>"
        "<p style='color:#888;font-size:1.05em;line-height:1.8;max-width:520px;margin:0 auto 28px;'>"
        "Spotify Wrapped tells you what you listened to.<br>"
        "<b style='color:#fff;'>MusicDNA tells you who you are.</b>"
        "</p>"
        "<a href='" + auth_url + "' target='_self' "
        "style='background:#1DB954;color:#000;font-weight:800;"
        "padding:14px 36px;border-radius:30px;text-decoration:none;"
        "font-size:1em;display:inline-block;margin-bottom:10px;'>"
        "Connect Spotify — instant access</a>"
        "<div style='color:#444;font-size:.78em;margin-top:8px;'>"
        "Or upload your Extended History zip in the sidebar for the full 12-year analysis</div>"
        "</div>",
        unsafe_allow_html=True
    )

    st.markdown("---")

    st.markdown(
        "<div style='text-align:center;margin-bottom:16px;'>"
        "<div style='color:#A78BFA;font-size:.75em;font-weight:700;"
        "text-transform:uppercase;letter-spacing:.1em;'>What your data reveals</div>"
        "</div>",
        unsafe_allow_html=True
    )

    c1, c2, c3, c4 = st.columns(4)
    shocks = [
        (c1, "45%",     "of liked tracks are never played",       "You collect music like books youll never read."),
        (c2, "1,343h",  "of one users account was his daughters",  "Spotify saw he became a parent before he posted it anywhere."),
        (c3, "2017-18", "peak listening years for most users",     "Life was different then. The data agrees."),
        (c4, "17%",     "average skip rate",                       "Lower than you think. You are more committed than you admit."),
    ]
    for col, val, lbl, sub in shocks:
        with col:
            st.markdown(
                "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
                "border-radius:12px;padding:18px;text-align:center;'>"
                "<div style='font-size:1.8em;font-weight:900;color:#A78BFA;'>" + val + "</div>"
                "<div style='font-size:.75em;color:#888;margin:6px 0 8px;line-height:1.4;'>" + lbl + "</div>"
                "<div style='font-size:.72em;color:#444;font-style:italic;line-height:1.4;'>" + sub + "</div>"
                "</div>",
                unsafe_allow_html=True
            )

    st.markdown(
        "<div style='color:#A78BFA;font-size:.75em;font-weight:700;"
        "text-transform:uppercase;letter-spacing:.1em;margin:20px 0 12px;'>"
        "9 analyses — none of them are in Wrapped</div>",
        unsafe_allow_html=True
    )

    features = [
        ("🏠", "Musical Profile",   "12 years of listening history. Your eras, your evolution, your numbers."),
        ("🎤", "Artists and Tracks","Your all-time top artists and tracks with yearly breakdowns."),
        ("🕐", "Time Patterns",     "When you listen. Hour by hour, day by day. Your listening heatmap."),
        ("👶", "Parent Mode",       "How parenthood rewrote your Spotify. Detected automatically."),
        ("💔", "Likes Autopsy",     "45% of liked tracks never played. Who you think you are vs. reality."),
        ("📋", "Playlist Autopsy",  "Active playlists vs archives. Plus merge candidates."),
        ("😳", "Hall of Shame",     "Your most-played tracks judged. Sarcastically. Without mercy."),
        ("⭐", "Celebrity Twin",    "Which public figures share your exact musical taste."),
        ("🔮", "Musical Horoscope", "Your sign, your curse, your gift, your prediction. From real data."),
    ]

    cols = st.columns(3)
    for i, (icon, title, desc) in enumerate(features):
        with cols[i % 3]:
            st.markdown(
                "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
                "border-left:3px solid #7C3AED;border-radius:8px;"
                "padding:14px;margin-bottom:10px;'>"
                "<div style='font-weight:700;margin-bottom:4px;'>" + icon + " " + title + "</div>"
                "<div style='color:#555;font-size:.8em;line-height:1.5;'>" + desc + "</div>"
                "</div>",
                unsafe_allow_html=True
            )

    st.markdown("---")

    st.markdown(
        "<div style='background:#0f0505;border:1px solid #dc262633;"
        "border-radius:14px;padding:24px;margin-bottom:20px;'>"
        "<div style='color:#f87171;font-size:.75em;font-weight:700;"
        "text-transform:uppercase;letter-spacing:.1em;margin-bottom:8px;'>"
        "Parent Mode — unique to MusicDNA</div>"
        "<div style='font-size:1.1em;font-weight:800;color:#fff;margin-bottom:8px;'>"
        "Spotify knows when you became a parent.</div>"
        "<div style='color:#888;font-size:.88em;line-height:1.8;'>"
        "One month your listening is yours. The next it shifts — lullabies, nursery rhymes, "
        "children songs on loop at 3am. MusicDNA detects this automatically and shows you "
        "the exact month it happened.<br><br>"
        "<b style='color:#ccc;'>You posted the birth announcement. "
        "Spotify had already figured it out weeks earlier.</b>"
        "</div>"
        "</div>",
        unsafe_allow_html=True
    )

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            "<div style='background:#0f0f0f;border:1px solid #1DB95433;"
            "border-radius:12px;padding:18px;'>"
            "<div style='color:#1DB954;font-weight:700;font-size:.82em;margin-bottom:10px;'>"
            "OPTION 1 — Instant</div>"
            "<div style='color:#888;font-size:.83em;line-height:2;'>"
            "Click <b style='color:#fff;'>Connect Spotify</b> in the sidebar<br>"
            "Works on mobile and desktop<br>"
            "Get Discovery and recommendations now<br>"
            "<span style='color:#444;'>6 months of history</span>"
            "</div>"
            "</div>",
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            "<div style='background:#0f0f0f;border:1px solid #A78BFA33;"
            "border-radius:12px;padding:18px;'>"
            "<div style='color:#A78BFA;font-weight:700;font-size:.82em;margin-bottom:10px;'>"
            "OPTION 2 — Full depth (12+ years)</div>"
            "<div style='color:#888;font-size:.83em;line-height:2;'>"
            "1. Go to <b style='color:#fff;'>spotify.com/account/privacy</b><br>"
            "2. Request <b style='color:#fff;'>Extended streaming history</b><br>"
            "3. Wait up to 30 days for the email<br>"
            "4. Upload both zips in the sidebar"
            "</div>"
            "</div>",
            unsafe_allow_html=True
        )

    st.markdown(
        "<div style='text-align:center;padding:28px 0 12px;'>"
        "<a href='" + auth_url + "' target='_self' "
        "style='background:#7C3AED;color:#fff;font-weight:800;"
        "padding:14px 36px;border-radius:30px;text-decoration:none;"
        "font-size:1em;display:inline-block;'>"
        "Start now — free, no account needed</a>"
        "</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<div style='text-align:center;padding:8px 0 32px;'>"
        "<div style='color:#333;font-size:.75em;line-height:1.7;max-width:480px;margin:0 auto;'>"
        "Your data never leaves your browser. "
        "MusicDNA does not store, share or transmit any of your Spotify data. "
        "All analysis runs locally in your session and is deleted when you close the tab."
        "</div>"
        "</div>",
        unsafe_allow_html=True
    )
