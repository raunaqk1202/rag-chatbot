"""
Mutual Fund FAQ Assistant — Centralised Configuration

Loads environment variables from .env and provides all config constants
used across the application (corpus URLs, model settings, chunking params).
"""

import os
from dotenv import load_dotenv

# Load .env file from project root
load_dotenv()

# ──────────────────────────────────────────────
# Corpus Definition
# ──────────────────────────────────────────────

CORPUS_URLS = [
    "https://groww.in/mutual-funds/hdfc-large-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-mid-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-small-cap-fund-direct-growth",
    "https://groww.in/mutual-funds/hdfc-gold-etf-fund-of-fund-direct-plan-growth",
    "https://groww.in/mutual-funds/hdfc-silver-etf-fof-direct-growth",
]

SCHEME_NAMES = [
    "HDFC Large Cap Fund – Direct Growth",
    "HDFC Mid Cap Fund – Direct Growth",
    "HDFC Small Cap Fund – Direct Growth",
    "HDFC Gold ETF Fund of Fund – Direct Growth",
    "HDFC Silver ETF FoF – Direct Growth",
]

# Map URL slug → scheme name for easy lookup
URL_TO_SCHEME = dict(zip(CORPUS_URLS, SCHEME_NAMES))

# ──────────────────────────────────────────────
# ChromaDB Settings
# ──────────────────────────────────────────────

CHROMA_DB_PATH = os.getenv("CHROMA_DB_PATH", "./chroma_db")
CHROMA_COLLECTION = "hdfc_mutual_funds"

# ──────────────────────────────────────────────
# LLM Settings (Groq)
# ──────────────────────────────────────────────

GROQ_API_KEY = os.getenv("GROQ_API_KEY", "")
LLM_MODEL = os.getenv("LLM_MODEL", "llama-3.3-70b-versatile")
LLM_TEMPERATURE = 0.0
LLM_MAX_TOKENS = 200

# ──────────────────────────────────────────────
# Embedding Model Settings (BGE)
# ──────────────────────────────────────────────

EMBEDDING_MODEL = "BAAI/bge-small-en-v1.5"
EMBEDDING_DIMENSION = 384

# ──────────────────────────────────────────────
# Chunking Settings
# ──────────────────────────────────────────────

CHUNK_SIZE = 400
CHUNK_OVERLAP = 50

# ──────────────────────────────────────────────
# Retrieval Settings
# ──────────────────────────────────────────────

TOP_K = 4
MIN_SIMILARITY_SCORE = 0.3

# ──────────────────────────────────────────────
# Data Paths
# ──────────────────────────────────────────────

DATA_RAW_DIR = "data/raw"
DATA_PROCESSED_DIR = "data/processed"
METADATA_FILE = "data/metadata.json"

# ──────────────────────────────────────────────
# Scraper Settings
# ──────────────────────────────────────────────

SCRAPER_TIMEOUT = 10  # seconds per request
SCRAPER_MAX_RETRIES = 3
SCRAPER_DELAY = 1.0  # seconds between requests
SCRAPER_USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

# ──────────────────────────────────────────────
# Query Classifier Settings
# ──────────────────────────────────────────────

MAX_QUERY_LENGTH = 500
