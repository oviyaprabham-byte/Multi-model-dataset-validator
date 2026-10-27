from typing import Dict, Any


def calculate_quality_score(stats: Dict[str, Any], dataset_type: str) -> Dict[str, Any]:
    """
    Weighted quality score formula.
    Returns score (0-100), badge, and dimension breakdown.
    """
    score = 100.0
    breakdown = {}

    # ── Missing values (weight: 20) ────────────────────────────────────
    missing_ratio = stats.get("missing_ratio", 0.0)
    missing_deduction = min(missing_ratio * 200, 20)  # max 20 pts off
    breakdown["missing_values"] = round(20 - missing_deduction, 1)
    score -= missing_deduction

    # ── Duplicate data (weight: 15) ────────────────────────────────────
    dup_ratio = stats.get("duplicate_ratio", 0.0)
    dup_deduction = min(dup_ratio * 150, 15)
    breakdown["duplicates"] = round(15 - dup_deduction, 1)
    score -= dup_deduction

    # ── Corrupted files (weight: 25) ──────────────────────────────────
    corrupted_ratio = stats.get("corrupted_ratio", 0.0)
    corrupt_deduction = min(corrupted_ratio * 250, 25)
    breakdown["corrupted"] = round(25 - corrupt_deduction, 1)
    score -= corrupt_deduction

    # ── Empty files/columns (weight: 15) ──────────────────────────────
    empty_ratio = stats.get("empty_ratio", stats.get("empty_col_ratio", 0.0))
    empty_deduction = min(empty_ratio * 150, 15)
    breakdown["empty"] = round(15 - empty_deduction, 1)
    score -= empty_deduction

    # ── Format issues (weight: 10) ────────────────────────────────────
    format_issues = stats.get("format_issues", False)
    format_deduction = 10 if format_issues else 0
    breakdown["format"] = round(10 - format_deduction, 1)
    score -= format_deduction

    # ── Class imbalance (weight: 10) ──────────────────────────────────
    class_imbalance = stats.get("class_imbalance", False)
    imbalance_deduction = 8 if class_imbalance else 0
    breakdown["class_imbalance"] = round(10 - imbalance_deduction, 1)
    score -= imbalance_deduction

    # ── Missing labels (weight: 5) ────────────────────────────────────
    missing_labels = stats.get("missing_labels", False)
    label_deduction = 5 if missing_labels else 0
    breakdown["missing_labels"] = round(5 - label_deduction, 1)
    score -= label_deduction

    # Clamp to [0, 100]
    score = max(0.0, min(100.0, score))

    # Badge
    if score >= 95:
        badge = "Excellent"
    elif score >= 80:
        badge = "Good"
    elif score >= 60:
        badge = "Average"
    else:
        badge = "Poor"

    return {
        "score": round(score, 1),
        "percentage": round(score, 1),
        "badge": badge,
        "breakdown": breakdown,
    }
