"""
Retriever — embeds queries and performs cosine similarity search.
"""

import os
import sys
import logging
from typing import List, Dict, Any

# ── Add project root to path for imports ──────────────────────
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import chromadb
from sentence_transformers import SentenceTransformer

from src.utils.config import (
    CHROMA_DB_PATH,
    CHROMA_COLLECTION,
    EMBEDDING_MODEL,
    TOP_K,
    MIN_SIMILARITY_SCORE,
)
from src.retrieval.query_parser import extract_scheme_name

logger = logging.getLogger("retriever")

# Global instances for reuse
_chroma_client = None
_collection = None
_embedding_model = None


def _get_embedding_model():
    global _embedding_model
    if _embedding_model is None:
        _embedding_model = SentenceTransformer(EMBEDDING_MODEL)
    return _embedding_model


def _get_collection():
    global _chroma_client, _collection
    if _chroma_client is None:
        _chroma_client = chromadb.PersistentClient(path=CHROMA_DB_PATH)
        _collection = _chroma_client.get_collection(name=CHROMA_COLLECTION)
    return _collection


def retrieve(query: str, top_k: int = TOP_K) -> List[Dict[str, Any]]:
    """
    Embed query, apply metadata filter if scheme_name is found,
    and return top-K chunks.
    """
    # 1. Parse query for scheme_name
    target_scheme = extract_scheme_name(query)

    # 2. Setup filtering
    where_filter = {}
    if target_scheme:
        where_filter = {"scheme_name": target_scheme}
        logger.info(f"Filtering retrieval by scheme_name: '{target_scheme}'")
    else:
        logger.info("No specific scheme detected in query. Searching across all funds.")

    # 3. Embed the query
    model = _get_embedding_model()
    # Normalize since Chroma uses cosine distance
    query_embedding = model.encode([query], normalize_embeddings=True).tolist()[0]

    # 4. Search in ChromaDB
    collection = _get_collection()
    results = collection.query(
        query_embeddings=[query_embedding],
        n_results=top_k,
        where=where_filter if where_filter else None,
    )

    # 5. Format results and apply threshold
    formatted_results = []

    # Chroma returns lists of lists (one per query)
    if not results["documents"] or not results["documents"][0]:
        return formatted_results

    documents = results["documents"][0]
    metadatas = results["metadatas"][0]
    distances = results["distances"][0]

    for doc, meta, dist in zip(documents, metadatas, distances):
        # Convert distance to similarity score (assuming cosine space: distance = 1 - similarity)
        # Note: sometimes Chroma can return slightly negative distances or >1 due to float precision
        # We will just pass the distance as requested by plan, and also check a rough threshold.
        # Let's say MIN_SIMILARITY_SCORE = 0.3 means distance must be <= 0.7
        similarity = 1.0 - dist
        if similarity >= MIN_SIMILARITY_SCORE:
            formatted_results.append(
                {
                    "text": doc,
                    "source_url": meta.get("source_url", ""),
                    "scheme_name": meta.get("scheme_name", ""),
                    "section": meta.get("section", ""),
                    "distance": dist,
                }
            )

    logger.info(
        f"Retrieved {len(formatted_results)} chunks above similarity threshold."
    )
    return formatted_results


if __name__ == "__main__":
    # Setup basic logging for testing
    logging.basicConfig(level=logging.INFO)

    # Quick test as specified in the plan
    print("Testing 'expense ratio HDFC Large Cap'...")
    res1 = retrieve("expense ratio HDFC Large Cap")
    import json

    print(json.dumps(res1, indent=2))
