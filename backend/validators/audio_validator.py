import os
import zipfile
from pathlib import Path
from typing import List, Dict, Any
from models.schemas import ValidationCheck, Issue, Severity

try:
    import librosa
    import soundfile as sf
    import numpy as np
    AUDIO_AVAILABLE = True
except ImportError:
    AUDIO_AVAILABLE = False

SUPPORTED_FORMATS = {".wav", ".mp3", ".ogg", ".flac", ".aac", ".m4a"}
MIN_DURATION = 0.5   # seconds
MAX_DURATION = 300   # 5 minutes
EXPECTED_SR = 22050  # Hz


def _get_audio_files(path: str) -> List[str]:
    files = []
    p = Path(path)
    if p.suffix.lower() == ".zip":
        extract_dir = p.parent / (p.stem + "_audio_extracted")
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


def validate_audio(filepath: str) -> Dict[str, Any]:
    checks: List[ValidationCheck] = []
    issues: List[Issue] = []

    audio_files = _get_audio_files(filepath)
    total = len(audio_files)

    if total == 0:
        return {
            "checks": [ValidationCheck(name="Audio Files", status="fail",
                                       message="No audio files found", severity=Severity.HIGH)],
            "issues": [Issue(title="No Audio Found", description="No audio files in upload",
                             severity=Severity.HIGH)],
            "dashboard_data": {},
            "stats": {"total_files": 0, "valid_files": 0, "corrupted_ratio": 1.0,
                      "format_issues": True, "class_imbalance": False, "missing_labels": False}
        }

    # ── 1. Format Check ──────────────────────────────────────────────────
    from collections import Counter
    format_counts = Counter(Path(f).suffix.lower() for f in audio_files)
    unsupported = [f for f in audio_files if Path(f).suffix.lower() not in SUPPORTED_FORMATS]

    if unsupported:
        checks.append(ValidationCheck(name="Supported Formats", status="fail",
                                      message=f"{len(unsupported)} unsupported audio files",
                                      severity=Severity.MEDIUM, value=len(unsupported)))
        issues.append(Issue(title="Unsupported Audio Formats", description=f"{len(unsupported)} files in unsupported format",
                            severity=Severity.MEDIUM, count=len(unsupported)))
    else:
        checks.append(ValidationCheck(name="Supported Formats", status="pass",
                                      message=f"All {total} audio files in supported formats"))

    # ── 2. Corrupted / Load Check ─────────────────────────────────────────
    corrupted = []
    valid_files = []
    sample_rates = []
    durations = []
    channels_list = []
    silent_count = 0

    for f in audio_files:
        if not AUDIO_AVAILABLE:
            valid_files.append(f)
            continue
        try:
            y, sr = librosa.load(f, sr=None, mono=False)
            valid_files.append(f)
            sample_rates.append(sr)

            if y.ndim == 1:
                channels_list.append(1)
                dur = len(y) / sr
                rms = float(np.sqrt(np.mean(y**2)))
            else:
                channels_list.append(y.shape[0])
                dur = y.shape[1] / sr
                rms = float(np.sqrt(np.mean(y**2)))

            durations.append(dur)

            # Silent detection (RMS < threshold)
            if rms < 0.001:
                silent_count += 1

        except Exception:
            corrupted.append(f)

    corrupted_ratio = len(corrupted) / max(total, 1)

    if corrupted:
        checks.append(ValidationCheck(name="Corrupted Audio", status="fail",
                                      message=f"{len(corrupted)} corrupted audio file(s)",
                                      severity=Severity.HIGH, value=len(corrupted)))
        issues.append(Issue(title="Corrupted Audio Files", description=f"{len(corrupted)} files could not be loaded",
                            severity=Severity.HIGH, count=len(corrupted)))
    else:
        checks.append(ValidationCheck(name="Corrupted Audio", status="pass",
                                      message="No corrupted audio files"))

    # ── 3. Sample Rate ────────────────────────────────────────────────────
    if sample_rates:
        from collections import Counter as C2
        sr_counts = C2(sample_rates)
        sr_str = ", ".join(f"{k}Hz×{v}" for k, v in sr_counts.items())
        if len(sr_counts) == 1:
            checks.append(ValidationCheck(name="Sample Rate", status="pass",
                                          message=f"Consistent sample rate: {list(sr_counts.keys())[0]}Hz"))
        else:
            checks.append(ValidationCheck(name="Sample Rate", status="warning",
                                          message=f"Mixed sample rates: {sr_str}",
                                          severity=Severity.MEDIUM))
            issues.append(Issue(title="Mixed Sample Rates", description=f"Audio files have different sample rates: {sr_str}",
                                severity=Severity.MEDIUM))
    else:
        checks.append(ValidationCheck(name="Sample Rate", status="warning",
                                      message="Could not check sample rates (librosa unavailable)"))

    # ── 4. Audio Duration ─────────────────────────────────────────────────
    if durations:
        too_short = [d for d in durations if d < MIN_DURATION]
        too_long = [d for d in durations if d > MAX_DURATION]
        avg_dur = sum(durations) / len(durations)

        if too_short:
            checks.append(ValidationCheck(name="Audio Duration", status="warning",
                                          message=f"{len(too_short)} clip(s) shorter than {MIN_DURATION}s",
                                          severity=Severity.MEDIUM, value=len(too_short)))
            issues.append(Issue(title="Short Audio Clips", description=f"{len(too_short)} clips under {MIN_DURATION}s",
                                severity=Severity.MEDIUM, count=len(too_short)))
        elif too_long:
            checks.append(ValidationCheck(name="Audio Duration", status="warning",
                                          message=f"{len(too_long)} clip(s) exceed {MAX_DURATION}s",
                                          severity=Severity.LOW, value=len(too_long)))
        else:
            checks.append(ValidationCheck(name="Audio Duration", status="pass",
                                          message=f"All clips within acceptable range (avg {avg_dur:.1f}s)"))
    else:
        checks.append(ValidationCheck(name="Audio Duration", status="warning",
                                      message="Duration check skipped"))

    # ── 5. Silent Audio ───────────────────────────────────────────────────
    if silent_count > 0:
        checks.append(ValidationCheck(name="Silent Audio Detection", status="warning",
                                      message=f"{silent_count} silent audio file(s) detected",
                                      severity=Severity.MEDIUM, value=silent_count))
        issues.append(Issue(title="Silent Audio Files", description=f"{silent_count} files appear to be silent",
                            severity=Severity.MEDIUM, count=silent_count))
    else:
        checks.append(ValidationCheck(name="Silent Audio Detection", status="pass",
                                      message="No silent audio files detected"))

    # ── 6. Channel Info ───────────────────────────────────────────────────
    if channels_list:
        from collections import Counter as C3
        ch_counts = C3(channels_list)
        ch_str = ", ".join(f"{k}ch×{v}" for k, v in ch_counts.items())
        if len(ch_counts) == 1:
            checks.append(ValidationCheck(name="Channel Info", status="pass",
                                          message=f"Consistent channels: {list(ch_counts.keys())[0]}ch"))
        else:
            checks.append(ValidationCheck(name="Channel Info", status="warning",
                                          message=f"Mixed channels: {ch_str}",
                                          severity=Severity.LOW))
            issues.append(Issue(title="Mixed Audio Channels", description=f"Files have different channel counts: {ch_str}",
                                severity=Severity.LOW))
    else:
        checks.append(ValidationCheck(name="Channel Info", status="warning",
                                      message="Channel check skipped"))

    # ── Dashboard ─────────────────────────────────────────────────────────
    dashboard_data = {
        "total_files": total,
        "valid_files": len(valid_files),
        "corrupted_files": len(corrupted),
        "silent_files": silent_count,
        "format_distribution": {k: v for k, v in format_counts.items()},
        "avg_duration": round(sum(durations) / len(durations), 2) if durations else 0,
        "sample_rates": [{"rate": k, "count": v} for k, v in
                         Counter(sample_rates).items()] if sample_rates else [],
    }

    stats = {
        "total_files": total,
        "valid_files": len(valid_files),
        "missing_ratio": 0.0,           # Not applicable for audio datasets
        "empty_ratio": len(corrupted) / max(total, 1),
        "corrupted_ratio": corrupted_ratio,
        "duplicate_ratio": 0.0,         # Audio deduplication not checked
        "format_issues": len(unsupported) > 0,
        "class_imbalance": False,
        "missing_labels": False,
        "silent_ratio": silent_count / max(total, 1),
    }

    return {"checks": checks, "issues": issues, "dashboard_data": dashboard_data, "stats": stats}
