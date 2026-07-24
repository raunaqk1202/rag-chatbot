"""
LLM Client — handles Groq API communication with rate limiting and orchestration.
"""

import os
import sys
import logging
from typing import Dict, Any, List

# Add project root to path for imports
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from groq import Groq
import groq
from tenacity import (
    retry,
    wait_exponential,
    stop_after_attempt,
    retry_if_exception_type,
)

from src.utils.config import (
    GROQ_API_KEY,
    LLM_MODEL,
    LLM_TEMPERATURE,
    LLM_MAX_TOKENS,
)
from src.generation.prompt_templates import SYSTEM_PROMPT, USER_PROMPT
from src.retrieval.retriever import retrieve

logger = logging.getLogger("llm_client")

# Global client
_client = None


def get_llm_client() -> Groq:
    global _client
    if _client is None:
        if not GROQ_API_KEY:
            logger.warning("GROQ_API_KEY is missing. Please set it in .env")
        _client = Groq(api_key=GROQ_API_KEY)
    return _client


# We add retry logic specifically for rate limit errors and internal server errors.
# wait_exponential with min=2, max=20 will wait 2, 4, 8, 16... up to max.
@retry(
    wait=wait_exponential(min=2, max=20),
    stop=stop_after_attempt(5),
    retry=retry_if_exception_type(
        (groq.RateLimitError, groq.InternalServerError, groq.APIConnectionError)
    ),
)
def generate_answer(system_prompt: str, user_prompt: str) -> str:
    """Send prompt to LLM and return raw answer with retry logic for Groq limits."""
    client = get_llm_client()

    logger.info("Sending request to LLM (Model: %s)...", LLM_MODEL)
    response = client.chat.completions.create(
        model=LLM_MODEL,
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
        temperature=LLM_TEMPERATURE,
        max_tokens=LLM_MAX_TOKENS,
    )

    return response.choices[0].message.content.strip()


def build_context_string(chunks: List[Dict[str, Any]]) -> str:
    """Convert retrieved chunks into a single context string."""
    # To respect the 12K TPM limit, we shouldn't send excessive chunks.
    # By default, TOP_K is 4, which is typically well under 12K.
    # Each chunk is ~150-250 words (~200-350 tokens).
    # 4 chunks = ~1400 tokens context. Well within limits.
    context_parts = []
    for i, chunk in enumerate(chunks):
        text = chunk.get("text", "")
        # Add metadata attribution in context
        source_url = chunk.get("source_url", "")
        context_parts.append(f"--- Chunk {i+1} ---\n{text}\nURL: {source_url}")
    return "\n\n".join(context_parts)


def ask(query: str) -> dict:
    """
    Full RAG pipeline:
    1. Parse query & Retrieve top-K context chunks
    2. Build prompt with context
    3. Generate answer via LLM
    4. Format response with citation
    """
    logger.info("Processing query: '%s'", query)

    # 1 & 2. Retrieve chunks
    chunks = retrieve(query)

    if not chunks:
        answer = "I don't have this information in my current sources."
        return {"answer": answer, "citations": [], "query": query}

    # Build context
    context_str = build_context_string(chunks)

    # 3. Build prompts
    user_prompt = USER_PROMPT.format(context=context_str, query=query)

    # 4. Generate answer
    try:
        raw_answer = generate_answer(SYSTEM_PROMPT, user_prompt)
    except groq.RateLimitError:
        logger.error("Groq API rate limit exceeded after retries.")
        raw_answer = "I am currently receiving too many requests. Please wait a moment and try again."
    except Exception as e:
        logger.error("Failed to generate answer: %s", e)
        raw_answer = "An unexpected error occurred while connecting to the AI service."

    # Extract unique source URLs from retrieved chunks to pass to the UI
    unique_urls = list({c.get("source_url") for c in chunks if c.get("source_url")})

    # Extract scrape date from the first chunk that has one (assuming all chunks from the same ingestion have similar dates)
    scrape_date = next((c.get("scrape_date") for c in chunks if c.get("scrape_date") and c.get("scrape_date") != "Unknown"), "2026-07-14")

    return {"answer": raw_answer, "citations": unique_urls, "query": query, "scrape_date": scrape_date}


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    import json

    res = ask("What is the expense ratio of HDFC Large Cap Fund?")
    print(json.dumps(res, indent=2))
