from app.retrieval.chroma_store import retriever


def test_retrieval_returns_grounded_sop_citations():
    citations = retriever.retrieve("battery critical voltage emergency landing RTH", top_k=2)
    assert len(citations) > 0
    top = citations[0]
    assert "SOP-001" in top["sop_id"]
    assert "Battery" in top["title"]
    assert top["relevance_score"] > 0.30
    assert len(top["excerpt"]) > 10


def test_retrieval_returns_empty_when_no_relevant_sop():
    citations = retriever.retrieve("extraterrestrial alien pulsar frequency transmission", top_k=2, min_similarity=0.45)
    assert len(citations) == 0


def test_retrieval_handles_conflicting_sops():
    citations = retriever.retrieve("High wind perimeter breach conflicting directive protocol SOP-005", top_k=2)
    assert len(citations) > 0
    assert any("SOP-005" in c["sop_id"] for c in citations)
