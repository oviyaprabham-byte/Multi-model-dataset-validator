import pandas as pd
import numpy as np
from typing import List, Dict, Any
from models.schemas import ValidationCheck, Issue, Severity


def validate_csv(filepath: str) -> Dict[str, Any]:
    checks: List[ValidationCheck] = []
    issues: List[Issue] = []
    dashboard_data = {}

    try:
        df = pd.read_csv(filepath)
    except Exception as e:
        return {
            "checks": [ValidationCheck(name="File Load", status="fail", message=f"Cannot read CSV: {e}", severity=Severity.HIGH)],
            "issues": [Issue(title="File Read Error", description=str(e), severity=Severity.HIGH)],
            "dashboard_data": {},
            "stats": {"total_rows": 0, "total_cols": 0, "missing_ratio": 1.0, "duplicate_ratio": 1.0,
                      "empty_col_ratio": 1.0, "class_imbalance": True, "format_issues": True}
        }

    total_rows = len(df)
    total_cols = len(df.columns)

    # ── 1. Missing Values ──────────────────────────────────────────────────
    missing_count = int(df.isnull().sum().sum())
    missing_ratio = missing_count / max(total_rows * total_cols, 1)
    per_col_missing = df.isnull().sum().to_dict()
    missing_cols = {k: int(v) for k, v in per_col_missing.items() if v > 0}

    if missing_count == 0:
        checks.append(ValidationCheck(name="Missing Values", status="pass",
                                      message="No missing values found", value=0))
    elif missing_ratio < 0.05:
        checks.append(ValidationCheck(name="Missing Values", status="warning",
                                      message=f"{missing_count} missing values detected ({missing_ratio*100:.1f}%)",
                                      details=str(missing_cols), severity=Severity.LOW, value=missing_count))
        issues.append(Issue(title="Missing Values", description=f"{missing_count} missing values across {len(missing_cols)} column(s)",
                            severity=Severity.LOW, count=missing_count))
    else:
        checks.append(ValidationCheck(name="Missing Values", status="fail",
                                      message=f"{missing_count} missing values ({missing_ratio*100:.1f}%)",
                                      details=str(missing_cols), severity=Severity.HIGH, value=missing_count))
        issues.append(Issue(title="Missing Values", description=f"{missing_count} missing values across {len(missing_cols)} column(s)",
                            severity=Severity.HIGH, count=missing_count))

    # ── 2. Duplicate Rows ──────────────────────────────────────────────────
    dup_count = int(df.duplicated().sum())
    dup_ratio = dup_count / max(total_rows, 1)

    if dup_count == 0:
        checks.append(ValidationCheck(name="Duplicate Rows", status="pass",
                                      message="No duplicate rows found", value=0))
    else:
        sev = Severity.HIGH if dup_ratio > 0.1 else Severity.MEDIUM
        checks.append(ValidationCheck(name="Duplicate Rows", status="fail",
                                      message=f"{dup_count} duplicate rows found ({dup_ratio*100:.1f}%)",
                                      severity=sev, value=dup_count))
        issues.append(Issue(title="Duplicate Rows", description=f"{dup_count} duplicate rows detected",
                            severity=sev, count=dup_count))

    # ── 3. Empty Columns ──────────────────────────────────────────────────
    empty_cols = [c for c in df.columns if df[c].isnull().all()]
    empty_col_ratio = len(empty_cols) / max(total_cols, 1)

    if not empty_cols:
        checks.append(ValidationCheck(name="Empty Columns", status="pass",
                                      message="No empty columns found", value=0))
    else:
        checks.append(ValidationCheck(name="Empty Columns", status="fail",
                                      message=f"{len(empty_cols)} empty column(s): {', '.join(empty_cols)}",
                                      severity=Severity.HIGH, value=len(empty_cols)))
        issues.append(Issue(title="Empty Columns", description=f"Columns with no data: {', '.join(empty_cols)}",
                            severity=Severity.HIGH, count=len(empty_cols)))

    # ── 4. Data Types ─────────────────────────────────────────────────────
    dtype_issues = []
    for col in df.columns:
        # In pandas 3.x, string columns use StringDtype, not object
        col_dtype = df[col].dtype
        is_string_like = (
            col_dtype == object or
            pd.api.types.is_string_dtype(col_dtype) and not pd.api.types.is_numeric_dtype(col_dtype)
        )
        if is_string_like:
            # Check if numeric data stored as string
            numeric_try = pd.to_numeric(df[col], errors='coerce')
            if numeric_try.notna().mean() > 0.8:
                dtype_issues.append(col)

    if not dtype_issues:
        checks.append(ValidationCheck(name="Data Types", status="pass",
                                      message="Data types appear consistent"))
    else:
        checks.append(ValidationCheck(name="Data Types", status="warning",
                                      message=f"Possible type mismatch in: {', '.join(dtype_issues)}",
                                      severity=Severity.MEDIUM, value=len(dtype_issues)))
        issues.append(Issue(title="Invalid Data Types", description=f"Columns may have incorrect types: {', '.join(dtype_issues)}",
                            severity=Severity.MEDIUM, count=len(dtype_issues)))

    # ── 5. Target Column ─────────────────────────────────────────────────
    target_candidates = ['label', 'target', 'class', 'y', 'output', 'result', 'category']
    found_target = [c for c in df.columns if c.lower() in target_candidates]

    if found_target:
        checks.append(ValidationCheck(name="Target Column", status="pass",
                                      message=f"Target column found: {', '.join(found_target)}"))
    else:
        checks.append(ValidationCheck(name="Target Column", status="warning",
                                      message="No obvious target column detected (label/target/class/y)",
                                      severity=Severity.MEDIUM))
        issues.append(Issue(title="Missing Labels", description="No standard target/label column found",
                            severity=Severity.MEDIUM))

    # ── 6. Class Imbalance ────────────────────────────────────────────────
    class_imbalance = False
    class_dist = {}
    if found_target:
        target_col = found_target[0]
        vc = df[target_col].value_counts()
        class_dist = vc.to_dict()
        if len(vc) >= 2:
            imbalance_ratio = vc.iloc[0] / max(vc.iloc[-1], 1)
            if imbalance_ratio > 3:
                class_imbalance = True
                checks.append(ValidationCheck(name="Class Imbalance", status="warning",
                                              message=f"Class imbalance ratio: {imbalance_ratio:.1f}x",
                                              details=str({str(k): int(v) for k, v in vc.items()}),
                                              severity=Severity.MEDIUM))
                issues.append(Issue(title="Class Imbalance", description=f"Imbalance ratio {imbalance_ratio:.1f}x exceeds threshold",
                                    severity=Severity.MEDIUM))
            else:
                checks.append(ValidationCheck(name="Class Imbalance", status="pass",
                                              message=f"Classes are reasonably balanced (ratio {imbalance_ratio:.1f}x)"))
        else:
            checks.append(ValidationCheck(name="Class Imbalance", status="warning",
                                          message="Only one class found or insufficient data",
                                          severity=Severity.MEDIUM))
    else:
        checks.append(ValidationCheck(name="Class Imbalance", status="warning",
                                      message="Skipped — no target column identified",
                                      severity=Severity.LOW))

    # ── 7. Train/Test Split ───────────────────────────────────────────────
    min_split_rows = 100
    if total_rows >= min_split_rows:
        checks.append(ValidationCheck(name="Train/Test Split", status="pass",
                                      message=f"{total_rows} rows — sufficient for train/test split"))
    else:
        checks.append(ValidationCheck(name="Train/Test Split", status="warning",
                                      message=f"Only {total_rows} rows — may be insufficient for reliable split",
                                      severity=Severity.MEDIUM))
        issues.append(Issue(title="Insufficient Data", description=f"Dataset has only {total_rows} rows",
                            severity=Severity.MEDIUM, count=total_rows))

    # ── Dashboard data ────────────────────────────────────────────────────
    # Build column type counts manually (pandas 3.x groupby on mixed dtypes fails)
    col_types = {}
    for col in df.columns:
        dtype_str = str(df[col].dtype)
        col_types[dtype_str] = col_types.get(dtype_str, 0) + 1

    missing_per_col = [{"column": k, "missing": int(v)} for k, v in per_col_missing.items() if v > 0]

    dashboard_data = {
        "total_rows": total_rows,
        "total_cols": total_cols,
        "missing_per_column": missing_per_col,
        "class_distribution": {str(k): int(v) for k, v in class_dist.items()},
        "column_types": col_types,
        "duplicate_count": dup_count,
        "empty_col_count": len(empty_cols),
    }

    stats = {
        "total_rows": total_rows,
        "total_cols": total_cols,
        "missing_ratio": missing_ratio,
        "duplicate_ratio": dup_ratio,
        "empty_col_ratio": empty_col_ratio,
        "class_imbalance": class_imbalance,
        "format_issues": len(dtype_issues) > 0,
        "missing_labels": len(found_target) == 0,
    }

    return {"checks": checks, "issues": issues, "dashboard_data": dashboard_data, "stats": stats}
