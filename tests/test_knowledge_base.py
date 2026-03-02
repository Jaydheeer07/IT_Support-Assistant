import pytest
from knowledge_base.store import KnowledgeBase

def test_search_returns_results_above_threshold():
    kb = KnowledgeBase(persist_dir=":memory:")
    kb.add_document("clear-cookies", "To clear cookies in Chrome: Settings > Privacy > Clear browsing data > Cookies")
    results = kb.search("how to clear cookies chrome", top_k=3)
    assert len(results) > 0
    assert results[0]["confidence"] > 0.0
    assert "content" in results[0]
    assert "source" in results[0]

def test_search_returns_empty_for_unrelated_query():
    kb = KnowledgeBase(persist_dir=":memory:")
    kb.add_document("clear-cookies", "To clear cookies in Chrome: Settings > Privacy > Clear browsing data")
    results = kb.search("quantum physics equations", top_k=3, min_confidence=0.95)
    assert len(results) == 0
