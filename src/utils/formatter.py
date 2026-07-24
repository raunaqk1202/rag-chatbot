"""
Formatter — assembles final responses, handles refusals, and validates output.
"""

from typing import Union, List
from src.classifier.query_classifier import QueryType

REFUSAL_TEMPLATES = {
    QueryType.ADVISORY: "I can only provide factual information about mutual fund schemes. I'm unable to offer investment advice or recommendations. For guidance, please visit [AMFI](https://www.amfiindia.com) or [SEBI Investor Education](https://investor.sebi.gov.in).",
    QueryType.PII_BLOCKED: "For your security, please do not share personal information like PAN, Aadhaar, or account numbers. I can help with factual queries about HDFC mutual fund schemes.",
    QueryType.OUT_OF_SCOPE: "I can only answer questions about HDFC mutual fund schemes listed on Groww. Please ask a question related to fund details like expense ratio, exit load, SIP amounts, or risk classification.",
}


def format_response(
    answer: str, source_url: Union[str, List[str]], scrape_date: str = "2026-07-14"
) -> str:
    """Assemble answer + citation + footer."""
    response = answer.strip()

    if isinstance(source_url, list):
        urls = source_url
    else:
        urls = [source_url] if source_url else []

    if urls:
        citation_str = "\n".join([f"📎 Source: {url}" for url in urls])
        response += f"\n\n{citation_str}"

    response += f"\n🕐 Last updated from sources: {scrape_date}"

    return response


def format_refusal(query_type: QueryType) -> str:
    """Return appropriate refusal message based on query type."""
    return REFUSAL_TEMPLATES.get(query_type, "I cannot process this query.")


def validate_response(response: str) -> bool:
    """
    Check:
    - <= 3 sentences (roughly)
    - has URL
    - has footer
    """
    import re

    # Strip the footer before counting sentences
    body = response.split("📎 Source")[0].split("🕐 Last updated")[0].strip()

    sentences = re.split(r"[.!?]+", body)
    # Filter out empty strings
    sentences = [s for s in sentences if s.strip()]

    if len(sentences) > 4:  # Allowing some leeway
        return False

    if "http" not in response:
        return False

    if "Last updated from sources" not in response:
        return False

    return True
