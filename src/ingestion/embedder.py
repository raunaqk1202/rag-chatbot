"""
Embedder — generates BGE embeddings and stores in ChromaDB.

Loads chunks from data/processed/, generates embeddings using the
specified SentenceTransformer model, and upserts them into ChromaDB.
Updates metadata.json with chunk counts per scheme.

Usage:
    python -m src.ingestion.embedder
"""

import json
import logging
import os
import sys
from typing import Any, List, Dict

# ── Add project root to path for imports ──────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import chromadb
from sentence_transformers import SentenceTransformer

from src.utils.config import (
    DATA_PROCESSED_DIR,
    METADATA_FILE,
    CHROMA_DB_PATH,
    CHROMA_COLLECTION,
    EMBEDDING_MODEL,
)

# ── Logging ───────────────────────────────────────────────────
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("embedder")

# ═════════════════════════════════════════════════════════════
# 1. Loading Model and Chunks
# ═════════════════════════════════════════════════════════════


def get_embedding_model() -> SentenceTransformer:
    """Load the SentenceTransformer model."""
    logger.info("Loading embedding model: %s", EMBEDDING_MODEL)
    model = SentenceTransformer(EMBEDDING_MODEL)
    return model


def load_chunks(processed_dir: str = DATA_PROCESSED_DIR) -> List[Dict[str, Any]]:
    """Load all chunks from all_chunks.json."""
    chunks_path = os.path.join(processed_dir, "all_chunks.json")
    if not os.path.exists(chunks_path):
        logger.error(
            "Chunks file not found at %s. Please run chunker first.", chunks_path
        )
        return []

    with open(chunks_path, "r", encoding="utf-8") as f:
        chunks = json.load(f)

    logger.info("Loaded %d chunks from %s", len(chunks), chunks_path)
    return chunks


# ═════════════════════════════════════════════════════════════
# 2. Embedding
# ═════════════════════════════════════════════════════════════


def embed_chunks(
    chunks: List[Dict[str, Any]], model: SentenceTransformer
) -> List[List[float]]:
    """Generate embeddings for a list of chunks."""
    logger.info("Generating embeddings for %d chunks...", len(chunks))
    texts = [chunk["text"] for chunk in chunks]
    # normalize_embeddings=True since we are using cosine distance metric
    embeddings = model.encode(texts, show_progress_bar=True, normalize_embeddings=True)

    # Convert numpy arrays to lists for ChromaDB
    embeddings_list = embeddings.tolist()
    logger.info(
        "Generated %d embeddings of dimension %d",
        len(embeddings_list),
        len(embeddings_list[0]),
    )
    return embeddings_list


# ═════════════════════════════════════════════════════════════
# 3. ChromaDB Storage
# ═════════════════════════════════════════════════════════════


def store_in_chroma(
    chunks: List[Dict[str, Any]], embeddings: List[List[float]]
) -> None:
    """Upsert chunks and embeddings into ChromaDB."""
    logger.info("Connecting to ChromaDB at %s", CHROMA_DB_PATH)
    os.makedirs(CHROMA_DB_PATH, exist_ok=True)

    client = chromadb.PersistentClient(path=CHROMA_DB_PATH)

    # Use cosine distance metric
    collection = client.get_or_create_collection(
        name=CHROMA_COLLECTION, metadata={"hnsw:space": "cosine"}
    )

    ids = [chunk["id"] for chunk in chunks]
    texts = [chunk["text"] for chunk in chunks]
    metadatas = [chunk["metadata"] for chunk in chunks]

    logger.info(
        "Upserting %d records into collection '%s'...", len(ids), CHROMA_COLLECTION
    )
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=texts,
        metadatas=metadatas,
    )

    count = collection.count()
    logger.info("Successfully upserted. Collection now has %d records.", count)


# ═════════════════════════════════════════════════════════════
# 4. Metadata Update
# ═════════════════════════════════════════════════════════════


def update_metadata(chunks: List[Dict[str, Any]]) -> None:
    """Update metadata.json with chunk_count per scheme."""
    if not os.path.exists(METADATA_FILE):
        logger.warning("Metadata file not found at %s. Skipping update.", METADATA_FILE)
        return

    with open(METADATA_FILE, "r", encoding="utf-8") as f:
        metadata = json.load(f)

    # Count chunks per scheme
    scheme_counts = {}
    for chunk in chunks:
        scheme_name = chunk["metadata"]["scheme_name"]
        scheme_counts[scheme_name] = scheme_counts.get(scheme_name, 0) + 1

    # Update metadata entries
    updated_count = 0
    for entry in metadata:
        scheme_name = entry.get("scheme_name")
        if scheme_name in scheme_counts:
            entry["chunk_count"] = scheme_counts[scheme_name]
            updated_count += 1

    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(metadata, f, indent=2, ensure_ascii=False)

    logger.info(
        "Updated chunk counts for %d schemes in %s", updated_count, METADATA_FILE
    )


# ═════════════════════════════════════════════════════════════
# 5. Orchestration
# ═════════════════════════════════════════════════════════════


def run_embedding_pipeline() -> None:
    """
    Full embedding pipeline entry point:
    1. Load chunks from data/processed/all_chunks.json
    2. Load embedding model
    3. Generate embeddings
    4. Upsert into ChromaDB
    5. Update metadata.json
    """
    logger.info("═" * 60)
    logger.info("MUTUAL FUND FAQ ASSISTANT — Embedding Pipeline")
    logger.info("═" * 60)

    chunks = load_chunks()
    if not chunks:
        logger.error("No chunks to embed. Exiting.")
        return

    model = get_embedding_model()
    embeddings = embed_chunks(chunks, model)

    store_in_chroma(chunks, embeddings)
    update_metadata(chunks)

    # Summary
    logger.info("═" * 60)
    logger.info("EMBEDDING SUMMARY")
    logger.info("═" * 60)

    schemes = set(c["metadata"]["scheme_name"] for c in chunks)
    logger.info(
        "Embedded and stored %d chunks across %d schemes into ChromaDB",
        len(chunks),
        len(schemes),
    )
    logger.info("ChromaDB Path: %s", CHROMA_DB_PATH)
    logger.info("Collection: %s", CHROMA_COLLECTION)
    logger.info("Model: %s (Dim: %d)", EMBEDDING_MODEL, len(embeddings[0]))
    logger.info("Done.")


# ═════════════════════════════════════════════════════════════
# Entry Point
# ═════════════════════════════════════════════════════════════

if __name__ == "__main__":
    run_embedding_pipeline()
