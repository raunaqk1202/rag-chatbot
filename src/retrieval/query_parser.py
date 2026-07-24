"""
Query Parser — Extracts entities (like target scheme name) from user queries.
"""

import re
from typing import Optional
from src.utils.config import SCHEME_NAMES

# Pre-compile regexes for each scheme based on its distinct keywords.
# We map simple keywords to the exact scheme name.
SCHEME_MAPPING = {
    r"large\s*cap": "HDFC Large Cap Fund – Direct Growth",
    r"mid\s*cap": "HDFC Mid Cap Fund – Direct Growth",
    r"small\s*cap": "HDFC Small Cap Fund – Direct Growth",
    r"gold": "HDFC Gold ETF Fund of Fund – Direct Growth",
    r"silver": "HDFC Silver ETF FoF – Direct Growth",
}


def extract_scheme_name(query: str) -> Optional[str]:
    """
    Identify specific fund mentioned in the query.
    Returns the exact scheme_name from config if found, otherwise None.
    """
    query_lower = query.lower()

    # Try mapping patterns first
    for pattern, exact_name in SCHEME_MAPPING.items():
        if re.search(pattern, query_lower):
            return exact_name

    # Fallback: check if the exact scheme name is somehow in the query
    for name in SCHEME_NAMES:
        if name.lower() in query_lower:
            return name

    return None
