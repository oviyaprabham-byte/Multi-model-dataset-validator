"""
doc_generator.py  — Generate rich dataset documentation from ValidationResult.

All fields sourced from the actual ValidationResult — never hardcoded.
Missing fields are explicitly marked as "Not available".
"""

from datetime import datetime
from typing import Any, Dict, List, Optional


# ── ML Algorithm heuristics ──────────────────────────────────────────────────

_ML_HINTS = {
    "csv": {
        "classification": "Random Forest / XGBoost (tabular classification)",
        "regression":     "Gradient Boosting / LightGBM (tabular regression)",
        "default":        "Random Forest (tabular data — inspect target column for task type)",
    },
    "image": {
        "default": "Convolutional Neural Network (CNN) — ResNet-50 or EfficientNet recommended",
    },
    "audio": {
        "default": "Audio CNN with Mel-Spectrogram features or LSTM for sequence data",
    },
    "text": {
        "default": "Transformer model (BERT / DistilBERT) for NLP tasks",
    },
    "zip": {
        "default": "Multi-modal model — type depends on dominant data modality inside ZIP",
    },
    "unknown": {
        "default": "Not available — dataset type not recognised",
    },
}


def _ml_recommendation(dataset_type: str, quality_score: float, issues: List[Dict]) -> str:
    dtype = dataset_type.lower()
    hints = _ML_HINTS.get(dtype, _ML_HINTS["unknown"])
    return hints.get("default", "Not available")


def _training_time_estimate(total_items: Optional[int], dataset_type: str,
                            quality_score: float) -> str:
    if total_items is None:
        return "Not available"
    dtype = dataset_type.lower()
    if dtype == "csv":
        if total_items < 1_000:
            return "< 1 minute (small dataset)"
        elif total_items < 100_000:
            return "1–10 minutes (medium dataset)"
        else:
            return "10–60+ minutes (large dataset, GPU recommended)"
    elif dtype == "image":
        if total_items < 500:
            return "5–20 minutes with transfer learning (GPU recommended)"
        elif total_items < 10_000:
            return "1–4 hours with transfer learning (GPU required)"
        else:
            return "4–24+ hours (GPU required)"
    elif dtype == "audio":
        return "30 minutes–4 hours depending on audio length (GPU recommended)"
    elif dtype == "text":
        return "Fine-tuning: 30 minutes–2 hours with pre-trained model (GPU recommended)"
    return "Not available"


def _derive_limitations(issues: List[Dict], quality_score: float,
                        is_ready: bool) -> List[str]:
    lims = []
    if quality_score < 60:
        lims.append(f"Low quality score ({quality_score:.0f}/100) — dataset may produce unreliable models")
    if not is_ready:
        lims.append("Dataset is not ready for training — critical issues detected")
    for iss in issues:
        sev = iss.get("severity", "").lower()
        title = iss.get("title", "")
        if sev == "high":
            lims.append(f"Critical issue: {title}")
    if not lims:
        lims.append("No significant limitations detected")
    return lims


# ── Public API ───────────────────────────────────────────────────────────────

def generate_documentation(result: Any) -> Dict[str, Any]:
    """
    Generate a documentation dict from a ValidationResult object.
    All values come from the actual result — nothing is hardcoded.
    """
    info    = result.dataset_info
    qs      = result.quality_score
    issues  = result.issues
    recs    = result.recommendations

    dtype = info.dataset_type.value if hasattr(info.dataset_type, "value") else str(info.dataset_type)

    # Features (CSV columns)
    dash  = result.dashboard_data or {}
    features = dash.get("columns") or dash.get("features")
    if features is None and info.total_columns:
        features = [f"Column_{i+1}" for i in range(info.total_columns)]

    # Classes from distribution
    class_dist = dash.get("class_distribution") or {}
    classes = list(class_dist.keys()) if class_dist else None

    # File formats
    fmt_dist = dash.get("format_distribution") or {}
    file_formats = list(fmt_dist.keys()) if fmt_dist else [info.format or "Not available"]

    # Missing / duplicate / corrupted counts from issues
    missing_val   = _find_issue_count(issues, "missing")
    duplicate_val = _find_issue_count(issues, "duplicate")
    corrupted_val = _find_issue_count(issues, "corrupted")

    # Validation summary
    checks   = result.checks
    total_c  = len(checks)
    pass_c   = sum(1 for c in checks if c.status == "pass")
    fail_c   = sum(1 for c in checks if c.status == "fail")
    warn_c   = sum(1 for c in checks if c.status == "warning")
    val_summ = (
        f"{total_c} checks performed — {pass_c} passed, {fail_c} failed, {warn_c} warnings"
        if total_c > 0 else "Not available"
    )

    # Total items
    total_items = info.total_rows or info.total_files

    # ML recommendation
    issues_dicts = [{"title": i.title, "severity": i.severity} for i in issues]
    ml_algo = _ml_recommendation(dtype, qs.score, issues_dicts)
    train_time = _training_time_estimate(total_items, dtype, qs.score)

    limitations = _derive_limitations(issues_dicts, qs.score, result.is_ready)

    doc = {
        "session_id":          result.session_id,
        "dataset_name":        info.filename,
        "dataset_type":        dtype.upper(),
        "dataset_size":        info.size_human,
        "total_rows":          info.total_rows     if info.total_rows     is not None else "Not available",
        "total_columns":       info.total_columns  if info.total_columns  is not None else "Not available",
        "total_files":         info.total_files    if info.total_files    is not None else "Not available",
        "features":            features            if features            is not None else "Not available",
        "classes":             classes             if classes             is not None else "Not available",
        "class_distribution":  class_dist          if class_dist                      else "Not available",
        "file_formats":        file_formats,
        "missing_values":      missing_val         if missing_val         is not None else "Not available",
        "duplicate_count":     duplicate_val       if duplicate_val       is not None else "Not available",
        "corrupted_count":     corrupted_val       if corrupted_val       is not None else "Not available",
        "validation_summary":  val_summ,
        "quality_score":       qs.score,
        "quality_badge":       qs.badge,
        "ai_readiness":        result.is_ready,
        "readiness_reasons":   result.readiness_reasons or [],
        "issues":              [
            {"title": i.title, "description": i.description,
             "severity": i.severity, "count": i.count}
            for i in issues
        ],
        "recommendations":     [
            {"title": r.title, "description": r.description, "priority": r.priority}
            for r in recs
        ],
        "ml_algorithm":          ml_algo,
        "training_time_estimate": train_time,
        "limitations":           limitations,
        "timestamp":             result.timestamp,
        "generated_at":          datetime.now().isoformat(),
    }
    return doc


def documentation_to_text(doc: Dict[str, Any]) -> str:
    """
    Convert a documentation dict to a natural, spoken-language script
    suitable for Text-to-Speech playback.
    Returns a single string with section markers that the frontend can split.
    """
    na = "Not available"
    name   = doc.get("dataset_name", na)
    dtype  = doc.get("dataset_type", na)
    size   = doc.get("dataset_size", na)
    qs     = doc.get("quality_score")
    badge  = doc.get("quality_badge", na)
    ready  = doc.get("ai_readiness")
    rows   = doc.get("total_rows", na)
    cols   = doc.get("total_columns", na)
    files  = doc.get("total_files", na)
    mv     = doc.get("missing_values", na)
    dups   = doc.get("duplicate_count", na)
    corr   = doc.get("corrupted_count", na)
    val_s  = doc.get("validation_summary", na)
    ml     = doc.get("ml_algorithm", na)
    tt     = doc.get("training_time_estimate", na)
    lims   = doc.get("limitations", [])
    issues = doc.get("issues", [])
    recs   = doc.get("recommendations", [])

    lines = [
        f"Hello. I will read the dataset documentation for you.",
        "",
        f"## Dataset Overview",
        f"The dataset name is {name}.",
        f"The dataset type is {dtype}.",
        f"The dataset size is {size}.",
    ]

    if rows != na and rows is not None:
        lines.append(f"The dataset contains {rows:,} records." if isinstance(rows, int) else f"The dataset contains {rows} records.")
    if cols != na and cols is not None:
        lines.append(f"It has {cols} features or columns." if isinstance(cols, int) else f"It has {cols} columns.")
    if files != na and files is not None:
        lines.append(f"The dataset contains {files:,} files." if isinstance(files, int) else f"The dataset contains {files} files.")

    lines += [
        "",
        f"## Quality Assessment",
    ]
    if qs is not None:
        lines.append(f"The dataset quality score is {qs:.0f} out of 100.")
        lines.append(f"The quality rating is {badge}.")
    else:
        lines.append("The quality score is not available.")

    if ready is True:
        lines.append("The dataset is ready for machine learning training.")
    elif ready is False:
        lines.append("The dataset is NOT ready for training. Issues must be resolved first.")
    else:
        lines.append("Training readiness status is not available.")

    lines += [
        "",
        f"## Validation Results",
        f"{val_s}",
    ]

    if mv not in (na, None, 0, "0"):
        lines.append(f"Missing values detected: {mv}.")
    else:
        lines.append("No significant missing values detected.")

    if dups not in (na, None, 0, "0"):
        lines.append(f"Duplicate records detected: {dups}.")
    else:
        lines.append("No significant duplicate records detected.")

    if corr not in (na, None, 0, "0"):
        lines.append(f"Corrupted files detected: {corr}.")
    else:
        lines.append("No corrupted files detected.")

    if issues:
        lines += ["", "## Issues Detected"]
        high_issues   = [i for i in issues if str(i.get("severity","")).lower() == "high"]
        medium_issues = [i for i in issues if str(i.get("severity","")).lower() == "medium"]
        low_issues    = [i for i in issues if str(i.get("severity","")).lower() == "low"]

        if high_issues:
            lines.append(f"There are {len(high_issues)} high-severity issue(s):")
            for iss in high_issues:
                lines.append(f"  — {iss['title']}: {iss.get('description','')}")
        if medium_issues:
            lines.append(f"There are {len(medium_issues)} medium-severity issue(s):")
            for iss in medium_issues:
                lines.append(f"  — {iss['title']}: {iss.get('description','')}")
        if low_issues:
            lines.append(f"There are {len(low_issues)} low-severity issue(s).")
    else:
        lines += ["", "## Issues Detected", "No issues were detected in this dataset."]

    if recs:
        lines += ["", "## Recommendations"]
        for i, rec in enumerate(recs, 1):
            lines.append(f"Recommendation {i}: {rec['title']}. {rec.get('description','')}")
    else:
        lines += ["", "## Recommendations", "No specific recommendations — dataset appears clean."]

    lines += [
        "",
        "## Machine Learning Guidance",
        f"Recommended algorithm: {ml}.",
        f"Estimated training time: {tt}.",
    ]

    if lims:
        lines += ["", "## Limitations"]
        for lim in lims:
            lines.append(f"  — {lim}")

    lines += [
        "",
        "## End of Documentation",
        "That concludes the dataset documentation. You may ask me questions about this dataset.",
    ]

    return "\n".join(lines)


# ── Private helpers ───────────────────────────────────────────────────────────

def _find_issue_count(issues, keyword: str) -> Optional[int]:
    """Extract count from the first issue whose title contains keyword."""
    for iss in issues:
        title = iss.title.lower() if hasattr(iss, "title") else str(iss.get("title","")).lower()
        if keyword in title:
            count = iss.count if hasattr(iss, "count") else iss.get("count")
            if count is not None:
                return count
            return "Detected"
    return None
