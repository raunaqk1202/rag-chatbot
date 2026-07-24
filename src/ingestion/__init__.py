"""Ingestion pipeline — chunking, embedding, and ChromaDB storage."""

from src.ingestion.chunker import (
    chunk_all_funds,
    chunk_fund,
    flatten_section,
    load_parsed_json,
    run_chunking_pipeline,
    save_chunks,
)
from src.ingestion.embedder import run_embedding_pipeline

__all__ = [
    "chunk_all_funds",
    "chunk_fund",
    "flatten_section",
    "load_parsed_json",
    "run_chunking_pipeline",
    "save_chunks",
    "run_embedding_pipeline",
]
