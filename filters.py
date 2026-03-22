"""
filters.py — split user vs children's content, extended kids detection
"""
import re

# ── extended kids keywords ────────────────────────────────────────────────────

KIDS_ARTIST_KEYWORDS = {
    # french
    "henri dès", "henri des", "anny versini", "aldebert", "titounis",
    "les bisounours", "tchoupi", "les minouchkis", "dorothée",
    "chansons pour enfants", "comptines", "les coccinelles",
    "pil et face", "les razmoket", "le manège enchanté",
    # brazilian / portuguese
    "judson mancebo", "mundo bita", "galinha pintadinha", "palavra cantada",
    "patati patatá", "patati patata", "turma do balão mágico", "xuxa",
    "luluca", "bonde do tigrão",
    # indian / bollywood kids
    "jatin-lalit", "jatin lalit",
    # english kids
    "cocomelon", "pinkfong", "super simple songs", "baby shark",
    "the wiggles", "barney", "hi-5", "hi5", "mrs. rachel",
    "blippi", "chuggington", "bob the builder",
    # lullaby / generic
    "lullaby time", "marco bernardo", "beth mclaughlin",
    "música para bebés", "musica para bebes",
    "música para bebés exigentes", "musica para bebes exigentes",
    "music for babies", "baby music", "nursery rhymes",
    "sleeping baby", "lullabies for babies",
}

KIDS_TRACK_KEYWORDS = {
    # french
    "berceuse", "comptine", "dodo", "nounours", "petit lapin",
    "il était une fois", "il etait une fois",
    # shows / movies
    "frozen", "reine des neiges", "vaiana", "moana", "encanto",
    "hatrix", "miraculous", "winx", "peppa pig", "paw patrol",
    "pat patrouille", "bluey", "cocomelon", "minions",
    "toy story", "cars disney", "bambi", "dumbo", "aristocats",
    "roi lion", "lion king", "belle et la bête", "beauty and the beast",
    "aladdin", "cinderella", "cendrillon", "blanche neige",
    "snow white", "pinocchio", "peter pan", "nemo", "dory",
    "monsters inc", "ratatouille", "wall-e", "walle", "up pixar",
    "coco pixar", "soul pixar", "turning red", "brave pixar",
    "inside out", "vice versa",
    # generic
    "lullaby", "lullabies", "nursery rhyme", "nursery rhymes",
    "bébé", "bebe", "baby song", "kids song", "children song",
    "goodnight", "bonne nuit", "dors mon bébé",
}

KIDS_ALBUM_KEYWORDS = {
    "disney", "pixar", "dreamworks kids", "nickelodeon",
    "cartoon network", "baby einstein",
}


def _clean(s):
    return s.lower().strip() if s else ""


def is_kids_content(artist_name, track_name, album_name=""):
    a = _clean(artist_name)
    t = _clean(track_name)
    al = _clean(album_name)

    for kw in KIDS_ARTIST_KEYWORDS:
        if kw in a:
            return True
    for kw in KIDS_TRACK_KEYWORDS:
        if kw in t:
            return True
    for kw in KIDS_ALBUM_KEYWORDS:
        if kw in al or kw in a:
            return True
    return False


# ── culture fingerprints for child profile ────────────────────────────────────

CULTURE_ARTISTS = {
    "French": [
        "henri dès", "henri des", "anny versini", "aldebert", "titounis",
        "dorothée", "les bisounours", "comptines", "berceuse",
    ],
    "Brazilian / Portuguese": [
        "judson mancebo", "mundo bita", "galinha pintadinha",
        "patati patatá", "patati patata", "xuxa", "luluca",
    ],
    "Indian / Bollywood": [
        "jatin-lalit", "jatin lalit", "bole chudiyan", "kuch kuch",
        "dilbar", "nagada", "discowale",
    ],
    "English": [
        "cocomelon", "pinkfong", "super simple songs", "baby shark",
        "the wiggles", "blippi", "mrs. rachel",
    ],
    "African / Afrobeats": [
        "marco bernardo", "beth mclaughlin",
    ],
}


def detect_child_cultures(dfd):
    """Returns dict of culture -> hours for children's content df."""
    if dfd is None or dfd.empty:
        return {}
    cultures = {}
    for _, row in dfd.iterrows():
        a = _clean(row.get("artistName", ""))
        for culture, keywords in CULTURE_ARTISTS.items():
            if any(kw in a for kw in keywords):
                cultures[culture] = cultures.get(culture, 0) + row.get("ms", 0) / 3600000
    return {k: round(v, 1) for k, v in sorted(cultures.items(), key=lambda x: -x[1])}


# ── user / children split ─────────────────────────────────────────────────────

DAUGHTERS_ARTISTS = set(KIDS_ARTIST_KEYWORDS)

DAUGHTERS_TRACKS = {
    "i'll be there - instrumental",
    "i'll be there",
} | KIDS_TRACK_KEYWORDS


def is_daughters(record):
    """Legacy function name kept for compatibility."""
    a = _clean(record.get("artistName", ""))
    t = _clean(record.get("trackName", ""))
    al = _clean(record.get("albumName", ""))
    return is_kids_content(a, t, al)


def split(records):
    """Split records into (user_records, children_records)."""
    user, kids = [], []
    for r in records:
        if is_daughters(r):
            kids.append(r)
        else:
            user.append(r)
    return user, kids
