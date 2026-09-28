# MusicDNA
your stream Analysis by DhalsimStream

## Concert Radar

Lists upcoming concerts near a chosen city/region (default: Île-de-France)
matched to what you actually listen to — not what's trending. New nav
section "Live", page `Concert Radar`.

### Setup

Env vars (Railway → Variables):

| Var | Required | Notes |
|---|---|---|
| `BANDSINTOWN_APP_ID` | Yes | Free — register any app name at bandsintown.com/api. Without it, Bandsintown results are empty and the KPI header shows `missing_app_id`. |
| `LASTFM_API_KEY` | Already required elsewhere in the app | Reused for the "Close to my taste" tab (Last.fm `artist.getSimilar`). |
| `CONCERT_RADAR_ENABLE_SONGKICK` | No, default off | Set to `true` to turn on the Songkick scraper. See ToS note below before enabling. |
| `ANTHROPIC_API_KEY` | No, not wired in the MVP | Reserved for the optional V3 LLM disambiguation pass on "To verify" items. |

New Python deps: `pyyaml`, `openpyxl`, `beautifulsoup4` (added to `requirements.txt`).

### Sources and their terms-of-service notes

- **Bandsintown** — public per-artist events API, used as documented
  (`GET /artists/{name}/events`). No scraping involved.
- **Songkick** (feature-flagged, `CONCERT_RADAR_ENABLE_SONGKICK`) — this is
  an **HTML scrape** of the public metro-area calendar page, not an
  official API (Songkick's partner API requires an approved application we
  don't have). Songkick's terms of service restrict automated access; this
  is built for personal, non-commercial use with a conservative 1
  req/s-per-host budget, exponential backoff and a 24h cache to minimise
  load. Turn it on knowing that: (a) it can be blocked or break without
  notice if Songkick changes its markup, and (b) sustained/commercial use
  would need Songkick's explicit permission. Off by default for this
  reason.
- **Ticketmaster Discovery API** — not implemented yet (V2). Official,
  keyed, generous free tier — the natural next source, especially for
  arena-scale Caribbean/Congolese/konpa shows Bandsintown under-covers.

Each source fails independently: a Bandsintown outage or a missing API key
never blocks Songkick results (or vice-versa), and the KPI header always
shows which sources ran and which failed, with the error.

### Scoring

- **Affinity score** (who counts as "my artists"):
  `log1p(total_hours) × recency_weight`, where
  `recency_weight = 0.5 + 0.5 × (hours_last_12m / total_hours)`.
  Rationale: raw total hours reward old loyalty, not current intent — an
  artist you played 169 hours of years ago and haven't touched since should
  not outrank someone you're actively listening to now. Eligible "my
  artists" = affinity rank in the top 200 AND ≥1 total hour (both
  configurable — see `concert_radar/profile.py`,
  `DEFAULT_TOP_RANK_LIMIT` / `DEFAULT_MIN_HOURS`).
- Deceased artists / ended groups are excluded from "my artists" regardless
  of hours, via a MusicBrainz life-span check (30-day cache) plus a manual
  `concert_radar/overrides.yaml` for cases MusicBrainz misses or gets wrong.
- **Similar-artist score**: `lastfm_match × parent_affinity` — a Last.fm
  match score alone doesn't account for how much you actually listen to the
  seed artist; weighting by their affinity keeps a 95%-match to an artist
  you played twice from outranking an 80%-match to your most-played artist.
- **Confidence** (why an event lands in "To verify"): homonym risk (short
  name + genre mismatch), tribute-act wording, venue name that's actually a
  production/booking company, single-source events with an inconsistent
  line-up, and artists you listen to for under 1 hour. See
  `concert_radar/matching.py::classify_match` and
  `tests/concert_radar/test_matching.py` for the exact cases this is tuned
  against (Eve at Bataclan vs. Noname at Parc Floral, Maitre Gim's → GIMS,
  SOLEXPROD/Madoky as fake venues, Mario Canonge's 16-date residency, etc.).

### Editable config

- `concert_radar/aliases.yaml` — line-up name → canonical Spotify-history
  name (e.g. `maitre gims: gims`).
- `concert_radar/overrides.yaml` — manual touring-status overrides.
- `concert_radar/region_communes.yaml` — the commune list used to filter
  events into the target region (default Île-de-France + départements
  75/77/78/91/92/93/94/95 by postcode prefix).

### Not built yet (V2/V3 — stubbed, see code comments for interfaces)

- Ticketmaster Discovery API source.
- Venue-scraper framework (New Morning, La Cigale, Cabaret Sauvage, Le
  Trabendo, La Marbrerie, Le Tamanoir, La Cave Argenteuil, Paul B, Le 360
  Paris Music Factory) and seasonal-festival adapters (Villes des Musiques
  du Monde, Africolor, Blues sur Seine, Jazz sur Seine, Sons d'hiver).
- Niche genre agendas (reggae.fr, bizouk.com).
- "Small venues & festivals" tab: genre-fit scoring for unmatched events.
- LLM extractor for unstructured venue pages.
- Weekly digest, sell-out-risk alerts, multi-city support, price/genre
  filters.

### Tests

```
pip install -r requirements.txt pytest
pytest tests/concert_radar/ -v
```
40 tests, all offline (MusicBrainz/Last.fm calls are mocked or bypassed via
`check_life_span=False` where the test isn't specifically about that
lookup).
