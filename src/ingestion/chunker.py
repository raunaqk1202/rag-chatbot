"""
Chunker — section-based chunking from parsed JSON files.

Reads structured JSON from data/raw/parsed/, flattens each section
into natural-language text, and saves chunks with metadata to
data/processed/. Each section becomes one chunk — no text splitter
needed since sections are small, self-contained units (50–200 words).

Usage:
    python -m src.ingestion.chunker
"""

import glob
import json
import logging
import os
import re
import sys
from typing import Any, Optional

# ── Add project root to path for imports ──────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.utils.config import DATA_PROCESSED_DIR

# ── Logging ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("chunker")

# ── Constants ─────────────────────────────────────────────────
PARSED_JSON_DIR = os.path.join("data", "raw", "parsed")

# Sections to merge into a single "risk_and_benchmark" chunk
MERGE_SECTIONS = {"risk", "benchmark"}

# Section processing order (determines chunk_index)
SECTION_ORDER = [
    "fund_overview",
    "fund_details",
    "returns",
    "risk_and_benchmark",  # merged from risk + benchmark
    "holdings",
    "tax",
    "fund_management",
    "amc_info",
    "analysis",
]

# Human-readable section titles for chunk text
SECTION_TITLES = {
    "fund_overview": "Fund Overview",
    "fund_details": "Fund Details",
    "returns": "Returns & Performance",
    "risk_and_benchmark": "Risk & Benchmark",
    "holdings": "Portfolio Holdings",
    "tax": "Tax Information",
    "fund_management": "Fund Management",
    "amc_info": "AMC Information",
    "analysis": "Analysis – Pros & Cons",
}


# ═════════════════════════════════════════════════════════════
# 1. Loading Parsed JSON
# ═════════════════════════════════════════════════════════════


def load_parsed_json(parsed_dir: str = PARSED_JSON_DIR) -> list[dict]:
    """
    Read all parsed JSON files from the parsed directory.

    Args:
        parsed_dir: Path to directory containing *_parsed.json files

    Returns:
        List of parsed fund dicts, each with scheme_name, source_url, sections
    """
    pattern = os.path.join(parsed_dir, "*_parsed.json")
    files = sorted(glob.glob(pattern))

    if not files:
        logger.error("No parsed JSON files found in %s", parsed_dir)
        return []

    parsed_data = []
    for filepath in files:
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                data = json.load(f)
            parsed_data.append(data)
            logger.info(
                "Loaded: %s (%s)",
                os.path.basename(filepath),
                data.get("scheme_name", "Unknown"),
            )
        except (json.JSONDecodeError, OSError) as e:
            logger.error("Failed to load %s: %s", filepath, str(e))

    logger.info("Loaded %d parsed JSON files from %s", len(parsed_data), parsed_dir)
    return parsed_data


# ═════════════════════════════════════════════════════════════
# 2. Section Flattening — JSON to Natural Language
# ═════════════════════════════════════════════════════════════


def _humanise_key(key: str) -> str:
    """Convert snake_case key to Title Case label."""
    return key.replace("_", " ").title()


def _flatten_key_value(data: dict, scheme_name: str, section_title: str) -> str:
    """
    Generic flattening for simple key-value sections.
    Produces: 'Key: value. Key: value.'
    """
    header = f"{scheme_name}: {section_title}."
    parts = [header]

    for key, value in data.items():
        label = _humanise_key(key)
        if isinstance(value, dict):
            # Nested dict — flatten to sub-items
            sub_parts = [f"{_humanise_key(k)}: {v}" for k, v in value.items()]
            parts.append(f"{label}: {'; '.join(sub_parts)}.")
        elif isinstance(value, list):
            # List — join items
            items_str = "; ".join(str(item) for item in value)
            parts.append(f"{label}: {items_str}.")
        else:
            parts.append(f"{label}: {value}.")

    return " ".join(parts)


def _flatten_fund_overview(data: dict, scheme_name: str) -> str:
    """Flatten fund overview into a descriptive paragraph."""
    header = f"{scheme_name}: Fund Overview."
    parts = [header]

    field_map = [
        ("fund_name", "Fund Name"),
        ("category", "Category"),
        ("sub_category", "Sub-Category"),
        ("amc", "AMC"),
        ("plan_type", "Plan Type"),
        ("description", "Description"),
        ("launch_date", "Launch Date"),
        ("registrar_agent", "Registrar Agent"),
        ("isin", "ISIN"),
        ("risk_level", "Risk Level"),
        ("groww_rating", "Groww Rating"),
    ]

    for key, label in field_map:
        value = data.get(key)
        if value:
            parts.append(f"{label}: {value}.")

    return " ".join(parts)


def _flatten_fund_details(data: dict, scheme_name: str) -> str:
    """Flatten fund details with clear financial labels."""
    header = f"{scheme_name}: Fund Details."
    parts = [header]

    field_map = [
        ("nav", "NAV"),
        ("nav_date", "NAV Date"),
        ("aum", "AUM"),
        ("expense_ratio", "Expense Ratio"),
        ("exit_load", "Exit Load"),
        ("min_sip_investment", "Minimum SIP Investment"),
        ("min_lumpsum_investment", "Minimum Lumpsum Investment"),
        ("min_additional_investment", "Minimum Additional Investment"),
        ("lock_in_period", "Lock-in Period"),
        ("stamp_duty", "Stamp Duty"),
        ("portfolio_turnover", "Portfolio Turnover"),
    ]

    for key, label in field_map:
        value = data.get(key)
        if value:
            parts.append(f"{label}: {value}.")

    return " ".join(parts)


def _flatten_returns(data: dict, scheme_name: str) -> str:
    """
    Flatten returns section with nested sub-sections.
    Combines CAGR, category averages, rankings, risk metrics, and SIP returns.
    """
    header = f"{scheme_name}: Returns & Performance."
    parts = [header]

    # Annualised CAGR returns
    cagr = data.get("annualised_returns_cagr", {})
    if cagr:
        period_parts = []
        for period, value in cagr.items():
            label = _humanise_key(period)
            period_parts.append(f"{label}: {value}")
        parts.append(f"Annualised Returns (CAGR): {', '.join(period_parts)}.")

    # Category average returns
    cat_avg = data.get("category_average_returns", {})
    if cat_avg:
        avg_parts = [f"{_humanise_key(k)}: {v}" for k, v in cat_avg.items()]
        parts.append(f"Category Average Returns: {', '.join(avg_parts)}.")

    # Category rankings
    rankings = data.get("category_rankings", {})
    if rankings:
        rank_parts = [f"{_humanise_key(k)}: {v}" for k, v in rankings.items()]
        parts.append(f"Category Rankings: {', '.join(rank_parts)}.")

    # Risk metrics
    risk_metrics = data.get("risk_metrics", {})
    if risk_metrics:
        metric_parts = [f"{_humanise_key(k)}: {v}" for k, v in risk_metrics.items()]
        parts.append(f"Risk Metrics: {', '.join(metric_parts)}.")

    # SIP returns
    sip = data.get("sip_returns", {})
    if sip:
        sip_parts = [f"{_humanise_key(k)}: {v}" for k, v in sip.items()]
        parts.append(f"SIP Returns: {', '.join(sip_parts)}.")

    return " ".join(parts)


def _flatten_risk_and_benchmark(
    risk_data: dict, benchmark_data: dict, scheme_name: str
) -> str:
    """
    Merge risk and benchmark into a single chunk.
    Both are very small (~30 words combined).
    """
    header = f"{scheme_name}: Risk & Benchmark."
    parts = [header]

    # Risk fields
    risk_field_map = [
        ("riskometer_category", "Riskometer Category"),
        ("nfo_riskometer", "NFO Riskometer"),
        ("standard_deviation", "Standard Deviation"),
        ("beta", "Beta"),
    ]
    for key, label in risk_field_map:
        value = risk_data.get(key)
        if value:
            parts.append(f"{label}: {value}.")

    # Benchmark fields
    bench_index = benchmark_data.get("benchmark_index", "")
    bench_full = benchmark_data.get("benchmark_full_name", "")
    if bench_index:
        if bench_full and bench_full != bench_index:
            parts.append(f"Benchmark Index: {bench_index} ({bench_full}).")
        else:
            parts.append(f"Benchmark Index: {bench_index}.")

    return " ".join(parts)


def _flatten_holdings(data: dict, scheme_name: str) -> str:
    """Flatten holdings with top-10 list, sector and asset allocation."""
    header = f"{scheme_name}: Portfolio Holdings."
    parts = [header]

    # Top 10 holdings
    top_10 = data.get("top_10_holdings", [])
    if top_10:
        holdings_str = "; ".join(top_10)
        parts.append(f"Top 10 Holdings: {holdings_str}.")

    # Asset allocation
    asset_alloc = data.get("asset_allocation", {})
    if asset_alloc:
        alloc_parts = [f"{_humanise_key(k)}: {v}" for k, v in asset_alloc.items()]
        parts.append(f"Asset Allocation: {', '.join(alloc_parts)}.")

    # Sector allocation
    sector_alloc = data.get("sector_allocation", {})
    if sector_alloc:
        sector_parts = [f"{k}: {v}" for k, v in sector_alloc.items()]
        parts.append(f"Sector Allocation: {', '.join(sector_parts)}.")

    # Portfolio date and total holdings count
    portfolio_date = data.get("portfolio_date")
    if portfolio_date:
        parts.append(f"Portfolio Date: {portfolio_date}.")

    total = data.get("total_holdings")
    if total:
        parts.append(f"Total Holdings: {total}.")

    return " ".join(parts)


def _flatten_tax(data: dict, scheme_name: str) -> str:
    """Flatten tax information."""
    header = f"{scheme_name}: Tax Information."
    parts = [header]

    tax_impl = data.get("tax_implications")
    if tax_impl:
        parts.append(f"Tax Implications: {tax_impl}")

    cat_desc = data.get("category_description")
    if cat_desc:
        parts.append(f"Category Description: {cat_desc}")

    return " ".join(parts)


def _flatten_fund_management(data: dict, scheme_name: str) -> str:
    """Flatten fund manager bios into sentences."""
    header = f"{scheme_name}: Fund Management."
    parts = [header]

    managers = data.get("fund_managers", [])
    if managers:
        for i, bio in enumerate(managers, 1):
            parts.append(f"Fund Manager {i}: {bio}")

    return " ".join(parts)


def _flatten_amc_info(data: dict, scheme_name: str) -> str:
    """Flatten AMC information."""
    header = f"{scheme_name}: AMC Information."
    parts = [header]

    field_map = [
        ("amc_name", "AMC Name"),
        ("total_amc_aum", "Total AMC AUM"),
        ("contact_email", "Contact Email"),
        ("contact_phone", "Contact Phone"),
        ("website", "Website"),
    ]

    for key, label in field_map:
        value = data.get(key)
        if value:
            parts.append(f"{label}: {value}.")

    return " ".join(parts)


def _flatten_analysis(data: dict, scheme_name: str) -> str:
    """Flatten Groww's analysis (pros and cons)."""
    header = f"{scheme_name}: Analysis – Pros & Cons."
    parts = [header]

    pros = data.get("pros", [])
    if pros:
        pros_str = "; ".join(pros)
        parts.append(f"Pros: {pros_str}.")

    cons = data.get("cons", [])
    if cons:
        cons_str = "; ".join(cons)
        parts.append(f"Cons: {cons_str}.")

    return " ".join(parts)


def flatten_section(
    section_name: str, data: dict, scheme_name: str, extra_data: Optional[dict] = None
) -> str:
    """
    Convert a section's JSON data to natural-language text.

    Args:
        section_name: Section identifier (e.g., 'fund_details', 'risk_and_benchmark')
        data: The section's JSON data dict
        scheme_name: Fund scheme name to prepend
        extra_data: Additional data for merged sections (e.g., benchmark data for risk_and_benchmark)

    Returns:
        Flattened natural-language text string
    """
    flatteners = {
        "fund_overview": _flatten_fund_overview,
        "fund_details": _flatten_fund_details,
        "returns": _flatten_returns,
        "holdings": _flatten_holdings,
        "tax": _flatten_tax,
        "fund_management": _flatten_fund_management,
        "amc_info": _flatten_amc_info,
        "analysis": _flatten_analysis,
    }

    if section_name == "risk_and_benchmark":
        benchmark_data = extra_data or {}
        return _flatten_risk_and_benchmark(data, benchmark_data, scheme_name)

    flattener = flatteners.get(section_name)
    if flattener:
        return flattener(data, scheme_name)

    # Fallback: generic key-value flattening
    title = SECTION_TITLES.get(section_name, _humanise_key(section_name))
    return _flatten_key_value(data, scheme_name, title)


# ═════════════════════════════════════════════════════════════
# 3. Chunk Assembly
# ═════════════════════════════════════════════════════════════


def _scheme_to_slug(scheme_name: str) -> str:
    """
    Convert scheme name to a filesystem/ID-safe slug.

    Example: 'HDFC Large Cap Fund – Direct Growth' → 'hdfc_large_cap_fund'
    """
    # Remove plan type suffix for shorter slugs
    name = scheme_name.lower()
    name = re.sub(r"\s*[–-]\s*direct\s+(growth|plan\s+growth)", "", name)
    name = re.sub(r"\s+", "_", name)
    name = re.sub(r"[^a-z0-9_]", "", name)
    name = re.sub(r"_+", "_", name).strip("_")
    return name


def chunk_fund(parsed_data: dict) -> list[dict]:
    """
    Create all chunks for a single fund from its parsed JSON data.

    Processes sections in a defined order, merges risk+benchmark,
    and attaches full metadata to each chunk.

    Args:
        parsed_data: A single fund's parsed JSON dict

    Returns:
        List of chunk dicts with 'id', 'text', and 'metadata'
    """
    scheme_name = parsed_data.get("scheme_name", "Unknown Fund")
    source_url = parsed_data.get("source_url", "")
    sections = parsed_data.get("sections", {})
    scrape_date = parsed_data.get("parse_timestamp", "")[:10]  # Extract date portion
    slug = _scheme_to_slug(scheme_name)

    chunks = []
    chunk_index = 0

    for section_name in SECTION_ORDER:
        # Handle merged risk + benchmark section
        if section_name == "risk_and_benchmark":
            risk_data = sections.get("risk", {})
            benchmark_data = sections.get("benchmark", {})
            if not risk_data and not benchmark_data:
                continue
            text = flatten_section(
                "risk_and_benchmark",
                risk_data,
                scheme_name,
                extra_data=benchmark_data,
            )
        else:
            # Skip sections that are handled by the merge
            if section_name in MERGE_SECTIONS:
                continue

            section_data = sections.get(section_name)
            if not section_data:
                logger.warning(
                    "Section '%s' not found for %s", section_name, scheme_name
                )
                continue

            text = flatten_section(section_name, section_data, scheme_name)

        # Skip empty text
        if not text or len(text.strip()) == 0:
            continue

        word_count = len(text.split())
        chunk_id = f"{slug}__{section_name}"

        chunk = {
            "id": chunk_id,
            "text": text,
            "metadata": {
                "source_url": source_url,
                "scheme_name": scheme_name,
                "section": section_name,
                "scrape_date": scrape_date,
                "chunk_index": chunk_index,
                "word_count": word_count,
            },
        }

        chunks.append(chunk)
        chunk_index += 1

    return chunks


def chunk_all_funds(parsed_dir: str = PARSED_JSON_DIR) -> list[dict]:
    """
    Process all parsed JSON files and return all chunks.

    Args:
        parsed_dir: Directory containing *_parsed.json files

    Returns:
        List of all chunk dicts across all funds
    """
    parsed_data = load_parsed_json(parsed_dir)

    if not parsed_data:
        logger.error("No parsed data to chunk.")
        return []

    all_chunks = []
    fund_summaries = []

    for fund_data in parsed_data:
        scheme_name = fund_data.get("scheme_name", "Unknown")
        fund_chunks = chunk_fund(fund_data)
        all_chunks.extend(fund_chunks)
        fund_summaries.append((scheme_name, len(fund_chunks)))
        logger.info("  %s: %d chunks", scheme_name, len(fund_chunks))

    logger.info("─" * 60)
    logger.info(
        "Chunked %d funds into %d chunks",
        len(parsed_data),
        len(all_chunks),
    )

    return all_chunks


# ═════════════════════════════════════════════════════════════
# 4. Saving Chunks
# ═════════════════════════════════════════════════════════════


def save_chunks(chunks: list[dict], output_dir: str = DATA_PROCESSED_DIR) -> None:
    """
    Save chunks to data/processed/ as JSON files.

    Creates:
    - all_chunks.json — all chunks across all funds
    - <fund_slug>_chunks.json — per-fund chunk files

    Args:
        chunks: List of chunk dicts
        output_dir: Output directory path
    """
    os.makedirs(output_dir, exist_ok=True)

    # Save all chunks
    all_chunks_path = os.path.join(output_dir, "all_chunks.json")
    with open(all_chunks_path, "w", encoding="utf-8") as f:
        json.dump(chunks, f, indent=2, ensure_ascii=False)
    logger.info(
        "Saved all_chunks.json (%d chunks, %d bytes)",
        len(chunks),
        os.path.getsize(all_chunks_path),
    )

    # Group chunks by scheme and save per-fund files
    funds = {}
    for chunk in chunks:
        scheme = chunk["metadata"]["scheme_name"]
        if scheme not in funds:
            funds[scheme] = []
        funds[scheme].append(chunk)

    for scheme_name, fund_chunks in funds.items():
        slug = _scheme_to_slug(scheme_name)
        filepath = os.path.join(output_dir, f"{slug}_chunks.json")
        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(fund_chunks, f, indent=2, ensure_ascii=False)
        logger.info("Saved %s_chunks.json (%d chunks)", slug, len(fund_chunks))


# ═════════════════════════════════════════════════════════════
# 5. Orchestration
# ═════════════════════════════════════════════════════════════


def run_chunking_pipeline(
    parsed_dir: str = PARSED_JSON_DIR,
    output_dir: str = DATA_PROCESSED_DIR,
) -> list[dict]:
    """
    Full chunking pipeline entry point:
    1. Load parsed JSON files from data/raw/parsed/
    2. Chunk each fund by section
    3. Save chunks to data/processed/

    Args:
        parsed_dir: Input directory with parsed JSON
        output_dir: Output directory for chunks

    Returns:
        List of all chunk dicts
    """
    logger.info("═" * 60)
    logger.info("MUTUAL FUND FAQ ASSISTANT — Chunking Pipeline")
    logger.info("═" * 60)
    logger.info("Input:  %s", parsed_dir)
    logger.info("Output: %s", output_dir)
    logger.info("")

    # Step 1 & 2: Load and chunk
    all_chunks = chunk_all_funds(parsed_dir)

    if not all_chunks:
        logger.error("No chunks generated. Exiting.")
        return []

    # Step 3: Save
    save_chunks(all_chunks, output_dir)

    # Summary
    logger.info("═" * 60)
    logger.info("CHUNKING SUMMARY")
    logger.info("═" * 60)

    # Group by fund for summary
    funds = {}
    for chunk in all_chunks:
        scheme = chunk["metadata"]["scheme_name"]
        funds.setdefault(scheme, []).append(chunk)

    for scheme_name, fund_chunks in funds.items():
        total_words = sum(c["metadata"]["word_count"] for c in fund_chunks)
        logger.info(
            "  ✅ %s: %d chunks (%d words)", scheme_name, len(fund_chunks), total_words
        )

    total_words = sum(c["metadata"]["word_count"] for c in all_chunks)
    avg_words = total_words / len(all_chunks) if all_chunks else 0
    logger.info("")
    logger.info("Total: %d chunks across %d funds", len(all_chunks), len(funds))
    logger.info("Total words: %d | Avg words per chunk: %.0f", total_words, avg_words)
    logger.info("Output: %s", output_dir)
    logger.info("Done.")

    return all_chunks


# ═════════════════════════════════════════════════════════════
# Entry Point
# ═════════════════════════════════════════════════════════════

if __name__ == "__main__":
    run_chunking_pipeline()
