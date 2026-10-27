import os
import zipfile
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Tuple
from collections import defaultdict, Counter
from models.schemas import ValidationCheck, Issue, Severity

try:
    from PIL import Image
    import imagehash
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

SUPPORTED_FORMATS = {".jpg", ".jpeg", ".png", ".bmp", ".gif", ".webp", ".tiff"}


def _get_image_files(path: str) -> List[str]:
    """Collect all image files from path (file or directory or zip)."""
    files = []
    p = Path(path)
    if p.suffix.lower() == ".zip":
        extract_dir = p.parent / (p.stem + "_extracted")
        with zipfile.ZipFile(path, "r") as z:
            z.extractall(extract_dir)
        for f in extract_dir.rglob("*"):
            if f.is_file() and f.suffix.lower() in SUPPORTED_FORMATS:
                files.append(str(f))
    elif p.is_dir():
        for f in p.rglob("*"):
            if f.is_file() and f.suffix.lower() in SUPPORTED_FORMATS:
                files.append(str(f))
    elif p.suffix.lower() in SUPPORTED_FORMATS:
        files.append(str(p))
    return files


def validate_images(filepath: str) -> Dict[str, Any]:
    checks: List[ValidationCheck] = []
    issues: List[Issue] = []

    image_files = _get_image_files(filepath)
    total = len(image_files)

    if total == 0:
        return {
            "checks": [ValidationCheck(name="Image Files", status="fail",
                                       message="No image files found", severity=Severity.HIGH)],
            "issues": [Issue(title="No Images Found", description="The uploaded path contains no images",
                             severity=Severity.HIGH)],
            "dashboard_data": {},
            "stats": {"total_files": 0, "valid_files": 0, "corrupted_ratio": 1.0,
                      "duplicate_ratio": 1.0, "format_issues": True, "class_imbalance": False,
                      "empty_folder": True, "missing_labels": False}
        }

    # ── 1. Format Check ──────────────────────────────────────────────────
    format_counts = Counter(Path(f).suffix.lower() for f in image_files)
    unsupported = [f for f in image_files if Path(f).suffix.lower() not in SUPPORTED_FORMATS]
    if unsupported:
        checks.append(ValidationCheck(name="Supported Formats", status="fail",
                                      message=f"{len(unsupported)} files with unsupported formats",
                                      severity=Severity.MEDIUM, value=len(unsupported)))
        issues.append(Issue(title="Unsupported Formats", description=f"{len(unsupported)} images in unsupported format",
                            severity=Severity.MEDIUM, count=len(unsupported)))
    else:
        checks.append(ValidationCheck(name="Supported Formats", status="pass",
                                      message=f"All {total} images in supported formats"))

    # ── 2. Corrupted Images ───────────────────────────────────────────────
    corrupted = []
    valid_images = []
    dimensions = []
    hashes = []

    for f in image_files:
        if not PIL_AVAILABLE:
            valid_images.append(f)
            continue
        try:
            with Image.open(f) as img:
                img.verify()
            # Re-open for dimensions (verify closes the file)
            with Image.open(f) as img:
                dimensions.append(img.size)
                hashes.append(str(imagehash.phash(img)))
            valid_images.append(f)
        except Exception:
            corrupted.append(f)

    corrupted_ratio = len(corrupted) / max(total, 1)
    if corrupted:
        checks.append(ValidationCheck(name="Corrupted Images", status="fail",
                                      message=f"{len(corrupted)} corrupted image(s) found",
                                      severity=Severity.HIGH, value=len(corrupted)))
        issues.append(Issue(title="Corrupted Images", description=f"{len(corrupted)} images could not be opened",
                            severity=Severity.HIGH, count=len(corrupted)))
    else:
        checks.append(ValidationCheck(name="Corrupted Images", status="pass",
                                      message="No corrupted images found"))

    # ── 3. Duplicate Images ───────────────────────────────────────────────
    dup_count = 0
    if hashes:
        hash_counter = Counter(hashes)
        dup_count = sum(v - 1 for v in hash_counter.values() if v > 1)

    dup_ratio = dup_count / max(total, 1)
    if dup_count > 0:
        sev = Severity.HIGH if dup_ratio > 0.1 else Severity.MEDIUM
        checks.append(ValidationCheck(name="Duplicate Images", status="fail",
                                      message=f"{dup_count} duplicate image(s) detected (perceptual hash)",
                                      severity=sev, value=dup_count))
        issues.append(Issue(title="Duplicate Images", description=f"{dup_count} near-duplicate images found",
                            severity=sev, count=dup_count))
    else:
        checks.append(ValidationCheck(name="Duplicate Images", status="pass",
                                      message="No duplicate images found"))

    # ── 4. Resolution & Consistency ──────────────────────────────────────
    if dimensions:
        unique_dims = set(dimensions)
        if len(unique_dims) == 1:
            w, h = list(unique_dims)[0]
            checks.append(ValidationCheck(name="Image Dimensions", status="pass",
                                          message=f"All images are {w}×{h} — consistent"))
        else:
            checks.append(ValidationCheck(name="Image Dimensions", status="warning",
                                          message=f"{len(unique_dims)} different resolutions found",
                                          details=f"Sample sizes: {list(unique_dims)[:5]}",
                                          severity=Severity.MEDIUM, value=len(unique_dims)))
            issues.append(Issue(title="Inconsistent Dimensions", description=f"{len(unique_dims)} unique resolutions",
                                severity=Severity.MEDIUM, count=len(unique_dims)))

        # Minimum resolution check
        small_images = [(w, h) for w, h in dimensions if w < 32 or h < 32]
        if small_images:
            checks.append(ValidationCheck(name="Image Resolution", status="warning",
                                          message=f"{len(small_images)} image(s) below 32×32 pixels",
                                          severity=Severity.MEDIUM, value=len(small_images)))
            issues.append(Issue(title="Low Resolution Images", description=f"{len(small_images)} images are too small (<32px)",
                                severity=Severity.MEDIUM, count=len(small_images)))
        else:
            checks.append(ValidationCheck(name="Image Resolution", status="pass",
                                          message="All images meet minimum resolution (32×32)"))
    else:
        checks.append(ValidationCheck(name="Image Dimensions", status="warning",
                                      message="Could not read dimensions (PIL not available)"))

    # ── 5. Class Distribution (folder-based) ─────────────────────────────
    p = Path(filepath)
    class_dist = {}
    class_imbalance = False

    if p.suffix.lower() == ".zip":
        extract_dir = p.parent / (p.stem + "_extracted")
        base = extract_dir
    elif p.is_dir():
        base = p
    else:
        base = p.parent

    if base.is_dir():
        for sub in base.iterdir():
            if sub.is_dir():
                imgs = [f for f in sub.rglob("*") if f.suffix.lower() in SUPPORTED_FORMATS]
                if imgs:
                    class_dist[sub.name] = len(imgs)

    if class_dist:
        vals = list(class_dist.values())
        imbalance_ratio = max(vals) / max(min(vals), 1)
        if imbalance_ratio > 3:
            class_imbalance = True
            checks.append(ValidationCheck(name="Class Distribution", status="warning",
                                          message=f"Class imbalance ratio {imbalance_ratio:.1f}x",
                                          details=str(class_dist), severity=Severity.MEDIUM))
            issues.append(Issue(title="Class Imbalance", description=f"Image classes imbalanced by {imbalance_ratio:.1f}x",
                                severity=Severity.MEDIUM))
        else:
            checks.append(ValidationCheck(name="Class Distribution", status="pass",
                                          message=f"{len(class_dist)} classes, reasonably balanced"))
    else:
        checks.append(ValidationCheck(name="Class Distribution", status="warning",
                                      message="No class sub-folders detected", severity=Severity.LOW))

    # ── 6. Empty Folders ─────────────────────────────────────────────────
    empty_folder = total == 0
    if not empty_folder:
        checks.append(ValidationCheck(name="Empty Folders", status="pass",
                                      message="Dataset folder is not empty"))

    # ── Dashboard ─────────────────────────────────────────────────────────
    dashboard_data = {
        "total_files": total,
        "valid_files": len(valid_images),
        "corrupted_files": len(corrupted),
        "duplicate_files": dup_count,
        "format_distribution": {k: v for k, v in format_counts.items()},
        "class_distribution": class_dist,
        "unique_resolutions": len(set(dimensions)) if dimensions else 0,
    }

    stats = {
        "total_files": total,
        "valid_files": len(valid_images),
        "missing_ratio": 0.0,           # Not applicable for image datasets
        "empty_ratio": corrupted_ratio, # Treat corrupted as "empty" for quality scoring
        "corrupted_ratio": corrupted_ratio,
        "duplicate_ratio": dup_ratio,
        "format_issues": len(unsupported) > 0,
        "class_imbalance": class_imbalance,
        "empty_folder": empty_folder,
        "missing_labels": len(class_dist) == 0,
    }

    return {"checks": checks, "issues": issues, "dashboard_data": dashboard_data, "stats": stats}
