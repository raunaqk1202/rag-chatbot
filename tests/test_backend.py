"""
End-to-end tests for the backend pipeline.
Tests edge cases, guardrails, and successful retrieval.
"""
import pytest
from src.backend_app import process_query

@pytest.fixture(autouse=True)
def mock_ask(monkeypatch):
    def fake_ask(query):
        # We can simulate responses based on query
        return {
            "answer": "This is a simulated factual answer.",
            "citations": ["https://groww.in/mock-url"],
            "query": query
        }
    monkeypatch.setattr("src.backend_app.ask", fake_ask)

def test_factual_query_1():
    res = process_query("What is the expense ratio of HDFC Large Cap Fund?")
    assert "This is a simulated factual answer" in res
    assert "https://groww.in/mock-url" in res
    assert "Last updated from sources" in res

def test_factual_query_2():
    res = process_query("What is the exit load for HDFC Small Cap Fund?")
    assert "This is a simulated factual answer" in res

def test_factual_query_3():
    res = process_query("What is the minimum SIP amount for HDFC Mid Cap Fund?")
    assert "This is a simulated factual answer" in res

def test_factual_query_4():
    res = process_query("What benchmark does HDFC Gold ETF FoF track?")
    assert "This is a simulated factual answer" in res

def test_factual_query_5():
    res = process_query("What is the risk category of HDFC Silver ETF FoF?")
    assert "This is a simulated factual answer" in res

def test_advisory_query_6():
    res = process_query("Should I invest in HDFC Large Cap Fund?")
    assert "unable to offer investment advice" in res

def test_advisory_query_7():
    res = process_query("Which is better — HDFC Mid Cap or Small Cap?")
    assert "unable to offer investment advice" in res

def test_advisory_query_8():
    res = process_query("Is HDFC Gold ETF a good investment?")
    assert "unable to offer investment advice" in res

def test_pii_query_9():
    res = process_query("My PAN is ABCDE1234F, check my portfolio")
    assert "For your security, please do not share personal information" in res

def test_pii_query_10():
    res = process_query("My phone number is 9876543210")
    assert "For your security, please do not share personal information" in res

def test_out_of_scope_query_11():
    res = process_query("What is the weather in Mumbai?")
    assert "I can only answer questions about HDFC mutual fund schemes" in res

def test_out_of_scope_query_12():
    res = process_query("Tell me about SBI Blue Chip Fund")
    # This might fail initially if "fund" causes it to be factual.
    # We will verify the behavior.
    assert "I can only answer questions about HDFC mutual fund schemes" in res

def test_edge_empty_query_13():
    res = process_query("")
    assert "Please ask a question" in res
    res2 = process_query("   ")
    assert "Please ask a question" in res2

def test_edge_long_input_14():
    long_q = "hdfc fund " * 120 # ~1200 characters
    res = process_query(long_q)
    assert "This is a simulated factual answer" in res

def test_edge_no_scheme_15():
    res = process_query("expense ratio")
    assert "This is a simulated factual answer" in res
