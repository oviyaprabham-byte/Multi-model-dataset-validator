from pydantic import BaseModel
from typing import List, Optional, Dict, Any
from enum import Enum


class DatasetType(str, Enum):
    CSV = "csv"
    IMAGE = "image"
    AUDIO = "audio"
    TEXT = "text"
    ZIP = "zip"
    UNKNOWN = "unknown"


class Severity(str, Enum):
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"


class ValidationCheck(BaseModel):
    name: str
    status: str  # "pass" | "fail" | "warning"
    message: str
    details: Optional[str] = None
    severity: Optional[Severity] = None
    value: Optional[Any] = None


class Issue(BaseModel):
    title: str
    description: str
    severity: Severity
    count: Optional[int] = None


class Recommendation(BaseModel):
    title: str
    description: str
    priority: Severity


class QualityScore(BaseModel):
    score: float
    percentage: float
    badge: str  # "Excellent" | "Good" | "Average" | "Poor"
    breakdown: Dict[str, float]


class DatasetInfo(BaseModel):
    filename: str
    size_bytes: int
    size_human: str
    dataset_type: DatasetType
    total_files: Optional[int] = None
    total_rows: Optional[int] = None
    total_columns: Optional[int] = None
    format: Optional[str] = None


class ValidationResult(BaseModel):
    session_id: str
    dataset_info: DatasetInfo
    checks: List[ValidationCheck]
    issues: List[Issue]
    recommendations: List[Recommendation]
    quality_score: QualityScore
    is_ready: bool
    readiness_reasons: List[str]
    dashboard_data: Dict[str, Any]
    timestamp: str


class HistoryEntry(BaseModel):
    session_id: str
    filename: str
    dataset_type: DatasetType
    quality_score: float
    badge: str
    is_ready: bool
    timestamp: str


class Documentation(BaseModel):
    session_id: str
    dataset_name: str
    dataset_type: str
    dataset_size: str
    total_rows: Optional[Any] = None
    total_columns: Optional[Any] = None
    total_files: Optional[Any] = None
    features: Optional[List[str]] = None
    classes: Optional[List[str]] = None
    class_distribution: Optional[Dict[str, Any]] = None
    file_formats: Optional[List[str]] = None
    missing_values: Optional[Any] = None
    duplicate_count: Optional[Any] = None
    corrupted_count: Optional[Any] = None
    validation_summary: Optional[str] = None
    quality_score: Optional[float] = None
    quality_badge: Optional[str] = None
    ai_readiness: Optional[bool] = None
    readiness_reasons: Optional[List[str]] = None
    issues: Optional[List[Dict[str, Any]]] = None
    recommendations: Optional[List[Dict[str, Any]]] = None
    ml_algorithm: Optional[str] = None
    training_time_estimate: Optional[str] = None
    limitations: Optional[List[str]] = None
    timestamp: str
    generated_at: str


class ChatMessage(BaseModel):
    session_id: str
    role: str  # "user" | "assistant"
    content: str
    timestamp: str
