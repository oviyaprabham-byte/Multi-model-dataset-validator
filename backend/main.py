import os
import uuid
import shutil
import json
from datetime import datetime
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from models.schemas import (
    DatasetType, DatasetInfo, ValidationResult, HistoryEntry, QualityScore
)
from validators.csv_validator import validate_csv
from validators.image_validator import validate_images
from validators.audio_validator import validate_audio
from validators.text_validator import validate_text
from services.quality_scorer import calculate_quality_score
from services.recommender import generate_recommendations
from services.report_generator import generate_pdf, generate_excel
from routers.doc_router import router as doc_router, auto_generate_doc
from routers.agent_router import router as agent_router

# ── App Setup ──────────────────────────────────────────────────────────────
app = FastAPI(
    title="Dataset Validator API",
    description="Multi-Modal Intelligent Dataset Validator",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount new routers
app.include_router(doc_router)
app.include_router(agent_router)

UPLOAD_DIR = Path("uploads")
REPORT_DIR = Path("reports")
HISTORY_FILE = Path("history.json")
SESSIONS_FILE = Path("sessions_store.json")   # full result persistence
UPLOAD_DIR.mkdir(exist_ok=True)
REPORT_DIR.mkdir(exist_ok=True)

# In-memory session store (also persisted to JSON)
sessions: dict = {}


# ── Helpers ────────────────────────────────────────────────────────────────
def human_size(size_bytes: int) -> str:
    for unit in ["B", "KB", "MB", "GB"]:
        if size_bytes < 1024:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.1f} TB"


def detect_dataset_type(filename: str) -> DatasetType:
    ext = Path(filename).suffix.lower()
    if ext == ".csv":
        return DatasetType.CSV
    elif ext in {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tiff"}:
        return DatasetType.IMAGE
    elif ext in {".wav", ".mp3", ".ogg", ".flac", ".aac", ".m4a"}:
        return DatasetType.AUDIO
    elif ext == ".txt":
        return DatasetType.TEXT
    elif ext == ".zip":
        return DatasetType.IMAGE  # Default ZIP to image; will re-detect from contents
    return DatasetType.UNKNOWN


def load_history() -> list:
    if HISTORY_FILE.exists():
        try:
            with open(HISTORY_FILE, "r") as f:
                return json.load(f)
        except Exception:
            return []
    return []


def save_history(entry: dict):
    history = load_history()
    history.insert(0, entry)
    history = history[:50]  # Keep last 50
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)


def save_session(session_id: str, result):
    """Persist the full ValidationResult to disk so reports survive server restarts."""
    try:
        store = {}
        if SESSIONS_FILE.exists():
            with open(SESSIONS_FILE, "r") as f:
                store = json.load(f)
        store[session_id] = result.model_dump(mode="json")
        # Keep only the latest 100 sessions to avoid unbounded growth
        if len(store) > 100:
            oldest = sorted(store.keys())[:-100]
            for k in oldest:
                del store[k]
        with open(SESSIONS_FILE, "w") as f:
            json.dump(store, f, indent=2)
    except Exception:
        pass  # Never block the response


def load_session(session_id: str):
    """Load a ValidationResult from the on-disk store (fallback when not in RAM)."""
    try:
        if SESSIONS_FILE.exists():
            with open(SESSIONS_FILE, "r") as f:
                store = json.load(f)
            if session_id in store:
                from models.schemas import ValidationResult as VR
                return VR(**store[session_id])
    except Exception:
        pass
    return None


def determine_readiness(issues, quality_score_val):
    reasons = []
    is_ready = True

    critical_issue_titles = {
        "corrupted images", "corrupted audio files", "corrupted",
        "missing labels", "class imbalance", "no images found",
        "no audio found", "no text files", "file read error"
    }

    for issue in issues:
        if issue.severity == "high":
            reasons.append(f"{issue.title}: {issue.description}")
            is_ready = False
        elif issue.title.lower() in critical_issue_titles:
            reasons.append(f"{issue.title}: {issue.description}")
            is_ready = False

    if quality_score_val < 60:
        is_ready = False
        reasons.append(f"Overall quality score {quality_score_val:.0f}/100 is below the threshold of 60")

    return is_ready, list(set(reasons))


# ── Routes ─────────────────────────────────────────────────────────────────

@app.get("/")
def root():
    return {"message": "Dataset Validator API v1.0", "status": "running"}


@app.get("/health")
def health():
    return {"status": "ok", "timestamp": datetime.now().isoformat()}


@app.post("/api/validate")
async def validate_dataset(file: UploadFile = File(...)):
    session_id = str(uuid.uuid4())
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Save uploaded file
    filename = file.filename or "upload"
    file_path = UPLOAD_DIR / f"{session_id}_{filename}"
    content = await file.read()
    file_size = len(content)

    with open(file_path, "wb") as f:
        f.write(content)

    # Detect type
    dataset_type = detect_dataset_type(filename)

    # For ZIP, detect by peeking inside
    if filename.endswith(".zip"):
        import zipfile as zf
        try:
            with zf.ZipFile(file_path) as z:
                names = z.namelist()
            exts = {Path(n).suffix.lower() for n in names if Path(n).suffix}
            if exts & {".wav", ".mp3", ".ogg", ".flac"}:
                dataset_type = DatasetType.AUDIO
            elif exts & {".txt"}:
                dataset_type = DatasetType.TEXT
            elif exts & {".csv"}:
                dataset_type = DatasetType.CSV
            else:
                dataset_type = DatasetType.IMAGE
        except Exception:
            dataset_type = DatasetType.IMAGE

    # Run validation
    if dataset_type == DatasetType.CSV:
        result_data = validate_csv(str(file_path))
    elif dataset_type == DatasetType.IMAGE:
        result_data = validate_images(str(file_path))
    elif dataset_type == DatasetType.AUDIO:
        result_data = validate_audio(str(file_path))
    elif dataset_type == DatasetType.TEXT:
        result_data = validate_text(str(file_path))
    else:
        result_data = {
            "checks": [], "issues": [], "dashboard_data": {},
            "stats": {"missing_ratio": 0, "duplicate_ratio": 0, "corrupted_ratio": 0,
                      "empty_ratio": 0, "format_issues": False, "class_imbalance": False,
                      "missing_labels": False}
        }

    checks = result_data["checks"]
    issues = result_data["issues"]
    dashboard_data = result_data.get("dashboard_data", {})
    stats = result_data.get("stats", {})

    # Quality score
    score_data = calculate_quality_score(stats, dataset_type)
    quality_score = QualityScore(**score_data)

    # Recommendations
    recommendations = generate_recommendations(issues)

    # Readiness
    is_ready, readiness_reasons = determine_readiness(issues, quality_score.score)

    # Dataset info
    stat = stats
    dataset_info = DatasetInfo(
        filename=filename,
        size_bytes=file_size,
        size_human=human_size(file_size),
        dataset_type=dataset_type,
        format=Path(filename).suffix.upper(),
        total_rows=stat.get("total_rows"),
        total_columns=stat.get("total_cols"),
        total_files=stat.get("total_files"),
    )

    # Build full result
    validation_result = ValidationResult(
        session_id=session_id,
        dataset_info=dataset_info,
        checks=checks,
        issues=issues,
        recommendations=recommendations,
        quality_score=quality_score,
        is_ready=is_ready,
        readiness_reasons=readiness_reasons,
        dashboard_data=dashboard_data,
        timestamp=timestamp,
    )

    # Store in memory & persist to disk
    sessions[session_id] = validation_result
    save_history({
        "session_id": session_id,
        "filename": filename,
        "dataset_type": dataset_type,
        "quality_score": quality_score.score,
        "badge": quality_score.badge,
        "is_ready": is_ready,
        "timestamp": timestamp,
    })
    save_session(session_id, validation_result)  # persist full result for report generation

    # Auto-generate documentation after every validation
    try:
        auto_generate_doc(session_id, validation_result)
    except Exception:
        pass  # Never block the validation response if doc generation fails

    return validation_result


@app.get("/api/report/pdf/{session_id}")
def download_pdf(session_id: str):
    result = sessions.get(session_id) or load_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found. Re-validate the dataset to download the report.")
    output_path = str(REPORT_DIR / f"{session_id}_report.pdf")
    generate_pdf(result, output_path)
    return FileResponse(
        output_path,
        media_type="application/pdf",
        filename=f"dataset_report_{session_id[:8]}.pdf",
        headers={"Content-Disposition": f'attachment; filename="dataset_report_{session_id[:8]}.pdf"'},
    )


@app.get("/api/report/excel/{session_id}")
def download_excel(session_id: str):
    result = sessions.get(session_id) or load_session(session_id)
    if not result:
        raise HTTPException(status_code=404, detail="Session not found. Re-validate the dataset to download the report.")
    output_path = str(REPORT_DIR / f"{session_id}_report.xlsx")
    generate_excel(result, output_path)
    return FileResponse(
        output_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=f"dataset_report_{session_id[:8]}.xlsx",
        headers={"Content-Disposition": f'attachment; filename="dataset_report_{session_id[:8]}.xlsx"'},
    )


@app.get("/api/history")
def get_history():
    return load_history()


@app.get("/api/results/{session_id}")
def get_result(session_id: str):
    """Restore a full validation result from an in-memory session."""
    if session_id not in sessions:
        raise HTTPException(
            status_code=404,
            detail="Session not found in memory. Results are only available for the current server session."
        )
    return sessions[session_id]


@app.delete("/api/history/{session_id}")
def delete_history(session_id: str):
    history = load_history()
    history = [h for h in history if h["session_id"] != session_id]
    with open(HISTORY_FILE, "w") as f:
        json.dump(history, f, indent=2)
    if session_id in sessions:
        del sessions[session_id]
    # Clean up any leftover upload/report files for this session
    for f in UPLOAD_DIR.glob(f"{session_id}_*"):
        try:
            f.unlink()
        except Exception:
            pass
    for f in REPORT_DIR.glob(f"{session_id}_*"):
        try:
            f.unlink()
        except Exception:
            pass
    return {"message": "Deleted"}


@app.delete("/api/history")
def clear_all_history():
    """Clear the entire validation history."""
    if HISTORY_FILE.exists():
        HISTORY_FILE.unlink()
    sessions.clear()
    return {"message": "All history cleared"}


# ── Serve React frontend (production build) ───────────────────────────────
STATIC_DIR = Path("static")
if STATIC_DIR.exists():
    # Mount assets sub-directory first
    assets_dir = STATIC_DIR / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=str(assets_dir)), name="assets")

    @app.get("/{full_path:path}", include_in_schema=False)
    async def serve_spa(full_path: str):
        """Catch-all: serve index.html for React Router (SPA fallback)."""
        index = STATIC_DIR / "index.html"
        if index.exists():
            return FileResponse(str(index))
        return {"detail": "Frontend not built"}


if __name__ == "__main__":
    import uvicorn
    port = int(os.environ.get("PORT", 8000))
    uvicorn.run("main:app", host="0.0.0.0", port=port)
