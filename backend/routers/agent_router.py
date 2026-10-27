"""
agent_router.py — AI Agent endpoints for document reading and Q&A.

Endpoints:
    GET  /api/agent/doc/{session_id}/text    → plain-text TTS script
    POST /api/agent/doc/{session_id}/ask     → ask a Q&A question (RAG + optional LLM)
    GET  /api/agent/chat/{session_id}        → get chat history
    DELETE /api/agent/chat/{session_id}      → clear chat history
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from services.doc_generator import documentation_to_text
from services.rag_service import answer_question, build_index, clear_index
from services.llm_service import get_llm_status

router = APIRouter(prefix="/api/agent", tags=["agent"])

DOCS_FILE = Path("docs_store.json")
CHAT_FILE = Path("chat_history.json")


# ── Pydantic models ───────────────────────────────────────────────────────────

class AskRequest(BaseModel):
    question: str
    use_llm: Optional[bool] = True


# ── Persistence helpers ───────────────────────────────────────────────────────

def _load_docs() -> dict:
    if DOCS_FILE.exists():
        try:
            with open(DOCS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _load_chat() -> dict:
    if CHAT_FILE.exists():
        try:
            with open(CHAT_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def _save_chat(chat: dict):
    with open(CHAT_FILE, "w", encoding="utf-8") as f:
        json.dump(chat, f, indent=2, default=str)


# ── Routes ────────────────────────────────────────────────────────────────────

@router.get("/doc/{session_id}/text")
def get_doc_text(session_id: str):
    """
    Return a natural-language TTS script for the documentation of a session.
    Also pre-builds the RAG index for the session.
    """
    docs = _load_docs()
    if session_id not in docs:
        raise HTTPException(
            status_code=404,
            detail="Documentation not found for this session. Generate it first from the Documentation page.",
        )
    doc = docs[session_id]
    text = documentation_to_text(doc)

    # Pre-build RAG index in background
    build_index(session_id, text)

    return {
        "session_id": session_id,
        "dataset_name": doc.get("dataset_name", "Unknown"),
        "text": text,
        "chunk_count": len(text.split()) // 200 + 1,
    }


@router.post("/doc/{session_id}/ask")
def ask_question_endpoint(session_id: str, body: AskRequest):
    """
    Answer a question about the dataset documentation.
    Uses RAG + optional LLM (or rule-based fallback if LLM not configured).
    """
    if not body.question or not body.question.strip():
        raise HTTPException(status_code=400, detail="Question cannot be empty.")

    docs = _load_docs()
    if session_id not in docs:
        raise HTTPException(
            status_code=404,
            detail="Documentation not found for this session.",
        )

    doc = docs[session_id]
    doc_text = documentation_to_text(doc)

    answer = answer_question(
        session_id=session_id,
        question=body.question.strip(),
        doc_text=doc_text,
        use_llm=body.use_llm,
    )

    # Persist chat message
    chat = _load_chat()
    if session_id not in chat:
        chat[session_id] = []

    timestamp = datetime.now().isoformat()
    chat[session_id].append({
        "role": "user",
        "content": body.question.strip(),
        "timestamp": timestamp,
    })
    chat[session_id].append({
        "role": "assistant",
        "content": answer,
        "timestamp": timestamp,
    })
    # Keep last 100 messages per session
    chat[session_id] = chat[session_id][-100:]
    _save_chat(chat)

    return {
        "session_id": session_id,
        "question": body.question.strip(),
        "answer": answer,
        "llm_status": get_llm_status(),
        "timestamp": timestamp,
    }


@router.get("/chat/{session_id}")
def get_chat(session_id: str):
    """Return the chat history for a session."""
    chat = _load_chat()
    return {
        "session_id": session_id,
        "messages": chat.get(session_id, []),
    }


@router.delete("/chat/{session_id}")
def clear_chat(session_id: str):
    """Clear chat history for a session."""
    chat = _load_chat()
    if session_id in chat:
        del chat[session_id]
        _save_chat(chat)
    clear_index(session_id)
    return {"message": "Chat history cleared", "session_id": session_id}


@router.get("/status")
def agent_status():
    """Return LLM configuration status."""
    return get_llm_status()
