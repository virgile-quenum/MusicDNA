"""
filter_manager.py
Manages the artist/track exclusion list — persisted in a JSON file.
Allows adding/removing artists from the Streamlit UI without touching code.
"""

import json, os
import streamlit as st

FILTER_FILE = "data/exclusions.json"

# ── Default exclusions (seeded from our analysis) ──────────────────────────
DEFAULT_EXCLUSIONS = {
    "artists": {
        # Kids storytellers
        "Alain Royer":          "kids_stories",
        "Henri Dès":            "kids_music",
        "Les Petites Tounes":   "kids_music",
        "Gérard Delahaye":      "kids_music",
        "Monde des Titounis":   "kids_music",
        "Anny Versini":         "kids_music",
        "Magguy Faraux":        "kids_music",
        "Gérard Philipe":       "kids_stories",
        "Gallimard Jeunesse":   "kids_stories",
        "HeyKids Comptine Pour Bébé": "kids_music",
        "Le Choeur des Enfants": "kids_music",
        "Les plus belles comptines d'Okoo": "kids_music",
        "La Reine des chansons pour enfants et bébés": "kids_music",
        # Bollywood (daughters)
        "Jatin-Lalit":          "daughters_bollywood",
        "Pritam":               "daughters_bollywood",
        "Sanjay Leela Bhansali":"daughters_bollywood",
        "Neha Kakkar":          "daughters_bollywood",
        "Panjabi MC":           "daughters_bollywood",
        "Sonu Nigam":           "daughters_bollywood",
        "Kumar Sanu":           "daughters_bollywood",
        "Alka Yagnik":          "daughters_bollywood",
        "Lata Mangeshkar":      "daughters_bollywood",
        "Udit Narayan":         "daughters_bollywood",
        "Shankar-Ehsaan-Loy":   "daughters_bollywood",
        "Shreya Ghoshal":       "daughters_bollywood",
        # Other daughters
        "GIMS":                 "daughters_other",
        "Meryl":                "daughters_other",
    },
    "tracks": [
        # Track-level exclusions: [trackName, artistName]
        ["On se connaît", "Youssoupha"],
    ],
    "categories": {
        "kids_stories":         "Kids — Stories & audiobooks",
        "kids_music":           "Kids — Songs & nursery rhymes",
        "daughters_bollywood":  "Daughters — Bollywood",
        "daughters_other":      "Daughters — Other",
    }
}

CATEGORY_COLORS = {
    "kids_stories":         "#9B59B6",
    "kids_music":           "#E74C3C",
    "daughters_bollywood":  "#F39C12",
    "daughters_other":      "#E67E22",
}

def load_exclusions():
    if os.path.exists(FILTER_FILE):
        with open(FILTER_FILE, "r") as f:
            return json.load(f)
    # First run — seed with defaults
    save_exclusions(DEFAULT_EXCLUSIONS)
    return DEFAULT_EXCLUSIONS

def save_exclusions(excl):
    os.makedirs("data", exist_ok=True)
    with open(FILTER_FILE, "w") as f:
        json.dump(excl, f, indent=2, ensure_ascii=False)

def apply_exclusions(df, excl, include_kids=False):
    """Filter dataframe based on current exclusions."""
    if include_kids:
        return df
    excluded_artists = set(excl["artists"].keys())
    excluded_tracks  = {(t[0], t[1]) for t in excl.get("tracks", [])}
    mask = ~df["artistName"].isin(excluded_artists)
    for track, artist in excluded_tracks:
        mask &= ~((df["trackName"] == track) & (df["artistName"] == artist))
    return df[mask]

def render_filter_manager(df):
    """Full Streamlit UI for managing exclusions."""
    st.markdown("# ⚙️ Content Filter Manager")
    st.markdown("*Add or remove artists from your analysis. Changes are saved automatically.*")

    excl = load_exclusions()
    categories = excl.get("categories", DEFAULT_EXCLUSIONS["categories"])

    # ── Currently excluded ────────────────────────────────────────────────
    st.markdown("### 🚫 Currently Excluded")

    # Group by category
    by_cat = {}
    for artist, cat in excl["artists"].items():
        by_cat.setdefault(cat, []).append(artist)

    cols = st.columns(len(categories))
    for i, (cat_key, cat_label) in enumerate(categories.items()):
        with cols[i % len(categories)]:
            color = CATEGORY_COLORS.get(cat_key, "#888")
            artists_in_cat = by_cat.get(cat_key, [])
            st.markdown(f"""
            <div style='background:#1a1a1a;border:1px solid {color}33;border-radius:10px;
                        padding:14px;margin-bottom:12px;'>
              <div style='color:{color};font-size:.72em;font-weight:700;text-transform:uppercase;
                          letter-spacing:.07em;margin-bottom:10px;'>{cat_label}</div>
              {''.join(f"<div style='font-size:.82em;padding:3px 0;border-bottom:1px solid #222;'>{a}</div>" for a in sorted(artists_in_cat))}
              <div style='color:#555;font-size:.75em;margin-top:8px;'>{len(artists_in_cat)} artists</div>
            </div>""", unsafe_allow_html=True)

    # Track-level exclusions
    if excl.get("tracks"):
        st.markdown("**Track-level exclusions:**")
        for t in excl["tracks"]:
            st.markdown(f"<span style='color:#888;font-size:.85em;'>✕ {t[0]} — {t[1]}</span>", unsafe_allow_html=True)

    st.markdown("---")

    # ── Add artist ────────────────────────────────────────────────────────
    st.markdown("### ➕ Exclude an Artist")

    all_artists = sorted(df["artistName"].dropna().unique().tolist())
    already_excluded = set(excl["artists"].keys())
    available = [a for a in all_artists if a not in already_excluded]

    col1, col2, col3 = st.columns([3, 2, 1])
    with col1:
        artist_to_add = st.selectbox("Select artist", ["— choose —"] + available, key="add_artist")
    with col2:
        category = st.selectbox("Category", list(categories.keys()),
                                format_func=lambda x: categories[x], key="add_cat")
    with col3:
        st.markdown("<div style='margin-top:28px'>", unsafe_allow_html=True)
        if st.button("Exclude", use_container_width=True):
            if artist_to_add != "— choose —":
                excl["artists"][artist_to_add] = category
                save_exclusions(excl)
                st.success(f"✅ {artist_to_add} excluded")
                st.rerun()

    # ── Remove artist ─────────────────────────────────────────────────────
    st.markdown("### ✅ Re-include an Artist")

    col4, col5 = st.columns([4, 1])
    with col4:
        artist_to_remove = st.selectbox(
            "Select excluded artist to re-include",
            ["— choose —"] + sorted(list(excl["artists"].keys())),
            key="remove_artist"
        )
    with col5:
        st.markdown("<div style='margin-top:28px'>", unsafe_allow_html=True)
        if st.button("Re-include", use_container_width=True):
            if artist_to_remove != "— choose —":
                del excl["artists"][artist_to_remove]
                save_exclusions(excl)
                st.success(f"✅ {artist_to_remove} re-included")
                st.rerun()

    # ── Quick scan: potential kids content not yet flagged ─────────────────
    st.markdown("---")
    st.markdown("### 🔍 Auto-detected — Possible Children's Content")
    st.markdown("<div style='color:#888;font-size:.82em;margin-bottom:12px'>Artists not yet excluded whose track names contain children's keywords. Review and exclude if needed.</div>", unsafe_allow_html=True)

    CHILDREN_KW = [
        'comptine','berceuse','enfant','titounis','disney','frozen','encanto',
        'peppa','paw patrol','teletubbies','babar','winnie','reine des neiges',
        'blanche neige','cendrillon','chaperon','lutin','maternelle','lullaby',
        'nursery','bedtime','kids','children','bébé','comptines','okoo'
    ]

    suspects = {}
    for _, row in df.iterrows():
        if row["artistName"] in already_excluded:
            continue
        tl = str(row.get("trackName", "")).lower()
        if any(k in tl for k in CHILDREN_KW):
            suspects[row["artistName"]] = suspects.get(row["artistName"], 0) + 1

    if suspects:
        for artist, count in sorted(suspects.items(), key=lambda x: -x[1]):
            c1, c2 = st.columns([5, 1])
            with c1:
                st.markdown(f"<div style='font-size:.85em;padding:4px 0;'>{artist} <span style='color:#888'>— {count} matching plays</span></div>", unsafe_allow_html=True)
            with c2:
                if st.button("Exclude", key=f"susp_{artist}"):
                    excl["artists"][artist] = "kids_music"
                    save_exclusions(excl)
                    st.rerun()
    else:
        st.info("No additional children's content detected.")

    # ── Reset to defaults ─────────────────────────────────────────────────
    st.markdown("---")
    if st.button("🔄 Reset to default exclusions", type="secondary"):
        save_exclusions(DEFAULT_EXCLUSIONS)
        st.success("Reset to defaults")
        st.rerun()
