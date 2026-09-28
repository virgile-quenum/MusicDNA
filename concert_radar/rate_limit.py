"""
concert_radar/rate_limit.py — per-host throttling with exponential backoff.

Used by the Songkick scraper (spec: at most 1 req/s per host). Bandsintown's
own API is generous enough that we don't throttle it, but the helper is
generic so any future source can reuse it.
"""

import time
import threading

_last_call_by_host = {}
_lock = threading.Lock()


def throttle(host, min_interval=1.0):
    """Block until at least `min_interval` seconds have passed since the last
    call to this host from this process."""
    with _lock:
        last = _last_call_by_host.get(host, 0.0)
        wait = min_interval - (time.time() - last)
        if wait > 0:
            time.sleep(wait)
        _last_call_by_host[host] = time.time()


def call_with_backoff(fn, max_retries=3, base_delay=1.5):
    """Call fn() with exponential backoff on exception. Returns fn()'s result,
    or None if every attempt failed."""
    for attempt in range(max_retries):
        try:
            return fn()
        except Exception:
            if attempt == max_retries - 1:
                return None
            time.sleep(base_delay * (2 ** attempt))
    return None
