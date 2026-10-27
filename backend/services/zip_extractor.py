"""
zip_extractor.py  — Safe ZIP extraction + multi-type validation dispatcher

Security features:
  - Prevents zip-slip / path traversal attacks
  - Rejects absolute paths and paths with ".." components
  - Handles corrupted ZIP files gracefully
  - Does NOT overwrite original uploaded files
"""

import os
import zipfile
import shutil
import tempfile
from pathlib import Path
from typing import Dict, Any, List, Optional

# File-type categorisation
CSV_EXTS   = {".csv"}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tiff", ".tif"}
AUDIO_EXTS = {".wav", ".mp3", ".ogg", ".flac", ".aac", ".m4a"}
TEXT_EXTS  = {".txt"}

def _is_safe_path(zip_ref: zipfile.ZipFile, member: str, dest: Path) -> bool:
    """Return True only if the extracted member stays inside dest."""
    target = (dest / member).resolve()
    try:
        target.relative_to(dest.resolve())
        return True
    except ValueError:
        return False


def extract_zip_safe(zip_path: str, extract_dir: str) -> Dict[str, Any]:
    """
    Safely extract a ZIP file.

    Returns:
        {
            "success": bool,
            "error": Optional[str],
            "extracted_files": List[str],   # absolute paths
            "skipped": List[str],           # paths that were unsafe / rejected
        }
    """
    dest = Path(extract_dir)
    dest.mkdir(parents=True, exist_ok=True)

    extracted: List[str] = []
    skipped:   List[str] = []

    try:
        with zipfile.ZipFile(zip_path, "r") as zf:
            # Iterate members and apply safety checks
            for member in zf.namelist():
                # Skip directories
                if member.endswith("/") or member.endswith("\\"):
                    continue

                # Normalise member path (strip leading / or drive letters)
                member_clean = member.lstrip("/\\")
                if not member_clean:
                    continue

                # Safety check — must stay inside dest
                if not _is_safe_path(zf, member_clean, dest):
                    skipped.append(member)
                    continue

                # Also reject absolute or traversal-containing raw names
                raw = Path(member_clean)
                if raw.is_absolute() or ".." in raw.parts:
                    skipped.append(member)
                    continue

                target_path = dest / member_clean
                target_path.parent.mkdir(parents=True, exist_ok=True)

                with zf.open(member) as src, open(target_path, "wb") as dst:
                    shutil.copyfileobj(src, dst)

                extracted.append(str(target_path))

    except zipfile.BadZipFile as e:
        return {"success": False, "error": f"Corrupted ZIP file: {e}", "extracted_files": [], "skipped": []}
    except Exception as e:
        return {"success": False, "error": str(e), "extracted_files": [], "skipped": []}

    return {
        "success": True,
        "error": None,
        "extracted_files": extracted,
        "skipped": skipped,
    }


def scan_zip_contents(extracted_files: List[str]) -> Dict[str, List[str]]:
    """
    Categorise extracted files into type buckets.

    Returns:
        {
            "csv":   [...],
            "image": [...],
            "audio": [...],
            "text":  [...],
            "other": [...],
        }
    """
    buckets: Dict[str, List[str]] = {
        "csv": [], "image": [], "audio": [], "text": [], "other": []
    }
    for fp in extracted_files:
        ext = Path(fp).suffix.lower()
        if ext in CSV_EXTS:
            buckets["csv"].append(fp)
        elif ext in IMAGE_EXTS:
            buckets["image"].append(fp)
        elif ext in AUDIO_EXTS:
            buckets["audio"].append(fp)
        elif ext in TEXT_EXTS:
            buckets["text"].append(fp)
        else:
            buckets["other"].append(fp)
    return buckets


def validate_zip_contents(zip_path: str) -> Dict[str, Any]:
    """
    Full pipeline: extract → scan → dispatch to existing validators → merge.

    Returns a ValidationResult-compatible dict that main.py can consume.
    """
    from validators.csv_validator   import validate_csv
    from validators.image_validator import validate_images
    from validators.audio_validator import validate_audio
    from validators.text_validator  import validate_text

    # Create a temporary extraction directory (will NOT overwrite upload)
    extract_dir = zip_path + "_extracted"

    extraction = extract_zip_safe(zip_path, extract_dir)

    if not extraction["success"]:
        from models.schemas import ValidationCheck, Issue, Severity
        return {
            "checks": [ValidationCheck(
                name="ZIP Extraction", status="fail",
                message=extraction["error"], severity=Severity.HIGH
            )],
            "issues": [Issue(
                title="ZIP Extraction Failed",
                description=extraction["error"],
                severity=Severity.HIGH
            )],
            "dashboard_data": {},
            "stats": {
                "total_files": 0,
                "missing_ratio": 0, "duplicate_ratio": 0,
                "corrupted_ratio": 0, "empty_ratio": 0,
                "format_issues": False, "class_imbalance": False, "missing_labels": False
            },
            "zip_info": extraction,
        }

    buckets = scan_zip_contents(extraction["extracted_files"])

    all_checks  = []
    all_issues  = []
    all_stats   = {}
    dashboard   = {}
    total_files = 0

    # ── Validate each bucket ─────────────────────────────────────────────────

    # CSV
    for csv_file in buckets["csv"]:
        r = validate_csv(csv_file)
        all_checks.extend(r["checks"])
        all_issues.extend(r["issues"])
        _merge_stats(all_stats, r.get("stats", {}))
        _merge_dashboard(dashboard, r.get("dashboard_data", {}))
        total_files += 1

    # Images — pass a temporary ZIP-like path using the directory
    if buckets["image"]:
        # Build a lightweight pseudo-zip for the image validator by passing
        # the first image (validator handles both single-file and ZIP paths)
        # Actually pass the extract_dir so image_validator can glob
        r = _validate_image_dir(extract_dir, buckets["image"])
        all_checks.extend(r["checks"])
        all_issues.extend(r["issues"])
        _merge_stats(all_stats, r.get("stats", {}))
        _merge_dashboard(dashboard, r.get("dashboard_data", {}))
        total_files += len(buckets["image"])

    # Audio — same approach
    if buckets["audio"]:
        r = _validate_audio_dir(extract_dir, buckets["audio"])
        all_checks.extend(r["checks"])
        all_issues.extend(r["issues"])
        _merge_stats(all_stats, r.get("stats", {}))
        _merge_dashboard(dashboard, r.get("dashboard_data", {}))
        total_files += len(buckets["audio"])

    # Text files
    for txt_file in buckets["text"]:
        r = validate_text(txt_file)
        all_checks.extend(r["checks"])
        all_issues.extend(r["issues"])
        _merge_stats(all_stats, r.get("stats", {}))
        _merge_dashboard(dashboard, r.get("dashboard_data", {}))
        total_files += 1

    # Skipped / unsupported files note
    if extraction["skipped"]:
        from models.schemas import ValidationCheck, Severity
        all_checks.append(ValidationCheck(
            name="Unsafe Paths",
            status="warning",
            message=f"{len(extraction['skipped'])} file(s) were skipped due to unsafe paths",
            severity=Severity.MEDIUM,
        ))

    if buckets["other"]:
        from models.schemas import ValidationCheck, Severity
        all_checks.append(ValidationCheck(
            name="Unsupported Files",
            status="warning",
            message=f"{len(buckets['other'])} unsupported file(s) in ZIP were ignored",
            severity=Severity.LOW,
        ))

    # Deduplicate checks by name
    seen_names = set()
    unique_checks = []
    for c in all_checks:
        if c.name not in seen_names:
            seen_names.add(c.name)
            unique_checks.append(c)

    all_stats["total_files"] = total_files
    all_stats.setdefault("missing_ratio", 0)
    all_stats.setdefault("duplicate_ratio", 0)
    all_stats.setdefault("corrupted_ratio", 0)
    all_stats.setdefault("empty_ratio", 0)
    all_stats.setdefault("format_issues", False)
    all_stats.setdefault("class_imbalance", False)
    all_stats.setdefault("missing_labels", False)

    # Format distribution: show what was in the ZIP
    fmt_dist = {}
    for k, files in buckets.items():
        if files and k != "other":
            fmt_dist[k.upper()] = len(files)
    if fmt_dist:
        dashboard["format_distribution"] = fmt_dist

    return {
        "checks":         unique_checks,
        "issues":         all_issues,
        "dashboard_data": dashboard,
        "stats":          all_stats,
        "zip_info":       {
            "buckets": {k: len(v) for k, v in buckets.items()},
            "skipped": extraction["skipped"],
            "extracted": len(extraction["extracted_files"]),
        },
    }


# ── Internal helpers ──────────────────────────────────────────────────────────

def _merge_stats(base: dict, new: dict):
    """Merge numeric stats by taking max ratios, OR for counts."""
    for key, val in new.items():
        if key not in base:
            base[key] = val
        elif isinstance(val, (int, float)) and isinstance(base[key], (int, float)):
            if key.endswith("_ratio"):
                base[key] = max(base[key], val)
            elif key.startswith("total_"):
                base[key] = base[key] + val
            else:
                base[key] = max(base[key], val)
        elif isinstance(val, bool):
            base[key] = base[key] or val


def _merge_dashboard(base: dict, new: dict):
    """Merge dashboard data dicts."""
    for key, val in new.items():
        if key not in base:
            base[key] = val
        elif isinstance(val, dict) and isinstance(base.get(key), dict):
            base[key].update(val)
        elif isinstance(val, list) and isinstance(base.get(key), list):
            base[key].extend(val)


def _validate_image_dir(extract_dir: str, image_files: List[str]) -> Dict[str, Any]:
    """
    Validate images from extracted directory.
    The image_validator expects either a direct image path or a ZIP path.
    We create a temporary ZIP from the extracted images so we can reuse it as-is.
    """
    import zipfile as zf_mod
    import tempfile

    tmp_zip = extract_dir + "_images_tmp.zip"
    try:
        with zf_mod.ZipFile(tmp_zip, "w") as zout:
            for img in image_files:
                zout.write(img, Path(img).name)
        from validators.image_validator import validate_images
        return validate_images(tmp_zip)
    finally:
        if os.path.exists(tmp_zip):
            os.remove(tmp_zip)


def _validate_audio_dir(extract_dir: str, audio_files: List[str]) -> Dict[str, Any]:
    """Validate audio files from extracted directory."""
    import zipfile as zf_mod

    tmp_zip = extract_dir + "_audio_tmp.zip"
    try:
        with zf_mod.ZipFile(tmp_zip, "w") as zout:
            for af in audio_files:
                zout.write(af, Path(af).name)
        from validators.audio_validator import validate_audio
        return validate_audio(tmp_zip)
    finally:
        if os.path.exists(tmp_zip):
            os.remove(tmp_zip)
