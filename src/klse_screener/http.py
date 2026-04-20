"""
Rate-limited HTTP client for KLSE Screener.

Features:
- 2-second rate limiting between requests
- Custom User-Agent header
- Connection timeout (15 seconds)
- In-memory caching with TTL
"""

import time
import urllib.request
from typing import Dict

# Rate limiting
_MIN_INTERVAL = 2.0  # seconds between requests
_LAST_REQUEST_TIME: float = 0.0

# Cache
_CACHE: Dict[str, dict] = {}
_CACHE_TTL = 600  # 10 minutes

# Headers
_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) Chrome/131.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.9",
}


def fetch_url(url: str, cache_key: str) -> str:
    """
    Fetch a URL with caching and rate limiting.

    Args:
        url: URL to fetch
        cache_key: Key for caching the response

    Returns:
        HTML content as string
    """
    global _LAST_REQUEST_TIME

    now = time.time()

    # Check cache
    if cache_key in _CACHE and (now - _CACHE[cache_key]["ts"]) < _CACHE_TTL:
        return _CACHE[cache_key]["html"]

    # Rate limiting
    elapsed = now - _LAST_REQUEST_TIME
    if elapsed < _MIN_INTERVAL:
        time.sleep(_MIN_INTERVAL - elapsed)

    # Fetch
    req = urllib.request.Request(url, headers=_HEADERS)
    with urllib.request.urlopen(req, timeout=15) as resp:
        html = resp.read().decode("utf-8", errors="replace")

    # Update timing and cache
    _LAST_REQUEST_TIME = time.time()
    _CACHE[cache_key] = {"html": html, "ts": _LAST_REQUEST_TIME}

    return html


def reset_rate_limit() -> None:
    """Reset rate limiter (useful for testing)."""
    global _LAST_REQUEST_TIME
    _LAST_REQUEST_TIME = 0.0


def clear_cache() -> None:
    """Clear the HTTP cache."""
    _CACHE.clear()
