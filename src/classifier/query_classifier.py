"""
Query Classifier — filters queries into FACTUAL, ADVISORY, PII_BLOCKED, or OUT_OF_SCOPE.
"""

import re
from enum import Enum


class QueryType(Enum):
    FACTUAL = "FACTUAL"
    ADVISORY = "ADVISORY"
    PII_BLOCKED = "PII_BLOCKED"
    OUT_OF_SCOPE = "OUT_OF_SCOPE"


ADVISORY_KEYWORDS = [
    "should i invest",
    "which is better",
    "recommend",
    "worth it",
    "good investment",
    "best fund",
    "suggest",
    "better option",
    "compare returns",
    "which one",
    "buy or sell",
    "right time",
    "safe to invest",
]

# PII regex patterns
PII_PATTERNS = [
    r"[A-Z]{5}[0-9]{4}[A-Z]{1}",  # PAN
    r"\b\d{4}\s?\d{4}\s?\d{4}\b",  # Aadhaar
    r"\b[6-9]\d{9}\b",  # Phone
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b",  # Email
    r"\b\d{9,18}\b",  # Account No
]


def _check_advisory(query: str) -> bool:
    """Keyword + pattern matching for advisory intent."""
    q_lower = query.lower()
    for keyword in ADVISORY_KEYWORDS:
        if keyword in q_lower:
            return True
    return False


def _check_pii(query: str) -> bool:
    """Regex for PAN, Aadhaar, phone, email, account numbers."""
    for pattern in PII_PATTERNS:
        if re.search(pattern, query, re.IGNORECASE):
            return True
    return False


def _check_scope(query: str) -> bool:
    """Relevance check for mutual fund domain."""
    q_lower = query.lower()

    # Block queries about unsupported AMCs
    unsupported_amcs = ["sbi", "icici", "axis", "kotak", "nippon", "tata", "mirae"]
    for amc in unsupported_amcs:
        if re.search(r"\b" + amc + r"\b", q_lower):
            return False

    scope_keywords = [
        "fund",
        "nav",
        "expense ratio",
        "exit load",
        "sip",
        "lumpsum",
        "return",
        "cagr",
        "aum",
        "risk",
        "benchmark",
        "holding",
        "tax",
        "manager",
        "amc",
        "hdfc",
        "portfolio",
        "invest",
        "yield",
        "dividend",
        "cap",
        "gold",
        "silver",
        "etf",
        "plan",
        "growth",
        "direct",
        "scheme",
    ]
    for word in scope_keywords:
        if word in q_lower:
            return True
    return False


def classify_query(query: str) -> QueryType:
    """Returns enum: FACTUAL, ADVISORY, PII_BLOCKED, OUT_OF_SCOPE"""
    if _check_pii(query):
        return QueryType.PII_BLOCKED

    if _check_advisory(query):
        return QueryType.ADVISORY

    if not _check_scope(query):
        return QueryType.OUT_OF_SCOPE

    return QueryType.FACTUAL
