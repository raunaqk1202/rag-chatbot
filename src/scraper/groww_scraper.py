"""
Groww scheme page scraper — fetches and parses mutual fund data.

Uses Groww's internal API to get comprehensive JSON data for each scheme,
then formats it into clean text files suitable for chunking and embedding.

Scrapes 5 HDFC mutual fund scheme pages from Groww.in,
extracts structured sections (fund overview, returns, details,
risk, benchmark, holdings, tax), and saves cleaned text files
to data/raw/ with an audit trail in data/metadata.json.
"""

import html
import json
import logging
import os
import re
import sys
import time
from datetime import datetime, timezone
from typing import Any, Optional

import requests

# ── Add project root to path for imports ──────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from src.utils.config import (
    CORPUS_URLS,
    DATA_RAW_DIR,
    METADATA_FILE,
    SCRAPER_DELAY,
    SCRAPER_MAX_RETRIES,
    SCRAPER_TIMEOUT,
    SCRAPER_USER_AGENT,
    URL_TO_SCHEME,
)

# ── Logging ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("groww_scraper")

# ── Constants ─────────────────────────────────────────────────
HEADERS = {
    "User-Agent": SCRAPER_USER_AGENT,
    "Accept": "application/json",
    "Accept-Language": "en-US,en;q=0.9",
    "Accept-Encoding": "gzip, deflate",
    "Connection": "keep-alive",
}

# Groww internal API endpoint for mutual fund scheme data
GROWW_API_BASE = "https://groww.in/v1/api/data/mf/web/v4/scheme/search"

MAINTENANCE_KEYWORDS = [
    "maintenance",
    "coming soon",
    "under construction",
    "temporarily unavailable",
]


def _url_to_search_id(url: str) -> str:
    """
    Extract the search_id slug from a Groww URL.

    Example:
        'https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth'
        → 'hdfc-large-cap-fund-direct-growth'
    """
    return url.rstrip("/").split("/")[-1]


# ═════════════════════════════════════════════════════════════
# 1. HTTP Fetching — Groww API
# ═════════════════════════════════════════════════════════════


def scrape_url(url: str) -> Optional[dict]:
    """
    Fetch scheme data from Groww's internal API endpoint.

    Uses the API at /v1/api/data/mf/web/v4/scheme/search/{search_id}
    which returns comprehensive JSON with all fund details.

    Implements:
    - Exponential backoff on 5xx errors (E44)
    - Retry-After header respect on 429 (E48)
    - Progressive timeout increase (E45)
    - SSL verification (E47)

    Returns:
        dict with 'data' (parsed JSON), 'url', 'status_code', 'fetched_at'
        on success, None on failure after all retries
    """
    search_id = _url_to_search_id(url)
    api_url = f"{GROWW_API_BASE}/{search_id}"

    for attempt in range(SCRAPER_MAX_RETRIES):
        timeout = SCRAPER_TIMEOUT + (5 * attempt)  # 10s → 15s → 20s
        try:
            logger.info(
                "Fetching API: %s (attempt %d/%d, timeout=%ds)",
                api_url,
                attempt + 1,
                SCRAPER_MAX_RETRIES,
                timeout,
            )
            response = requests.get(api_url, headers=HEADERS, timeout=timeout)
            response.raise_for_status()

            # Parse JSON response
            data = response.json()

            if not data:
                logger.warning("Empty JSON response for %s", url)
                return None

            return {
                "data": data,
                "url": url,
                "api_url": api_url,
                "status_code": response.status_code,
                "fetched_at": datetime.now(timezone.utc).isoformat(),
            }

        except requests.exceptions.HTTPError as e:
            status = e.response.status_code if e.response is not None else 0
            if status == 429:
                # Rate limited (E48)
                retry_after = int(e.response.headers.get("Retry-After", 5))
                logger.warning("Rate limited (429). Waiting %ds...", retry_after)
                time.sleep(retry_after)
            elif status == 403:
                # Forbidden (E43)
                logger.warning(
                    "Forbidden (403) for %s. Retrying with different headers...", url
                )
                HEADERS["User-Agent"] = (
                    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                    "AppleWebKit/537.36 (KHTML, like Gecko) "
                    "Chrome/121.0.0.0 Safari/537.36"
                )
                time.sleep(2**attempt)
            elif status >= 500:
                # Server error (E44)
                wait = 2**attempt
                logger.warning(
                    "Server error (%d) for %s. Retrying in %ds...", status, url, wait
                )
                time.sleep(wait)
            else:
                logger.error("Client error (%d) for %s: %s", status, url, str(e))
                return None

        except requests.exceptions.ConnectionError as e:
            wait = 2**attempt
            logger.warning(
                "Connection error for %s: %s. Retrying in %ds...", url, str(e), wait
            )
            time.sleep(wait)

        except requests.exceptions.Timeout:
            logger.warning("Timeout (%ds) for %s.", timeout, url)
            time.sleep(1)

        except requests.exceptions.SSLError as e:
            logger.error("SSL error for %s: %s", url, str(e))
            return None

        except (json.JSONDecodeError, ValueError) as e:
            logger.error("JSON decode error for %s: %s", url, str(e))
            return None

        except requests.exceptions.RequestException as e:
            logger.error("Unexpected request error for %s: %s", url, str(e))
            return None

    logger.error("All %d retries exhausted for %s", SCRAPER_MAX_RETRIES, url)
    return None


# ═════════════════════════════════════════════════════════════
# 2. API Response Parsing — Structured Section Extraction
# ═════════════════════════════════════════════════════════════


def _safe_get(data: dict, *keys: str, default: Any = None) -> Any:
    """Safely navigate nested dict keys."""
    current = data
    for key in keys:
        if isinstance(current, dict):
            current = current.get(key, default)
        else:
            return default
    return current


def _extract_fund_overview(data: dict, url: str) -> dict:
    """Extract fund overview: name, category, AMC, plan type, risk level."""
    overview = {
        "fund_name": data.get("scheme_name", URL_TO_SCHEME.get(url, "Unknown Fund")),
        "category": data.get("category", ""),
        "sub_category": data.get("sub_category", ""),
        "amc": data.get("fund_house", "HDFC Mutual Fund"),
        "plan_type": f"{data.get('plan_type', 'Direct')} {data.get('scheme_type', 'Growth')}",
        "description": data.get("description", ""),
        "launch_date": data.get("launch_date", ""),
        "registrar_agent": data.get("registrar_agent", ""),
        "isin": data.get("isin", ""),
    }

    # Risk from return_stats
    return_stats = data.get("return_stats", [])
    if return_stats:
        risk = return_stats[0].get("risk", "")
        if risk:
            overview["risk_level"] = risk

    # Groww rating
    rating = data.get("groww_rating")
    if rating:
        overview["groww_rating"] = f"{rating} out of 5"

    return {k: v for k, v in overview.items() if v}


def _extract_fund_details(data: dict) -> dict:
    """
    Extract detailed fund metrics: NAV, expense ratio, min SIP,
    exit load, AUM, lock-in period, stamp duty.
    """
    details = {}

    # NAV
    nav = data.get("nav")
    if nav:
        details["nav"] = f"₹{nav}"
    nav_date = data.get("nav_date", "")
    if nav_date:
        details["nav_date"] = nav_date

    # AUM
    aum = data.get("aum")
    if aum:
        details["aum"] = f"₹{aum:,.2f} Cr"

    # Expense Ratio
    expense_ratio = data.get("expense_ratio")
    if expense_ratio:
        details["expense_ratio"] = f"{expense_ratio}%"

    # Exit Load
    exit_load = data.get("exit_load", "")
    if exit_load:
        details["exit_load"] = exit_load

    # Min SIP
    min_sip = data.get("min_sip_investment")
    if min_sip is not None:
        details["min_sip_investment"] = f"₹{min_sip:,.0f}"

    # Min Investment (Lumpsum)
    min_invest = data.get("min_investment_amount")
    if min_invest is not None:
        details["min_lumpsum_investment"] = f"₹{min_invest:,.0f}"

    # Min Additional Investment
    min_add = data.get("mini_additional_investment")
    if min_add is not None:
        details["min_additional_investment"] = f"₹{min_add:,.0f}"

    # Lock-in Period
    lock_in = data.get("lock_in", {})
    if lock_in and isinstance(lock_in, dict):
        years = lock_in.get("years")
        months = lock_in.get("months")
        days = lock_in.get("days")
        if years or months or days:
            parts = []
            if years:
                parts.append(f"{years} years")
            if months:
                parts.append(f"{months} months")
            if days:
                parts.append(f"{days} days")
            details["lock_in_period"] = ", ".join(parts)
        else:
            details["lock_in_period"] = "No lock-in period"
    else:
        details["lock_in_period"] = "No lock-in period"

    # Stamp Duty
    stamp_duty = data.get("stamp_duty", "")
    if stamp_duty:
        details["stamp_duty"] = stamp_duty

    # Portfolio Turnover
    turnover = data.get("portfolio_turnover")
    if turnover is not None:
        details["portfolio_turnover"] = f"{turnover}%"

    return details


def _extract_returns(data: dict) -> dict:
    """Extract return performance data from return_stats and sip_return."""
    returns = {}

    # Annualised (CAGR) returns
    return_stats = data.get("return_stats", [])
    if return_stats:
        rs = return_stats[0]
        return_periods = {
            "1_day": rs.get("return1d"),
            "1_week": rs.get("return1w"),
            "1_month": rs.get("return1m"),
            "3_months": rs.get("return3m"),
            "6_months": rs.get("return6m"),
            "1_year": rs.get("return1y"),
            "3_years": rs.get("return3y"),
            "5_years": rs.get("return5y"),
            "10_years": rs.get("return10y"),
            "since_inception": rs.get("return_default"),
        }
        cagr = {}
        for period, value in return_periods.items():
            if value is not None:
                cagr[period] = f"{value}%"
        if cagr:
            returns["annualised_returns_cagr"] = cagr

        # Category averages
        cat_returns = {}
        for period, key in [
            ("1_year", "cat_return1y"),
            ("3_years", "cat_return3y"),
            ("5_years", "cat_return5y"),
            ("10_years", "cat_return10y"),
        ]:
            val = rs.get(key)
            if val is not None:
                cat_returns[period] = f"{val:.2f}%"
        if cat_returns:
            returns["category_average_returns"] = cat_returns

        # Rankings
        rankings = {}
        for period, key in [
            ("1_year", "rank1yr"),
            ("3_years", "rank3yr"),
            ("5_years", "rank5yr"),
            ("10_years", "rank10yr"),
        ]:
            val = rs.get(key)
            if val is not None:
                rankings[period] = f"Rank {val}"
        if rankings:
            returns["category_rankings"] = rankings

        # Risk metrics
        risk_metrics = {}
        for metric, key in [
            ("sharpe_ratio", "sharpe_ratio"),
            ("beta", "beta"),
            ("alpha", "alpha"),
            ("standard_deviation", "standard_deviation"),
            ("sortino_ratio", "sortino_ratio"),
        ]:
            val = rs.get(key)
            if val is not None:
                risk_metrics[metric] = str(val)
        if risk_metrics:
            returns["risk_metrics"] = risk_metrics

    # SIP returns
    sip_return = data.get("sip_return", {})
    if sip_return:
        sip_data = {}
        for period, key in [
            ("1_year", "return1y"),
            ("3_years", "return3y"),
            ("5_years", "return5y"),
            ("10_years", "return10y"),
            ("since_inception", "return_since_created"),
        ]:
            val = sip_return.get(key)
            if val is not None:
                sip_data[period] = f"{val}%"
        if sip_data:
            returns["sip_returns"] = sip_data

    return returns


def _extract_risk(data: dict) -> dict:
    """Extract riskometer and risk-related information."""
    risk = {}

    return_stats = data.get("return_stats", [])
    if return_stats:
        risk_level = return_stats[0].get("risk", "")
        if risk_level:
            risk["riskometer_category"] = risk_level

    # NFO risk
    nfo_risk = data.get("nfo_risk", "")
    if nfo_risk:
        risk["nfo_riskometer"] = nfo_risk

    # Risk metrics
    if return_stats:
        rs = return_stats[0]
        std_dev = rs.get("standard_deviation")
        beta = rs.get("beta")
        if std_dev is not None:
            risk["standard_deviation"] = str(std_dev)
        if beta is not None:
            risk["beta"] = str(beta)

    return risk


def _extract_benchmark(data: dict) -> dict:
    """Extract benchmark index information."""
    benchmark = {}

    bench = data.get("benchmark", "")
    if bench:
        benchmark["benchmark_index"] = bench

    bench_name = data.get("benchmark_name", "")
    if bench_name:
        benchmark["benchmark_full_name"] = bench_name

    return benchmark


def _extract_holdings(data: dict) -> dict:
    """Extract top holdings and sector allocation."""
    holdings_data = {}

    holdings = data.get("holdings", [])
    if holdings:
        # Top 10 equity holdings
        equity_holdings = [h for h in holdings if h.get("nature_name") == "EQUITY"]
        top_10 = []
        for h in equity_holdings[:10]:
            name = h.get("company_name", "")
            pct = h.get("corpus_per", 0)
            sector = h.get("sector_name", "")
            if name:
                top_10.append(f"{name}: {pct}% ({sector})")
        if top_10:
            holdings_data["top_10_holdings"] = top_10

        # Asset allocation summary
        equity_pct = sum(
            h.get("corpus_per", 0) for h in holdings if h.get("nature_name") == "EQUITY"
        )
        debt_pct = sum(
            h.get("corpus_per", 0) for h in holdings if h.get("nature_name") == "DEBT"
        )
        cash_pct = sum(
            h.get("corpus_per", 0) for h in holdings if h.get("nature_name") == "CASH"
        )

        asset_alloc = {}
        if equity_pct > 0:
            asset_alloc["equity"] = f"{equity_pct:.2f}%"
        if debt_pct > 0:
            asset_alloc["debt"] = f"{debt_pct:.2f}%"
        if cash_pct > 0:
            asset_alloc["cash"] = f"{cash_pct:.2f}%"
        if asset_alloc:
            holdings_data["asset_allocation"] = asset_alloc

        # Sector breakdown
        sectors = {}
        for h in equity_holdings:
            sector = h.get("sector_name", "Unknown")
            pct = h.get("corpus_per", 0)
            sectors[sector] = sectors.get(sector, 0) + pct
        if sectors:
            sorted_sectors = dict(
                sorted(sectors.items(), key=lambda x: x[1], reverse=True)
            )
            holdings_data["sector_allocation"] = {
                k: f"{v:.2f}%" for k, v in sorted_sectors.items()
            }

        # Portfolio date
        if holdings and holdings[0].get("portfolio_date"):
            holdings_data["portfolio_date"] = holdings[0]["portfolio_date"][:10]

        # Total holdings count
        holdings_data["total_holdings"] = str(len(equity_holdings))

    return holdings_data


def _extract_tax(data: dict) -> dict:
    """Extract tax implication details from category_info."""
    tax = {}

    cat_info = data.get("category_info", {})
    if cat_info:
        tax_impact = cat_info.get("tax_impact", "")
        if tax_impact:
            tax["tax_implications"] = tax_impact

        cat_desc = cat_info.get("description", "")
        if cat_desc:
            tax["category_description"] = cat_desc

    return tax


def _extract_fund_managers(data: dict) -> dict:
    """Extract fund manager details."""
    managers = {}

    fm_details = data.get("fund_manager_details", [])
    if fm_details:
        manager_list = []
        for fm in fm_details:
            name = fm.get("person_name", "")
            education = fm.get("education", "")
            experience = fm.get("experience", "")
            since = fm.get("date_from", "")[:10] if fm.get("date_from") else ""

            entry = name
            if since:
                entry += f" (since {since})"
            if education:
                entry += f". {education}"
            if experience:
                entry += f". {experience}"
            manager_list.append(entry)

        if manager_list:
            managers["fund_managers"] = manager_list

    # Also extract fund manager from top-level field
    fm_name = data.get("fund_manager", "")
    if fm_name and not fm_details:
        managers["fund_managers"] = [fm_name]

    return managers


def _extract_amc_info(data: dict) -> dict:
    """Extract AMC (Asset Management Company) details."""
    amc_info = {}

    amc = data.get("amc_info", {})
    if amc:
        if amc.get("name"):
            amc_info["amc_name"] = amc["name"]
        if amc.get("aum"):
            amc_info["total_amc_aum"] = f"₹{amc['aum']:,.2f} Cr"
        if amc.get("email"):
            amc_info["contact_email"] = amc["email"]
        if amc.get("phone"):
            amc_info["contact_phone"] = amc["phone"]
        if amc.get("vro_website"):
            amc_info["website"] = amc["vro_website"]

    return amc_info


def _extract_analysis(data: dict) -> dict:
    """Extract Groww's analysis (pros and cons)."""
    analysis = {}

    analysis_items = data.get("analysis", [])
    if analysis_items:
        pros = []
        cons = []
        for item in analysis_items:
            desc = item.get("analysis_desc", "")
            if item.get("analysis_type") == "PROS":
                pros.append(desc)
            elif item.get("analysis_type") == "CONS":
                cons.append(desc)

        if pros:
            analysis["pros"] = pros
        if cons:
            analysis["cons"] = cons

    return analysis


def parse_scheme_page(api_data: dict, url: str) -> dict:
    """
    Parse Groww API JSON response and extract all structured sections.

    Args:
        api_data: Parsed JSON dict from the Groww API
        url: Source URL (the Groww page URL, not the API URL)

    Returns:
        dict with structured sections and metadata
    """
    scheme_name = URL_TO_SCHEME.get(url, api_data.get("scheme_name", "Unknown Fund"))

    sections = {}
    section_count = 0

    extractors = [
        ("fund_overview", lambda: _extract_fund_overview(api_data, url)),
        ("fund_details", lambda: _extract_fund_details(api_data)),
        ("returns", lambda: _extract_returns(api_data)),
        ("risk", lambda: _extract_risk(api_data)),
        ("benchmark", lambda: _extract_benchmark(api_data)),
        ("holdings", lambda: _extract_holdings(api_data)),
        ("tax", lambda: _extract_tax(api_data)),
        ("fund_management", lambda: _extract_fund_managers(api_data)),
        ("amc_info", lambda: _extract_amc_info(api_data)),
        ("analysis", lambda: _extract_analysis(api_data)),
    ]

    for section_name, extractor in extractors:
        try:
            result = extractor()
            if result:
                sections[section_name] = result
                section_count += 1
        except Exception as e:
            logger.warning("Error extracting %s for %s: %s", section_name, url, str(e))

    return {
        "scheme_name": scheme_name,
        "source_url": url,
        "sections": sections,
        "sections_extracted": section_count,
        "js_rendered_flag": False,  # API data — no JS rendering issue
        "parse_timestamp": datetime.now(timezone.utc).isoformat(),
    }


# ═════════════════════════════════════════════════════════════
# 3. Text Formatting for RAG
# ═════════════════════════════════════════════════════════════


def _format_section_text(section_name: str, data: dict, indent: str = "") -> str:
    """
    Convert a section dict to clean, readable text suitable for chunking
    and embedding in the RAG pipeline.
    """
    lines = [f"\n{'='*60}", f"  {section_name.upper().replace('_', ' ')}", f"{'='*60}"]

    for key, value in data.items():
        readable_key = key.replace("_", " ").title()

        if isinstance(value, dict):
            lines.append(f"\n{indent}{readable_key}:")
            for sub_key, sub_val in value.items():
                sub_readable = sub_key.replace("_", " ").title()
                if isinstance(sub_val, dict):
                    lines.append(f"{indent}  {sub_readable}:")
                    for k, v in sub_val.items():
                        lines.append(f"{indent}    {k.replace('_', ' ').title()}: {v}")
                else:
                    lines.append(f"{indent}  {sub_readable}: {sub_val}")
        elif isinstance(value, list):
            lines.append(f"\n{indent}{readable_key}:")
            for item in value:
                lines.append(f"{indent}  - {item}")
        else:
            lines.append(f"{indent}{readable_key}: {value}")

    return "\n".join(lines)


def format_parsed_data_as_text(parsed_data: dict) -> str:
    """
    Convert all parsed sections into a single clean text document
    suitable for storage as a .txt file and later chunking.

    The text is structured with clear section headers to support
    section-aware chunking in Phase 3.
    """
    lines = [
        f"SCHEME: {parsed_data['scheme_name']}",
        f"SOURCE: {parsed_data['source_url']}",
        f"SCRAPED: {parsed_data['parse_timestamp']}",
        "",
    ]

    for section_name, section_data in parsed_data.get("sections", {}).items():
        section_text = _format_section_text(section_name, section_data)
        lines.append(section_text)
        lines.append("")  # Blank line between sections

    full_text = "\n".join(lines)

    # Final cleanup — normalize whitespace (E56) and decode entities (E57)
    full_text = re.sub(r"\n{3,}", "\n\n", full_text)
    full_text = html.unescape(full_text)

    return full_text.strip()


# ═════════════════════════════════════════════════════════════
# 4. Data Persistence
# ═════════════════════════════════════════════════════════════


def _url_to_filename(url: str) -> str:
    """
    Convert a Groww URL to a safe filename.

    Example:
        'https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth'
        → 'hdfc_large_cap_fund_direct_growth.txt'
    """
    slug = url.rstrip("/").split("/")[-1]
    filename = slug.replace("-", "_")
    return f"{filename}.txt"


def save_raw_data(data: list[dict], path: str) -> list[dict]:
    """
    Save raw parsed text to individual .txt files in the specified directory.

    Args:
        data: List of parsed scheme dicts from parse_scheme_page()
        path: Directory to save files to (e.g., 'data/raw/')

    Returns:
        List of file info dicts with filename, path, and size
    """
    os.makedirs(path, exist_ok=True)
    saved_files = []

    for item in data:
        filename = _url_to_filename(item["source_url"])
        filepath = os.path.join(path, filename)

        text_content = format_parsed_data_as_text(item)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(text_content)

        file_size = os.path.getsize(filepath)
        saved_files.append(
            {
                "filename": filename,
                "filepath": filepath,
                "size_bytes": file_size,
                "scheme_name": item["scheme_name"],
            }
        )

        logger.info("Saved %s (%d bytes)", filepath, file_size)

    return saved_files


def save_raw_json(
    api_responses: list[dict],
    parsed_data: list[dict],
    raw_json_dir: str,
    parsed_json_dir: str,
) -> None:
    """
    Save raw API JSON responses and parsed structured data as JSON files
    so the data can be reviewed independently of the text output.

    Creates two subdirectories:
    - raw_json_dir:    Full API responses (data/raw/json/)
    - parsed_json_dir: Parsed section dicts (data/raw/parsed/)

    Args:
        api_responses: List of dicts containing raw API JSON under 'data' key
        parsed_data: List of parsed scheme dicts from parse_scheme_page()
        raw_json_dir: Directory for raw API JSON files
        parsed_json_dir: Directory for parsed/structured JSON files
    """
    os.makedirs(raw_json_dir, exist_ok=True)
    os.makedirs(parsed_json_dir, exist_ok=True)

    # Save raw API responses
    for resp in api_responses:
        url = resp.get("url", "")
        slug = url.rstrip("/").split("/")[-1]
        filename = slug.replace("-", "_") + "_api_response.json"
        filepath = os.path.join(raw_json_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(resp["data"], f, indent=2, ensure_ascii=False)

        logger.info(
            "Saved raw API JSON: %s (%d bytes)", filepath, os.path.getsize(filepath)
        )

    # Save parsed/structured data
    for item in parsed_data:
        slug = item["source_url"].rstrip("/").split("/")[-1]
        filename = slug.replace("-", "_") + "_parsed.json"
        filepath = os.path.join(parsed_json_dir, filename)

        with open(filepath, "w", encoding="utf-8") as f:
            json.dump(item, f, indent=2, ensure_ascii=False, default=str)

        logger.info(
            "Saved parsed JSON: %s (%d bytes)", filepath, os.path.getsize(filepath)
        )


def _generate_metadata(
    scraped_data: list[dict],
    saved_files: list[dict],
    failed_urls: list[str],
) -> list[dict]:
    """Generate metadata.json entries with scrape audit trail."""
    metadata = []

    file_map = {f["scheme_name"]: f for f in saved_files}

    for item in scraped_data:
        scheme = item["scheme_name"]
        file_info = file_map.get(scheme, {})

        entry = {
            "scheme_name": scheme,
            "source_url": item["source_url"],
            "last_scraped": item["parse_timestamp"],
            "status": "success",
            "sections_extracted": item["sections_extracted"],
            "js_rendered_flag": item.get("js_rendered_flag", False),
            "raw_file": file_info.get("filepath", ""),
            "raw_file_size_bytes": file_info.get("size_bytes", 0),
        }
        metadata.append(entry)

    for url in failed_urls:
        scheme = URL_TO_SCHEME.get(url, "Unknown")
        entry = {
            "scheme_name": scheme,
            "source_url": url,
            "last_scraped": datetime.now(timezone.utc).isoformat(),
            "status": "failed",
            "sections_extracted": 0,
            "js_rendered_flag": False,
            "raw_file": "",
            "raw_file_size_bytes": 0,
        }
        metadata.append(entry)

    return metadata


def save_metadata(metadata: list[dict], path: str) -> None:
    """
    Save metadata.json with scrape results.
    Merges with existing metadata if present.
    """
    existing = []
    if os.path.exists(path):
        try:
            with open(path, "r", encoding="utf-8") as f:
                existing = json.load(f)
                if not isinstance(existing, list):
                    existing = []
        except (json.JSONDecodeError, ValueError):
            existing = []

    existing_map = {e["source_url"]: e for e in existing}
    for entry in metadata:
        existing_map[entry["source_url"]] = entry

    merged = list(existing_map.values())

    with open(path, "w", encoding="utf-8") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)

    logger.info("Metadata saved to %s (%d entries)", path, len(merged))


# ═════════════════════════════════════════════════════════════
# 5. Orchestration
# ═════════════════════════════════════════════════════════════


def scrape_all_schemes() -> list[dict]:
    """
    Iterate over all 5 corpus URLs, scrape and parse each via the
    Groww API. Implements rate limiting with 1-second delay between
    requests.

    Returns:
        List of parsed scheme dicts for all successful scrapes
    """
    all_parsed = []
    api_responses = []
    failed_urls = []

    total = len(CORPUS_URLS)
    for i, url in enumerate(CORPUS_URLS, start=1):
        scheme_name = URL_TO_SCHEME.get(url, "Unknown")
        logger.info("─" * 60)
        logger.info("Scraping [%d/%d]: %s", i, total, scheme_name)
        logger.info("URL: %s", url)

        result = scrape_url(url)

        if result is None:
            logger.error("FAILED: Could not fetch %s", url)
            failed_urls.append(url)
            continue

        # Keep raw API response for JSON export
        api_responses.append(result)

        parsed = parse_scheme_page(result["data"], url)
        parsed["fetched_at"] = result["fetched_at"]
        parsed["http_status"] = result["status_code"]

        logger.info(
            "SUCCESS: Extracted %d sections from %s",
            parsed["sections_extracted"],
            scheme_name,
        )

        # Log key extracted data points
        details = parsed.get("sections", {}).get("fund_details", {})
        if details:
            logger.info(
                "  NAV: %s | Expense Ratio: %s | Exit Load: %s | Min SIP: %s",
                details.get("nav", "N/A"),
                details.get("expense_ratio", "N/A"),
                details.get("exit_load", "N/A"),
                details.get("min_sip_investment", "N/A"),
            )

        all_parsed.append(parsed)

        # Rate limiting delay — skip after last URL
        if i < total:
            logger.info(
                "Rate limiting: waiting %.1fs before next request...", SCRAPER_DELAY
            )
            time.sleep(SCRAPER_DELAY)

    logger.info("═" * 60)
    logger.info(
        "SCRAPING COMPLETE: %d/%d succeeded, %d failed",
        len(all_parsed),
        total,
        len(failed_urls),
    )
    if failed_urls:
        logger.warning("Failed URLs: %s", failed_urls)

    return all_parsed, api_responses


def run_scraper() -> None:
    """
    Full scraping pipeline entry point:
    1. Scrape all 5 Groww scheme pages via API
    2. Save cleaned text to data/raw/
    3. Update data/metadata.json with audit trail
    """
    logger.info("═" * 60)
    logger.info("MUTUAL FUND FAQ ASSISTANT — Web Scraper")
    logger.info("═" * 60)
    logger.info("Target URLs: %d", len(CORPUS_URLS))
    logger.info("Data source: Groww API (v4)")
    logger.info("Output directory: %s", DATA_RAW_DIR)
    logger.info("Metadata file: %s", METADATA_FILE)
    logger.info("")

    # Step 1: Scrape all schemes
    scraped_data, api_responses = scrape_all_schemes()

    if not scraped_data:
        logger.error("No data scraped. Exiting.")
        return

    # Step 2: Save raw text files
    logger.info("─" * 60)
    logger.info("Saving raw text files to %s...", DATA_RAW_DIR)
    saved_files = save_raw_data(scraped_data, DATA_RAW_DIR)

    # Step 3: Save JSON files (raw API + parsed) for review
    raw_json_dir = os.path.join(DATA_RAW_DIR, "json")
    parsed_json_dir = os.path.join(DATA_RAW_DIR, "parsed")
    logger.info("─" * 60)
    logger.info("Saving JSON files for review...")
    save_raw_json(api_responses, scraped_data, raw_json_dir, parsed_json_dir)

    # Step 4: Generate and save metadata
    failed_urls = [
        url for url in CORPUS_URLS if url not in {d["source_url"] for d in scraped_data}
    ]
    metadata = _generate_metadata(scraped_data, saved_files, failed_urls)
    save_metadata(metadata, METADATA_FILE)

    # Final summary
    logger.info("═" * 60)
    logger.info("SCRAPER SUMMARY")
    logger.info("═" * 60)
    for f in saved_files:
        logger.info(
            "  ✅ %s — %s (%d bytes)", f["scheme_name"], f["filename"], f["size_bytes"]
        )
    if failed_urls:
        for url in failed_urls:
            logger.warning("  ❌ FAILED: %s", url)
    logger.info("")
    logger.info("Raw text files:  %s", DATA_RAW_DIR)
    logger.info("Raw API JSON:    %s", raw_json_dir)
    logger.info("Parsed JSON:     %s", parsed_json_dir)
    logger.info("Metadata:        %s", METADATA_FILE)
    logger.info("Done.")


# ═════════════════════════════════════════════════════════════
# Entry Point
# ═════════════════════════════════════════════════════════════

if __name__ == "__main__":
    run_scraper()
