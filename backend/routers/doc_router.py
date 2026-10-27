"""
doc_router.py — Dataset Documentation CRUD endpoints.

Endpoints:
    GET  /api/docs                          → list all docs
    GET  /api/docs/{session_id}             → get one doc
    POST /api/docs/{session_id}/generate    → generate / regenerate doc
    DELETE /api/docs/{session_id}           → delete doc
"""

import json
from datetime import datetime
from pathlib import Path

from fastapi import APIRouter, HTTPException
from fastapi.responses import JSONResponse

from services.doc_generator import generate_documentation, documentation_to_text

router = APIRouter(prefix="/api/docs", tags=["documentation"])

DOCS_FILE = Path("docs_store.json")


# ── Persistence helpers ───────────────────────────────────────────────────────

def load_docs() -> dict:
    if DOCS_FILE.exists():
        try:
            with open(DOCS_FILE, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception:
            return {}
    return {}


def save_docs(docs: dict):
    with open(DOCS_FILE, "w", encoding="utf-8") as f:
        json.dump(docs, f, indent=2, default=str)


# ── Routes ───────────────────────────────────────────────────────────────────

@router.get("")
def list_docs():
    """Return all generated documentations as a list."""
    docs = load_docs()
    result = []
    for session_id, doc in docs.items():
        result.append({
            "session_id":    session_id,
            "dataset_name":  doc.get("dataset_name", "Unknown"),
            "dataset_type":  doc.get("dataset_type", "Unknown"),
            "dataset_size":  doc.get("dataset_size", "Unknown"),
            "quality_score": doc.get("quality_score"),
            "quality_badge": doc.get("quality_badge"),
            "ai_readiness":  doc.get("ai_readiness"),
            "timestamp":     doc.get("timestamp"),
            "generated_at":  doc.get("generated_at"),
        })
    # Newest first
    result.sort(key=lambda x: x.get("generated_at", ""), reverse=True)
    return result


@router.get("/{session_id}")
def get_doc(session_id: str):
    """Return full documentation for a session."""
    docs = load_docs()
    if session_id not in docs:
        raise HTTPException(status_code=404, detail="Documentation not found for this session.")
    return docs[session_id]


@router.post("/{session_id}/generate")
def generate_doc(session_id: str):
    """
    Generate (or regenerate) documentation for an existing session.
    The session must still be in the in-memory sessions store.
    """
    # Import sessions from main lazily to avoid circular import
    from main import sessions

    if session_id not in sessions:
        raise HTTPException(
            status_code=404,
            detail="Session not found in memory. Re-validate the dataset to regenerate documentation.",
        )

    result = sessions[session_id]
    doc = generate_documentation(result)

    docs = load_docs()
    docs[session_id] = doc
    save_docs(docs)

    return doc


@router.delete("/{session_id}")
def delete_doc(session_id: str):
    """Delete documentation for a session."""
    docs = load_docs()
    if session_id not in docs:
        raise HTTPException(status_code=404, detail="Documentation not found.")
    del docs[session_id]
    save_docs(docs)
    return {"message": "Documentation deleted"}


# ── Internal helper (called from main.py auto-generate) ──────────────────────

def auto_generate_doc(session_id: str, validation_result) -> dict:
    """
    Called automatically after each validation to persist documentation.
    Does not require the session to still be in memory (result passed directly).
    """
    doc = generate_documentation(validation_result)
    docs = load_docs()
    docs[session_id] = doc
    save_docs(docs)
    return doc
