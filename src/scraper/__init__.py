"""Web scraper for Groww mutual fund scheme pages."""

from src.scraper.groww_scraper import (
    run_scraper,
    scrape_all_schemes,
    scrape_url,
    parse_scheme_page,
    save_raw_data,
    save_metadata,
)

__all__ = [
    "run_scraper",
    "scrape_all_schemes",
    "scrape_url",
    "parse_scheme_page",
    "save_raw_data",
    "save_metadata",
]
