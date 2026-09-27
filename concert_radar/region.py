"""
concert_radar/region.py — configurable region filter (default: Île-de-France).

Matches on city name or postcode prefix. The commune list is intentionally
not exhaustive — it's the ~150 most relevant IDF communes for concerts
(county towns, Paris arrondissements, the usual venue clusters). Add to it
in region_communes.yaml if a real event gets missed; don't hardcode more
here.
"""

import os
import unicodedata

import yaml

_REGION_PATH = os.path.join(os.path.dirname(__file__), "region_communes.yaml")

IDF_DEPARTEMENT_PREFIXES = ("75", "77", "78", "91", "92", "93", "94", "95")


def _clean(s):
    if not s:
        return ""
    n = unicodedata.normalize("NFKD", s)
    n = "".join(c for c in n if not unicodedata.combining(c))
    return n.lower().strip()


def load_region_communes():
    """Returns a set of cleaned commune names for the default region."""
    if not os.path.exists(_REGION_PATH):
        return set()
    with open(_REGION_PATH, "r", encoding="utf-8") as f:
        raw = yaml.safe_load(f) or {}
    communes = raw.get("communes", [])
    return {_clean(c) for c in communes}


def postcode_in_region(postcode, departement_prefixes=IDF_DEPARTEMENT_PREFIXES):
    if not postcode:
        return False
    digits = "".join(ch for ch in str(postcode) if ch.isdigit())
    if len(digits) < 2:
        return False
    return digits[:2] in departement_prefixes


def event_in_region(city, postcode, region_communes=None,
                     departement_prefixes=IDF_DEPARTEMENT_PREFIXES):
    """True if this event's city/postcode falls inside the target region."""
    region_communes = region_communes if region_communes is not None else load_region_communes()
    if postcode_in_region(postcode, departement_prefixes):
        return True
    if not city:
        return False
    return _clean(city) in region_communes
