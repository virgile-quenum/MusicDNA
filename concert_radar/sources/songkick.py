"""
concert_radar/sources/songkick.py — Phase 3.B: Songkick metro-area calendar
scraper. OFF BY DEFAULT — see README "Concert Radar > Sources" for the
terms-of-service note before turning this on.

Paginates https://www.songkick.com/en/metro-areas/{metro_id}-{slug}?page=N,
parses date / line-up / venue / city per event, stops once events are past
the requested end date. Respects a 1 req/s-per-host budget with exponential
backoff, and caches each fetched page for 24h on disk, keyed by URL.

Songkick's markup is not a stable public API and can change without notice;
if this stops returning events, the CSS selectors below are the first thing
to check.
"""

import os
import re

import requests
from bs4 import BeautifulSoup

from concert_radar import cache
from concert_radar.rate_limit import throttle, call_with_backoff

DEFAULT_METRO_URL = "https://www.songkick.com/en/metro-areas/28909-france-paris"
HOST = "www.songkick.com"

_UA = "Mozilla/5.0 (compatible; MusicDNA-ConcertRadar/1.0; personal use, non-commercial)"


def is_enabled():
    return os.environ.get("CONCERT_RADAR_ENABLE_SONGKICK", "").lower() in ("1", "true", "yes")


def _fetch_page(url):
    def do_request():
        throttle(HOST, min_interval=1.0)
        resp = requests.get(url, headers={"User-Agent": _UA}, timeout=10)
        if resp.status_code != 200:
            raise RuntimeError("http_%d" % resp.status_code)
        return resp.text

    return call_with_backoff(do_request)


def get_page_cached(url):
    """24h disk-cached raw HTML for a Songkick page, keyed by URL."""
    key = "songkick_page:" + url
    return cache.cached(key, cache.TTL_SONGKICK_PAGE, lambda: _fetch_page(url))


def _parse_date(el):
    """Songkick embeds machine-readable dates on <time datetime="...">."""
    time_tag = el.find("time")
    if time_tag and time_tag.get("datetime"):
        return time_tag["datetime"][:10]
    return None


def _parse_event(el):
    lineup_tag = el.select_one(".artists, .primary-artist, .event-listing-artists")
    lineup_text = lineup_tag.get_text(strip=True) if lineup_tag else ""

    venue_tag = el.select_one(".venue-name, .venue")
    venue = venue_tag.get_text(strip=True) if venue_tag else ""

    city_tag = el.select_one(".venue-location, .location")
    city = city_tag.get_text(strip=True) if city_tag else ""
    city = re.sub(r"^\W+", "", city)  # Songkick prefixes location with an icon char sometimes

    link_tag = el.select_one("a[href*='/concerts/']")
    url = ("https://www.songkick.com" + link_tag["href"]) if link_tag and link_tag.get("href") else ""

    date = _parse_date(el)

    if not (lineup_text and date):
        return None

    return {
        "date": date,
        "lineup_raw": lineup_text,
        "venue": venue,
        "city": city,
        "url": url,
        "ticket_url": url,
        "price": None,
        "status": "unknown",
        "source": "songkick",
    }


def collect_events(metro_url=DEFAULT_METRO_URL, date_from=None, date_to=None, max_pages=20):
    """
    Paginate the metro calendar. Returns (events, stats). Each event has
    lineup_raw as a single string (split it with matching.split_lineup
    before matching against artists — line-ups here are multi-performer).
    """
    events = []
    stats = {"pages_fetched": 0, "errors": [], "enabled": is_enabled()}

    if not is_enabled():
        stats["errors"].append("songkick_disabled_by_feature_flag")
        return events, stats

    for page_num in range(1, max_pages + 1):
        url = "%s?page=%d" % (metro_url, page_num)
        html = get_page_cached(url)
        if html is None:
            stats["errors"].append("fetch_failed:%s" % url)
            break
        stats["pages_fetched"] += 1

        soup = BeautifulSoup(html, "html.parser")
        event_els = soup.select("li.event-listings-element, .event-listings li")
        if not event_els:
            break  # no more events → past the last page

        page_dates = []
        for el in event_els:
            parsed = _parse_event(el)
            if not parsed:
                continue
            page_dates.append(parsed["date"])
            if date_from and parsed["date"] < date_from:
                continue
            if date_to and parsed["date"] > date_to:
                continue
            events.append(parsed)

        if date_to and page_dates and min(page_dates) > date_to:
            break  # whole page is already past the window we care about

    return events, stats
