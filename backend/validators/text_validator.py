import os
import zipfile
import hashlib
from pathlib import Path
from typing import List, Dict, Any
from collections import Counter
from models.schemas import ValidationCheck, Issue, Severity

try:
    import chardet
    CHARDET_AVAILABLE = True
except ImportError:
    CHARDET_AVAILABLE = False


def _get_text_files(path: str) -> List[str]:
    files = []
    p = Path(path)
    if p.suffix.lower() == ".zip":
        extract_dir = p.parent / (p.stem + "_text_extracted")
        with zipfile.ZipFile(path, "r") as z:
            z.extractall(extract_dir)
        for f in extract_dir.rglob("*.txt"):
            files.append(str(f))
    elif p.is_dir():
        for f in p.rglob("*.txt"):
            files.append(str(f))
    elif p.suffix.lower() in {".txt", ".csv", ".tsv", ".json", ".jsonl"}:
        files.append(str(p))
    return files


def validate_text(filepath: str) -> Dict[str, Any]:
    checks: List[ValidationCheck] = []
    issues: List[Issue] = []

    text_files = _get_text_files(filepath)
    total = len(text_files)

    if total == 0:
        return {
            "checks": [ValidationCheck(name="Text Files", status="fail",
                                       message="No text files found", severity=Severity.HIGH)],
            "issues": [Issue(title="No Text Files", description="No .txt files found in upload",
                             severity=Severity.HIGH)],
            "dashboard_data": {},
            "stats": {"total_files": 0, "valid_files": 0, "empty_ratio": 1.0,
                      "duplicate_ratio": 0.0, "class_imbalance": False, "missing_labels": True,
                      "encoding_issues": False}
        }

    # ── 1. Empty Files ────────────────────────────────────────────────────
    empty_files = []
    valid_files = []
    contents = []

    for f in text_files:
        try:
            size = os.path.getsize(f)
            if size == 0:
                empty_files.append(f)
            else:
                valid_files.append(f)
                with open(f, "rb") as fh:
                    raw = fh.read()
                contents.append((f, raw))
        except Exception:
            empty_files.append(f)

    empty_ratio = len(empty_files) / max(total, 1)

    if empty_files:
        sev = Severity.HIGH if empty_ratio > 0.2 else Severity.MEDIUM
        checks.append(ValidationCheck(name="Empty Files", status="fail",
                                      message=f"{len(empty_files)} empty file(s) found",
                                      severity=sev, value=len(empty_files)))
        issues.append(Issue(title="Empty Files", description=f"{len(empty_files)} text files are empty",
                            severity=sev, count=len(empty_files)))
    else:
        checks.append(ValidationCheck(name="Empty Files", status="pass",
                                      message="No empty text files"))

    # ── 2. Encoding Validation ────────────────────────────────────────────
    encoding_issues = []
    for f, raw in contents:
        if CHARDET_AVAILABLE:
            result = chardet.detect(raw)
            enc = result.get("encoding", "utf-8") or "utf-8"
            confidence = result.get("confidence", 0)
            if confidence < 0.7 or enc.lower() not in {"utf-8", "ascii", "utf-8-sig", "iso-8859-1", "latin-1"}:
                encoding_issues.append(f)
        else:
            try:
                raw.decode("utf-8")
            except UnicodeDecodeError:
                encoding_issues.append(f)

    if encoding_issues:
        checks.append(ValidationCheck(name="Encoding Validation", status="warning",
                                      message=f"{len(encoding_issues)} file(s) with encoding issues",
                                      severity=Severity.MEDIUM, value=len(encoding_issues)))
        issues.append(Issue(title="Encoding Issues", description=f"{len(encoding_issues)} files may have encoding problems",
                            severity=Severity.MEDIUM, count=len(encoding_issues)))
    else:
        checks.append(ValidationCheck(name="Encoding Validation", status="pass",
                                      message="All files use standard encoding"))

    # ── 3. Duplicate Content ──────────────────────────────────────────────
    content_hashes = []
    for f, raw in contents:
        h = hashlib.md5(raw.strip()).hexdigest()
        content_hashes.append(h)

    hash_counts = Counter(content_hashes)
    dup_count = sum(v - 1 for v in hash_counts.values() if v > 1)
    dup_ratio = dup_count / max(len(contents), 1)

    if dup_count > 0:
        sev = Severity.HIGH if dup_ratio > 0.2 else Severity.LOW
        checks.append(ValidationCheck(name="Duplicate Content", status="fail",
                                      message=f"{dup_count} duplicate file(s) detected",
                                      severity=sev, value=dup_count))
        issues.append(Issue(title="Duplicate Content", description=f"{dup_count} files with identical content",
                            severity=sev, count=dup_count))
    else:
        checks.append(ValidationCheck(name="Duplicate Content", status="pass",
                                      message="No duplicate content found"))

    # ── 4. Missing Labels (folder-based class detection) ─────────────────
    p = Path(filepath)
    class_dist = {}
    class_imbalance = False

    if p.suffix.lower() == ".zip":
        base = p.parent / (p.stem + "_text_extracted")
    elif p.is_dir():
        base = p
    else:
        base = p.parent

    if base.is_dir():
        for sub in base.iterdir():
            if sub.is_dir():
                txts = list(sub.rglob("*.txt"))
                if txts:
                    class_dist[sub.name] = len(txts)

    if not class_dist and total >= 1:
        # Check if files themselves contain label-like names
        # Try parsing as label:text format
        labeled = 0
        for f, raw in contents[:min(20, len(contents))]:
            try:
                text = raw.decode("utf-8", errors="ignore")
                for line in text.splitlines():
                    if "\t" in line or line.startswith(("+", "-", "0", "1")):
                        labeled += 1
                        break
            except Exception:
                pass
        if labeled == 0:
            checks.append(ValidationCheck(name="Missing Labels", status="warning",
                                          message="No class structure or labels detected",
                                          severity=Severity.MEDIUM))
            issues.append(Issue(title="Missing Labels", description="Files do not appear to have class labels",
                                severity=Severity.MEDIUM))
            missing_labels = True
        else:
            checks.append(ValidationCheck(name="Missing Labels", status="pass",
                                          message="Files appear to contain labeled data"))
            missing_labels = False
    else:
        missing_labels = len(class_dist) == 0
        if class_dist:
            vals = list(class_dist.values())
            imbalance_ratio = max(vals) / max(min(vals), 1)
            if imbalance_ratio > 3:
                class_imbalance = True
                checks.append(ValidationCheck(name="Class Imbalance", status="warning",
                                              message=f"Class imbalance ratio {imbalance_ratio:.1f}x",
                                              details=str(class_dist), severity=Severity.MEDIUM))
                issues.append(Issue(title="Class Imbalance", description=f"Text classes imbalanced {imbalance_ratio:.1f}x",
                                    severity=Severity.MEDIUM))
            else:
                checks.append(ValidationCheck(name="Class Imbalance", status="pass",
                                              message=f"{len(class_dist)} classes reasonably balanced"))
        else:
            checks.append(ValidationCheck(name="Class Distribution", status="warning",
                                          message="Could not determine class structure",
                                          severity=Severity.LOW))

    # ── 5. Word Count / Content Length ───────────────────────────────────
    word_counts = []
    for f, raw in contents:
        try:
            text = raw.decode("utf-8", errors="ignore")
            wc = len(text.split())
            word_counts.append(wc)
        except Exception:
            word_counts.append(0)

    if word_counts:
        avg_words = sum(word_counts) / len(word_counts)
        very_short = sum(1 for w in word_counts if w < 5)
        if very_short > len(word_counts) * 0.2:
            checks.append(ValidationCheck(name="Content Length", status="warning",
                                          message=f"{very_short} file(s) with very short content (<5 words)",
                                          severity=Severity.LOW, value=very_short))
            issues.append(Issue(title="Short Content", description=f"{very_short} files have fewer than 5 words",
                                severity=Severity.LOW, count=very_short))
        else:
            checks.append(ValidationCheck(name="Content Length", status="pass",
                                          message=f"Average content length: {avg_words:.0f} words"))

    # ── Dashboard ─────────────────────────────────────────────────────────
    dashboard_data = {
        "total_files": total,
        "valid_files": len(valid_files),
        "empty_files": len(empty_files),
        "duplicate_files": dup_count,
        "encoding_issues": len(encoding_issues),
        "class_distribution": class_dist,
        "avg_word_count": round(sum(word_counts) / max(len(word_counts), 1)),
    }

    stats = {
        "total_files": total,
        "valid_files": len(valid_files),
        "missing_ratio": 0.0,           # Text files don't have column-level missing values
        "empty_ratio": empty_ratio,
        "corrupted_ratio": 0.0,         # Unreadable files counted as empty, not corrupted
        "duplicate_ratio": dup_ratio,
        "format_issues": len(encoding_issues) > 0,
        "class_imbalance": class_imbalance,
        "missing_labels": missing_labels,
        "encoding_issues": len(encoding_issues) > 0,
    }

    return {"checks": checks, "issues": issues, "dashboard_data": dashboard_data, "stats": stats}
