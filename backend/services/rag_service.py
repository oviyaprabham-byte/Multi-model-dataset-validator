"""
rag_service.py — Lightweight keyword-based RAG for document Q&A.

Design:
  - Pure Python (no vector DB, no heavy ML library)
  - TF-IDF-style keyword frequency scoring
  - Cosine similarity between query and chunks
  - STRICTLY isolated by session_id: Dataset A never retrieves Dataset B's chunks
  - In-memory index (auto-rebuilt per server session)
"""

import re
import math
from typing import Dict, List, Optional, Tuple

# ── In-memory index: {session_id: List[str]} ────────────────────────────────
_CHUNK_STORE: Dict[str, List[str]] = {}

# Common English stop-words to ignore in keyword matching
_STOP_WORDS = {
    "a", "an", "the", "is", "it", "in", "on", "at", "to", "of", "for",
    "and", "or", "but", "not", "with", "this", "that", "are", "was",
    "has", "have", "had", "be", "by", "from", "as", "its", "which",
    "what", "how", "when", "where", "who", "do", "does", "did", "will",
    "can", "could", "would", "should", "may", "might", "i", "you", "we",
    "they", "he", "she", "me", "my", "your", "their", "our", "about",
    "more", "also", "than", "then", "so", "if", "no", "yes", "all",
    "any", "each", "some", "there", "here", "up", "down", "into",
}


def _tokenize(text: str) -> List[str]:
    """Lowercase, split on non-alpha, remove stop-words."""
    tokens = re.findall(r"[a-z]+", text.lower())
    return [t for t in tokens if t not in _STOP_WORDS and len(t) > 1]


def _tf(tokens: List[str]) -> Dict[str, float]:
    """Term frequency dict."""
    freq: Dict[str, float] = {}
    for t in tokens:
        freq[t] = freq.get(t, 0) + 1
    total = max(len(tokens), 1)
    return {k: v / total for k, v in freq.items()}


def _cosine_sim(tf_a: Dict[str, float], tf_b: Dict[str, float]) -> float:
    """Cosine similarity between two TF dicts."""
    keys = set(tf_a) & set(tf_b)
    if not keys:
        return 0.0
    dot   = sum(tf_a[k] * tf_b[k] for k in keys)
    mag_a = math.sqrt(sum(v * v for v in tf_a.values()))
    mag_b = math.sqrt(sum(v * v for v in tf_b.values()))
    if mag_a == 0 or mag_b == 0:
        return 0.0
    return dot / (mag_a * mag_b)


def build_index(session_id: str, text: str, chunk_size: int = 200) -> int:
    """
    Chunk text into ~chunk_size word segments and store under session_id.
    Returns the number of chunks created.
    """
    words = text.split()
    chunks: List[str] = []
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i: i + chunk_size])
        if chunk.strip():
            chunks.append(chunk)

    _CHUNK_STORE[session_id] = chunks
    return len(chunks)


def retrieve(session_id: str, question: str, top_k: int = 3) -> List[str]:
    """
    Return the top_k most relevant chunks for the question.
    ONLY looks at chunks for the given session_id.
    """
    chunks = _CHUNK_STORE.get(session_id, [])
    if not chunks:
        return []

    q_tf    = _tf(_tokenize(question))
    scored: List[Tuple[float, str]] = []

    for chunk in chunks:
        c_tf  = _tf(_tokenize(chunk))
        score = _cosine_sim(q_tf, c_tf)
        scored.append((score, chunk))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [chunk for _, chunk in scored[:top_k]]


def has_index(session_id: str) -> bool:
    return session_id in _CHUNK_STORE and len(_CHUNK_STORE[session_id]) > 0


def clear_index(session_id: str):
    """Remove the index for a session."""
    _CHUNK_STORE.pop(session_id, None)


def answer_question(
    session_id: str,
    question: str,
    doc_text: str,
    use_llm: bool = True,
) -> str:
    """
    Full RAG pipeline:
      1. Ensure index is built for session_id.
      2. Retrieve top relevant chunks.
      3. Ask LLM (or fallback to rule-based).

    Returns the answer string.
    """
    from services.llm_service import get_llm_answer, is_llm_configured

    # Build index if not already built
    if not has_index(session_id):
        build_index(session_id, doc_text)

    chunks = retrieve(session_id, question)
    context = "\n\n".join(chunks) if chunks else doc_text[:2000]

    if use_llm and is_llm_configured():
        return get_llm_answer(context, question)

    # Rule-based fallback — keyword search in retrieved chunks
    return _rule_based_answer(question, context, doc_text)


# ── Rule-based fallback ───────────────────────────────────────────────────────

def _rule_based_answer(question: str, context: str, full_doc: str) -> str:
    """
    Simple keyword matching to answer common questions without an LLM.
    Searches the retrieved context first, then the full document.
    """
    q_lower = question.lower()
    search_text = context or full_doc

    # Try to extract a relevant sentence from context
    sentences = re.split(r"(?<=[.!?])\s+", search_text)

    q_tokens = set(_tokenize(q_lower))

    # Score each sentence
    best_score = 0
    best_sentence = ""
    for sent in sentences:
        s_tokens = set(_tokenize(sent.lower()))
        overlap = len(q_tokens & s_tokens)
        if overlap > best_score:
            best_score = overlap
            best_sentence = sent

    if best_score >= 1 and best_sentence.strip():
        return (
            f"Based on the documentation: {best_sentence.strip()}\n\n"
            "For more detailed answers, configure an LLM provider in the backend .env file."
        )

    # Topic-based fallback responses
    if any(w in q_lower for w in ["quality", "score", "rating"]):
        return _extract_about("quality score", full_doc)
    if any(w in q_lower for w in ["ready", "training", "readiness"]):
        return _extract_about("readiness", full_doc)
    if any(w in q_lower for w in ["issue", "problem", "error"]):
        return _extract_about("issues", full_doc)
    if any(w in q_lower for w in ["recommend", "suggestion", "fix", "improve"]):
        return _extract_about("recommendations", full_doc)
    if any(w in q_lower for w in ["algorithm", "ml", "model", "machine learning"]):
        return _extract_about("algorithm", full_doc)
    if any(w in q_lower for w in ["missing", "null", "nan"]):
        return _extract_about("missing values", full_doc)
    if any(w in q_lower for w in ["duplicate"]):
        return _extract_about("duplicate", full_doc)
    if any(w in q_lower for w in ["corrupted", "corrupt"]):
        return _extract_about("corrupted", full_doc)
    if any(w in q_lower for w in ["dataset", "what is", "describe"]):
        return _extract_about("Dataset Overview", full_doc)
    if any(w in q_lower for w in ["limitation"]):
        return _extract_about("limitations", full_doc)

    return (
        "This information is not clearly available in the documentation. "
        "Try asking about: quality score, issues, recommendations, training readiness, "
        "ML algorithm, missing values, or dataset overview. "
        "For detailed AI-powered answers, configure an LLM provider."
    )


def _extract_about(keyword: str, text: str) -> str:
    """Extract sentences around a keyword."""
    keyword_lower = keyword.lower()
    sentences = re.split(r"(?<=[.!?\n])\s+", text)
    relevant = [
        s.strip() for s in sentences
        if keyword_lower in s.lower() and len(s.strip()) > 10
    ]
    if relevant:
        answer = " ".join(relevant[:3])
        return f"From the documentation: {answer}"
    return f"Information about '{keyword}' was not found in this documentation."
