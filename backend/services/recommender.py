from typing import List, Dict, Any
from models.schemas import Issue, Recommendation, Severity


# Mapping of issue title keywords → recommendations
RECOMMENDATION_MAP = [
    {
        "keywords": ["missing values", "missing value"],
        "title": "Fill Missing Values",
        "description": "Use imputation strategies: mean/median for numerical columns, mode for categorical. Consider using sklearn's SimpleImputer or KNN Imputer.",
        "priority": Severity.HIGH,
    },
    {
        "keywords": ["duplicate rows", "duplicate content", "duplicate images", "duplicate"],
        "title": "Remove Duplicate Records",
        "description": "Drop duplicate rows/files to avoid data leakage and biased model training. Use df.drop_duplicates() for CSV, or hash-based deduplication for files.",
        "priority": Severity.HIGH,
    },
    {
        "keywords": ["corrupted images", "corrupted audio", "corrupted"],
        "title": "Remove Corrupted Files",
        "description": "Delete corrupted files and re-collect clean samples. Ensure all files can be opened and decoded before training.",
        "priority": Severity.HIGH,
    },
    {
        "keywords": ["empty columns", "empty files", "empty"],
        "title": "Remove Empty Columns / Files",
        "description": "Drop columns with 100% missing values. Remove empty files from the dataset. These add no value and may cause errors during training.",
        "priority": Severity.HIGH,
    },
    {
        "keywords": ["class imbalance"],
        "title": "Balance the Dataset",
        "description": "Apply oversampling (SMOTE, RandomOverSampler) for the minority class or undersample the majority class. Alternatively, use class_weight='balanced' in your model.",
        "priority": Severity.MEDIUM,
    },
    {
        "keywords": ["missing labels", "no class structure"],
        "title": "Add Missing Labels",
        "description": "Annotate unlabeled samples manually or using semi-supervised learning. Organize files into class sub-folders for image/text datasets.",
        "priority": Severity.MEDIUM,
    },
    {
        "keywords": ["inconsistent dimensions", "normalize image", "image dimension"],
        "title": "Normalize Image Sizes",
        "description": "Resize all images to a consistent resolution (e.g., 224×224). Use torchvision.transforms or tf.keras.preprocessing to apply uniform resizing.",
        "priority": Severity.MEDIUM,
    },
    {
        "keywords": ["unsupported formats", "unsupported audio formats", "convert"],
        "title": "Convert Unsupported Formats",
        "description": "Convert files to a supported format: PNG/JPEG for images, WAV/MP3 for audio, UTF-8 TXT for text. Use ffmpeg for audio/video, Pillow for images.",
        "priority": Severity.MEDIUM,
    },
    {
        "keywords": ["silent audio", "silent"],
        "title": "Remove Silent Audio Files",
        "description": "Silent clips carry no information and may harm model performance. Remove them or replace with valid recordings.",
        "priority": Severity.MEDIUM,
    },
    {
        "keywords": ["mixed sample rates", "sample rate"],
        "title": "Standardize Audio Sample Rate",
        "description": "Resample all audio files to a consistent sample rate (e.g., 22050 Hz or 44100 Hz) using librosa.resample() or ffmpeg.",
        "priority": Severity.MEDIUM,
    },
    {
        "keywords": ["mixed audio channels", "channels"],
        "title": "Normalize Audio Channels",
        "description": "Convert all audio files to mono or stereo consistently. Use librosa.to_mono() or ffmpeg's -ac flag.",
        "priority": Severity.LOW,
    },
    {
        "keywords": ["encoding issues", "encoding"],
        "title": "Fix Encoding Issues",
        "description": "Re-encode all text files to UTF-8 using Python's encode/decode or tools like iconv. Consistent encoding prevents training errors.",
        "priority": Severity.MEDIUM,
    },
    {
        "keywords": ["short content", "short audio"],
        "title": "Remove Very Short Samples",
        "description": "Remove files with insufficient content (< 5 words or < 0.5s audio) as they likely contain noise or errors.",
        "priority": Severity.LOW,
    },
    {
        "keywords": ["low resolution"],
        "title": "Replace Low-Resolution Images",
        "description": "Images below 32×32 pixels are unlikely to contain useful features. Replace them with higher-resolution versions or remove them.",
        "priority": Severity.MEDIUM,
    },
    {
        "keywords": ["invalid data types", "data type", "type mismatch"],
        "title": "Fix Data Type Inconsistencies",
        "description": "Cast columns to their correct data types using pd.to_numeric(), pd.to_datetime(), or .astype(). Incorrect types can cause model failures.",
        "priority": Severity.MEDIUM,
    },
    {
        "keywords": ["insufficient data", "too few rows"],
        "title": "Collect More Training Data",
        "description": "With fewer than 100 samples, the model may not generalize. Collect more data or apply data augmentation techniques.",
        "priority": Severity.MEDIUM,
    },
]


def generate_recommendations(issues: List[Issue]) -> List[Recommendation]:
    recommendations: List[Recommendation] = []
    seen_titles = set()

    # Sort issues by severity (high first)
    severity_order = {Severity.HIGH: 0, Severity.MEDIUM: 1, Severity.LOW: 2}
    sorted_issues = sorted(issues, key=lambda i: severity_order.get(i.severity, 3))

    for issue in sorted_issues:
        issue_lower = issue.title.lower()
        for rule in RECOMMENDATION_MAP:
            if any(kw in issue_lower for kw in rule["keywords"]):
                if rule["title"] not in seen_titles:
                    seen_titles.add(rule["title"])
                    recommendations.append(Recommendation(
                        title=rule["title"],
                        description=rule["description"],
                        priority=rule["priority"],
                    ))
                break

    # Always add a general recommendation if score is reasonable
    if not recommendations:
        recommendations.append(Recommendation(
            title="Dataset Looks Clean",
            description="Your dataset passed all key checks. Consider applying data augmentation to improve model robustness.",
            priority=Severity.LOW,
        ))

    return recommendations
