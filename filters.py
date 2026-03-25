"""
filters.py — split user vs children's content, extended kids detection
"""

KIDS_ARTIST_KEYWORDS = {
    # french
    "henri dès", "henri des", "anny versini", "aldebert", "titounis",
    "les bisounours", "tchoupi", "les minouchkis", "dorothée",
    "chansons pour enfants", "comptines", "les coccinelles",
    "pil et face", "les razmoket", "le manège enchanté",
    "petit ours brun", "monde des titounis", "alain royer",
    "les chansons de", "comptines tv",
    # lullaby / relaxation / baby
    "lullaby time", "marco bernardo", "beth mclaughlin",
    "música para bebés", "musica para bebes",
    "música para bebés exigentes", "musica para bebes exigentes",
    "music for babies", "baby music from", "baby music",
    "nursery rhymes", "sleeping baby", "lullabies for babies",
    "baby einstein", "miracle tones", "baby lullaby",
    "relaxing music for babies", "lullaby babies",
    "música para bebês", "musica para bebes",
    "i'm in records", "baby music from i'm in records",
    "percussioney", "batukem tukada",
    # english kids
    "cocomelon", "pinkfong", "super simple songs", "baby shark",
    "the wiggles", "barney", "hi-5", "hi5", "mrs. rachel",
    "blippi", "chuggington", "bob the builder",
    "little moons", "bobby celesti", "kiboomers",
    "teddy's wonderland", "teddy wonderland",
    "the kiboomers", "carmen campagne",
    "arlen ness", "judson mancebo",
    # brazilian / portuguese
    "mundo bita", "galinha pintadinha", "palavra cantada",
    "patati patatá", "patati patata", "turma do balão mágico", "xuxa",
    "luluca", "bonde do tigrão",
    # generic
    "baby songs", "kids songs", "children songs",
    "toddler songs", "preschool songs",
}

KIDS_TRACK_KEYWORDS = {
    # french
    "berceuse", "comptine", "dodo", "nounours", "petit lapin",
    "il était une fois", "il etait une fois",
    "ainsi font font font", "ainsi font",
    "batuqui cha cha cha",
    # shows / movies
    "frozen", "reine des neiges", "vaiana", "moana", "encanto",
    "hatrix", "miraculous", "winx", "peppa pig", "paw patrol",
    "pat patrouille", "bluey", "cocomelon", "minions",
    "toy story", "cars disney", "bambi", "dumbo", "aristocats",
    "roi lion", "lion king", "belle et la bête", "beauty and the beast",
    "aladdin", "cinderella", "cendrillon", "blanche neige",
    "snow white", "pinocchio", "peter pan", "nemo", "dory",
    "monsters inc", "ratatouille", "wall-e", "walle",
    "coco pixar", "soul pixar", "turning red", "brave pixar",
    "inside out", "vice versa",
    # generic
    "lullaby", "lullabies", "nursery rhyme", "nursery rhymes",
    "bébé", "bebe ", "baby song", "kids song", "children song",
    "goodnight song", "bonne nuit", "dors mon bébé",
}

KIDS_ALBUM_KEYWORDS = {
    "disney", "pixar", "dreamworks kids", "nickelodeon",
    "cartoon network", "baby einstein",
}

# ── Artists to always classify as kids regardless of other signals ────────────
KIDS_ARTIST_EXACT = {
    "alain royer", "bobby celesti", "marco bernardo", "beth mclaughlin",
    "judson mancebo", "little moons", "kiboomers", "the kiboomers",
    "teddy's wonderland", "teddy wonderland", "arlen ness",
    "carmen compagne", "carmen campagne", "monde des titounis",
    "comptines tv", "miracle tones", "percussioney", "batukem tukada",
    "lullaby time", "música para bebés exigentes de i'm in records",
    "baby music from i'm in records",
}


def _clean(s):
    return s.lower().strip() if s else ""


def is_kids_content(artist_name, track_name, album_name=""):
    a  = _clean(artist_name)
    t  = _clean(track_name)
    al = _clean(album_name)

    # Exact match first — fastest and most reliable
    if a in KIDS_ARTIST_EXACT:
        return True

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
        "dorothée", "les bisounours", "comptines", "alain royer",
        "monde des titounis", "comptines tv",
    ],
    "Brazilian / Portuguese": [
        "judson mancebo", "mundo bita", "galinha pintadinha",
        "patati patatá", "patati patata", "xuxa", "luluca",
    ],
    "Indian / Bollywood": [
        "jatin-lalit", "jatin lalit", "bole chudiyan", "kuch kuch",
    ],
    "English": [
        "cocomelon", "pinkfong", "super simple songs", "baby shark",
        "the wiggles", "blippi", "mrs. rachel", "kiboomers",
        "the kiboomers", "little moons", "bobby celesti",
        "teddy's wonderland", "arlen ness", "carmen campagne",
    ],
}


def detect_child_cultures(dfd):
    if dfd is None or dfd.empty:
        return {}
    cultures = {}
    for _, row in dfd.iterrows():
        a = _clean(row.get("artistName", ""))
        for culture, keywords in CULTURE_ARTISTS.items():
            if any(kw in a for kw in keywords):
                cultures[culture] = cultures.get(culture, 0) + row.get("ms", 0) / 3600000
    return {k: round(v, 1) for k, v in sorted(cultures.items(), key=lambda x: -x[1])}


DAUGHTERS_TRACKS = {
    "i'll be there - instrumental",
    "i'll be there",
} | KIDS_TRACK_KEYWORDS


def is_daughters(record):
    a  = _clean(record.get("artistName", ""))
    t  = _clean(record.get("trackName", ""))
    al = _clean(record.get("albumName", ""))
    return is_kids_content(a, t, al)


def split(records):
    user, kids = [], []
    for r in records:
        if is_daughters(r):
            kids.append(r)
        else:
            user.append(r)
    return user, kids
