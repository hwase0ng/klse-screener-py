"""
HTML parsing utilities for KLSE Screener.
"""

import re


def clean_html(html: str) -> str:
    """Remove HTML tags from string."""
    if not html:
        return ""
    return re.sub(r"<[^>]+>", "", html).strip()
