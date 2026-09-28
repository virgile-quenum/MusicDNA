"""
concert_radar/matching.py — name normalisation, line-up splitting, alias
resolution, event dedup and confidence scoring.

This is the trickiest part of Concert Radar: Bandsintown/Songkick data is
messy free text, and the failure modes are always the same shape (homonyms,
tribute acts, agency names posing as venues, alias mismatches). See
tests/concert_radar/test_matching.py for the concrete cases this file
exists to get right.
"""

import os
import re

import yaml

from concert_radar.profile import normalise_name  # single source of truth

_ALIASES_PATH = os.path.join(os.path.dirname(__file__), "aliases.yaml")

# Known duos/pairs whose name legitimately contains a splitting delimiter
# (e.g. "&") and must NOT be split into two performers. Match case-insensitively
# on the whole substring before generic splitting runs.
KNOWN_DUOS = {
    "fred and gustavo",  # spec example: "Fred & Gustavo" (post-normalisation)
}

# Venue names that are actually production/booking companies, not venues —
# added by hand because the generic keyword heuristic below won't catch them.
KNOWN_COMPANY_VENUES = {
    "solexprod", "madoky",
}

_COMPANY_KEYWORDS = ("prod", "production", "booking", "management", "agency")

_TRIBUTE_KEYWORDS = (
    "hommage", "tribute", "les classiques de", "the music of",
)

# Homonym risk: names this short (normalised, no spaces) or on this explicit
# list get flagged as risky UNLESS the rest of the line-up/venue fits the
# artist's known genre.
_COMMON_SHORT_NAMES = {"kim", "joe", "eve", "dice", "noname"}


# ── Alias table ──────────────────────────────────────────────────────────────

def load_aliases():
    """
    aliases.yaml format (normalised or raw keys, both work):
      "maitre gims": gims
      fianso: sofiane
      "matthieu chedid": "-m-"
    Returns dict of normalised_alias -> normalised_canonical.
    """
    if not os.path.exists(_ALIASES_PATH):
        return {}
    with open(_ALIASES_PATH, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    return {normalise_name(k): normalise_name(v) for k, v in raw.items()}


def resolve_alias(name, aliases=None):
    """Return the canonical normalised name for `name`, following the alias
    table if one exists, else just normalising."""
    aliases = aliases if aliases is not None else load_aliases()
    norm = normalise_name(name)
    return aliases.get(norm, norm)


# ── Line-up splitting ────────────────────────────────────────────────────────

_SPLIT_RE = re.compile(r"\s*(?:,|/|\+|&|\bx\b)\s*", flags=re.IGNORECASE)


def split_lineup(text, known_duos=None):
    """
    Split a raw line-up string into individual performer names, on
    "/", ",", "+", "&" and standalone "x" — except known duos, which are
    protected first so they survive as one performer.
    """
    if not text:
        return []
    known_duos = known_duos if known_duos is not None else KNOWN_DUOS

    working = text
    placeholders = {}
    for i, duo in enumerate(known_duos):
        pattern = re.compile(re.escape(duo).replace(r"\ and\ ", r"\s*(?:&|and)\s*"), re.IGNORECASE)
        # also try the literal duo string as given (handles "&" directly in config)
        for candidate_pattern in (pattern, re.compile(re.escape(duo), re.IGNORECASE)):
            m = candidate_pattern.search(working)
            if m:
                placeholder = "__DUO_%d__" % i
                working = candidate_pattern.sub(placeholder, working)
                placeholders[placeholder] = m.group(0)
                break

    parts = _SPLIT_RE.split(working)
    result = []
    for p in parts:
        p = p.strip()
        if not p:
            continue
        if p in placeholders:
            result.append(placeholders[p])
        else:
            result.append(p)
    return result


# ── Tribute / company-venue detection ────────────────────────────────────────

def is_tribute(text):
    if not text:
        return False
    t = text.lower()
    return any(kw in t for kw in _TRIBUTE_KEYWORDS)


def is_company_venue(venue_name):
    """True if the 'venue' name looks like a production/booking company
    rather than an actual place, or is missing entirely."""
    if not venue_name or not venue_name.strip():
        return True
    v = venue_name.lower().strip()
    if v in KNOWN_COMPANY_VENUES:
        return True
    return any(kw in v for kw in _COMPANY_KEYWORDS)


def is_homonym_risk(performer_name, genre_fits):
    """
    Flag short/common names as risky UNLESS the surrounding context (rest
    of line-up, venue programming) fits the artist's known genre — e.g.
    "Eve" at a hip-hop night is fine, "Noname" on an electro bill is not.
    """
    norm = normalise_name(performer_name).replace(" ", "")
    risky_name = norm in _COMMON_SHORT_NAMES or (0 < len(norm) <= 4)
    return risky_name and not genre_fits


# ── Confidence classification ────────────────────────────────────────────────

def classify_match(performer_raw, event_title="", venue_name="",
                    genre_fits=True, sources_count=1, lineup_consistent=True,
                    user_hours=0.0, is_headliner=True):
    """
    Returns (confidence, reasons) where confidence is "high" or "review",
    and reasons is a list of short machine-readable flags (empty if high).
    """
    reasons = []

    if is_tribute(event_title) or is_tribute(performer_raw):
        reasons.append("tribute_detected")

    if is_company_venue(venue_name):
        reasons.append("venue_is_company")

    if is_homonym_risk(performer_raw, genre_fits):
        reasons.append("homonym_risk")

    if sources_count <= 1 and not lineup_consistent:
        reasons.append("single_source_inconsistent_lineup")

    if user_hours < 1.0:
        reasons.append("low_listening_hours")

    if not is_headliner:
        reasons.append("not_headliner")

    if reasons:
        return "review", reasons
    return "high", []


# ── Event dedup ──────────────────────────────────────────────────────────────

def _event_key(event):
    return (
        str(event.get("date", "")),
        normalise_name(event.get("venue", "")),
        normalise_name(event.get("headliner", "")),
    )


def dedupe_events(events):
    """
    events: list of dicts with at least date, venue, headliner, source
    (a single source name string). Merges duplicates found across sources
    into one event with source -> list of sources.
    """
    merged = {}
    order = []
    for ev in events:
        key = _event_key(ev)
        if key not in merged:
            merged[key] = dict(ev)
            merged[key]["sources"] = [ev.get("source")] if ev.get("source") else []
            order.append(key)
        else:
            existing = merged[key]
            src = ev.get("source")
            if src and src not in existing["sources"]:
                existing["sources"].append(src)
            # fill in any fields the first source was missing
            for field in ("price", "status", "url", "ticket_url"):
                if not existing.get(field) and ev.get(field):
                    existing[field] = ev[field]
    return [merged[k] for k in order]


# ── Residency grouping (spec trap: Mario Canonge, 16 weekly dates) ─────────

def group_residencies(events, min_occurrences=4):
    """
    Groups events sharing the same normalised (headliner, venue) into a
    single "residency" row when they occur `min_occurrences` times or more,
    keeping the earliest date as the anchor and noting the date range and
    count. Non-residency events pass through unchanged.
    """
    by_pair = {}
    for ev in events:
        key = (normalise_name(ev.get("headliner", "")), normalise_name(ev.get("venue", "")))
        by_pair.setdefault(key, []).append(ev)

    result = []
    for key, group in by_pair.items():
        if len(group) >= min_occurrences:
            dates = sorted(str(ev.get("date", "")) for ev in group)
            head = dict(group[0])
            head["date"] = dates[0]
            head["residency"] = True
            head["residency_note"] = "Residency: %d dates, %s to %s" % (
                len(group), dates[0], dates[-1]
            )
            head["residency_dates"] = dates
            result.append(head)
        else:
            result.extend(group)
    return result
