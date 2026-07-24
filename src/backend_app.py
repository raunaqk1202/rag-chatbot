"""
Backend Orchestrator — integrates query classification, RAG, and formatting.
"""

import logging
from src.classifier.query_classifier import classify_query, QueryType
from src.generation.llm_client import ask
from src.utils.formatter import format_response, format_refusal, validate_response

logger = logging.getLogger(__name__)


def process_query(query: str) -> str:
    """
    Main entry point for processing a user query.
    1. Validate input
    2. Classify query
    3. If FACTUAL -> run RAG pipeline & format
    4. Otherwise -> return formatted refusal
    """
    if not query or not query.strip():
        return "Please ask a question."

    query = query.strip()
    if len(query) > 500:
        logger.warning("Query too long, truncating to 500 chars")
        query = query[:500]

    q_type = classify_query(query)

    if q_type == QueryType.FACTUAL:
        # Run RAG
        try:
            result = ask(query)
            formatted = format_response(result["answer"], result.get("citations", []))

            # Response validation check
            if not validate_response(formatted):
                logger.warning("Generated response failed validation")

            return formatted
        except Exception as e:
            logger.error(f"Error in RAG pipeline: {e}")
            return "An unexpected error occurred while processing your request."
    else:
        # Handle Refusal
        return format_refusal(q_type)


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    print(process_query("What is the expense ratio of HDFC Large Cap Fund?"))
