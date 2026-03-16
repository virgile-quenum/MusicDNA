import streamlit as st

VIOLET = "#7C3AED"
VL = "#A78BFA"
G = "#1DB954"

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
        "Or upload your Extended History zip for the full 12-year analysis</div>"
        "</div>",
        unsafe_allow_html=True
    )

    st.markdown("---")

    st.markdown(
        "<div style='text-align:center;margin-bottom:8px;'>"
        "<div style='color:#A78BFA;font-size:.75em;font-weight:700;"
        "text-transform:uppercase;letter-spacing:.1em;'>What your data reveals</div>"
        "</div>",
        unsafe_allow_html=True
    )

    c1, c2, c3, c4 = st.columns(4)
    shocks = [
        (c1, "45%", "of liked tracks are never played", "You collect music like books youll never read."),
        (c2, "1,343h", "of one users account was his daughters", "Spotify saw he became a parent before he posted it anywhere."),
        (c3, "2017-2018", "peak listening years for most users", "Life was different then. The data agrees."),
        (c4, "17%", "average skip rate", "Lower than you think. You are more committed than you admit."),
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

    st.markdown("---")

    st.markdown(
        "<div style='color:#A78BFA;font-size:.75em;font-weight:700;"
        "text-transform:uppercase;letter-spacing:.1em;margin-bottom:16px;'>"
        "Example — what your profile looks like</div>",
        unsafe_allow_html=True
    )

    col1, col2 = st.columns([1, 1])
    with col1:
        st.markdown(
            "<div style='background:linear-gradient(135deg,#0a0a1a,#12001a);"
            "border:1px solid #7C3AED;border-radius:14px;padding:24px;'>"
            "<div style='font-size:.7em;color:#555;text-transform:uppercase;"
            "letter-spacing:.1em;margin-bottom:8px;'>Musical Profile — Example</div>"
            "<div style='font-size:1.3em;font-weight:900;color:#fff;margin-bottom:6px;'>"
            "6,944h across 13 years</div>"
            "<div style='color:#777;font-size:.88em;line-height:1.9;'>"
            "7,644 unique artists<br>"
            "26,749 unique tracks<br>"
            "#1 all-time: <b style='color:#fff;'>Terry Callier</b><br>"
            "Peak year: <b style='color:#fff;'>2018</b> (954h)<br>"
            "Saturday is dominant — 18% of all listening<br>"
            "Discovery rate: ~380 new artists/year"
            "</div>"
            "</div>",
            unsafe_allow_html=True
        )

    with col2:
        st.markdown(
            "<div style='background:#0f0f0f;border:1px solid #1e1e1e;"
            "border-radius:14px;padding:24px;'>"
            "<div style='font-size:.7em;color:#555;text-transform:uppercase;"
            "letter-spacing:.1em;margin-bottom:12px;'>Musical Horoscope — Example</div>"
            "<div style='font-size:1.4em;'>♒</div>"
            "<div style='font-size:1.1em;font-weight:800;color:#A78BFA;margin:6px 0;'>"
            "The Feverish Archivist</div>"
            "<div style='color:#666;font-size:.83em;line-height:1.7;margin-bottom:12px;'>"
            "<b style='color:#888;'>Curse:</b> You build libraries you never open. "
            "45% of your likes have never been played.<br>"
            "<b style='color:#888;'>Gift:</b> When you find something, you commit. "
            "Your top track has 726 plays.<br>"
            "<b style='color:#888;'>Prediction:</b> Your collection keeps growing. "
            "Your actual listening does not. That day is not today."
            "</div>"
            "</div>",
            unsafe_allow_html=True
        )

    st.markdown("---")

    st.markdown(
        "<div style='background:#0f0505;border:1px solid #dc262633;"
        "border-radius:14px;padding:28px;margin-bottom:24px;'>"
        "<div style='color:#f87171;font-size:.75em;font-weight:700;"
        "text-transform:uppercase;letter-spacing:.1em;margin-bottom:10px;'>"
        "Parent Mode — unique to MusicDNA</div>"
        "<div style='font-size:1.2em;font-weight:800;color:#fff;margin-bottom:10px;'>"
        "Spotify knows when you became a parent.</div>"
        "<div style='color:#888;font-size:.9em;line-height:1.9;'>"
        "The data shows it clearly: one month your listening is yours, the next it shifts. "
        "Lullabies, nursery rhymes, children songs on loop at 3am. "
        "MusicDNA detects this transition automatically, shows you the exact month it happened, "
        "and tracks how your listening evolved from there.<br><br>"
        "<b style='color:#ccc;'>You posted the birth announcement. "
        "Spotify had already figured it out weeks earlier.</b>"
        "</div>"
        "</div>",
        unsafe_allow_html=True
    )

    st.markdown(
        "<div style='color:#A78BFA;font-size:.75em;font-weight:700;"
        "text-transform:uppercase;letter-spacing:.1em;margin-bottom:16px;'>"
        "9 analyses — none of them are in Wrapped</div>",
        unsafe_allow_html=True
    )

    features = [
        ("🏠", "Musical Profile",    "12 years of listening history. Your eras, your evolution, your numbers."),
        ("🎤", "Artists and Tracks", "Your all-time top artists and tracks with yearly breakdowns."),
        ("🕐", "Time Patterns",      "When you listen. Hour by hour, day by day. Your listening heatmap."),
        ("👶", "Parent Mode",        "How parenthood rewrote your Spotify. Detected automatically."),
        ("💔", "Likes Autopsy",      "45% of liked tracks never played. Who you think you are vs. reality."),
        ("📋", "Playlist Autopsy",   "Active playlists vs archives. Plus merge candidates."),
        ("😳", "Hall of Shame",      "Your most-played tracks judged. Sarcastically. Without mercy."),
        ("⭐", "Celebrity Twin",     "Which public figures share your exact musical taste."),
        ("🔮", "Musical Horoscope",  "Your sign, your curse, your gift, your prediction. From real data."),
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

    col1, col2 = st.columns(2)
    with col1:
        st.markdown(
            "<div style='background:#0f0f0f;border:1px solid #1DB95433;"
            "border-radius:12px;padding:20px;'>"
            "<div style='color:#1DB954;font-weight:700;font-size:.85em;margin-bottom:12px;'>"
            "OPTION 1 — Instant (recommended)</div>"
            "<div style='color:#888;font-size:.85em;line-height:2.2;'>"
            "Click Connect Spotify in the sidebar<br>"
            "Works on mobile and desktop<br>"
            "Get Discovery and recommendations immediately<br>"
            "<span style='color:#555;'>Limited to recent history (6 months)</span>"
            "</div>"
            "</div>",
            unsafe_allow_html=True
        )
    with col2:
        st.markdown(
            "<div style='background:#0f0f0f;border:1px solid #A78BFA33;"
            "border-radius:12px;padding:20px;'>"
            "<div style='color:#A78BFA;font-weight:700;font-size:.85em;margin-bottom:12px;'>"
            "OPTION 2 — Full depth (12+ years)</div>"
            "<div style='color:#888;font-size:.85em;line-height:2.2;'>"
            "1. Go to <b style='color:#fff;'>spotify.com/account/privacy</b><br>"
            "2. Request <b style='color:#fff;'>Extended streaming history</b><br>"
            "3. Wait up to 30 days for the email<br>"
            "4. Download the zip and upload it here"
            "</div>"
            "</div>",
            unsafe_allow_html=True
        )

    st.markdown(
        "<div style='text-align:center;padding:32px 0;'>"
        "<a href='" + auth_url + "' target='_self' "
        "style='background:#7C3AED;color:#fff;font-weight:800;"
        "padding:14px 36px;border-radius:30px;text-decoration:none;"
        "font-size:1em;display:inline-block;'>"
        "Start now — free, no account needed</a>"
        "</div>",
        unsafe_allow_html=True
    )
