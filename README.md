# 🧠 DataValidator — ML Dataset Quality Suite

A full-stack web application for validating machine learning datasets across **CSV, Image, Audio, and Text** modalities. Upload your dataset, get an instant quality score, identify issues, and download professional PDF/Excel reports.

---

## ✨ Features

| Feature | Details |
|---|---|
| **Multi-modal Validation** | CSV, Images (JPG/PNG/ZIP), Audio (WAV/MP3/ZIP), Text (TXT/ZIP) |
| **Quality Score** | 0–100 score with Excellent / Good / Average / Poor badge |
| **20+ Checks** | Missing values, duplicates, corruption, class imbalance, encoding issues, and more |
| **Recommendations** | Actionable fix suggestions ranked by severity |
| **Training Readiness** | Single READY / NOT READY verdict with reasons |
| **Analytics Dashboard** | Recharts-powered pie, bar, and radial charts |
| **Report Export** | Professional PDF (ReportLab) and Excel (openpyxl) with color-coded tables |
| **Validation History** | Persistent history with search, restore, and delete |

---

## 🚀 Quick Start

### Option A — One-click (Windows)
```
Double-click start.bat
```
The script will automatically:
1. Create a Python virtual environment
2. Install all backend pip dependencies
3. Install all frontend npm dependencies
4. Launch both servers
5. Open the browser at `http://localhost:5173`

### Option B — Manual

**Backend:**
```bash
cd backend
python -m venv venv
venv\Scripts\activate        # Windows
# source venv/bin/activate   # macOS/Linux
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

**Frontend** (in a separate terminal):
```bash
cd frontend
npm install
npm run dev
```

Open → `http://localhost:5173`

---

## 🏗️ Project Structure

```
Dataset validator/
├── start.bat                  # One-click launcher (Windows)
│
├── backend/                   # FastAPI server
│   ├── main.py                # All API routes
│   ├── requirements.txt       # Python dependencies
│   ├── models/
│   │   └── schemas.py         # Pydantic models
│   ├── validators/
│   │   ├── csv_validator.py   # CSV / tabular validation
│   │   ├── image_validator.py # Image dataset validation
│   │   ├── audio_validator.py # Audio dataset validation
│   │   └── text_validator.py  # Text dataset validation
│   ├── services/
│   │   ├── quality_scorer.py  # Weighted quality score formula
│   │   ├── recommender.py     # Issue → recommendation mapping
│   │   └── report_generator.py# PDF + Excel export
│   ├── uploads/               # Temporary uploaded files
│   └── reports/               # Generated report files
│
└── frontend/                  # React + Vite app
    ├── src/
    │   ├── App.jsx
    │   ├── index.css           # Design system (dark mode, CSS vars)
    │   ├── components/
    │   │   ├── Layout/Sidebar.jsx
    │   │   └── ErrorBoundary.jsx
    │   ├── pages/
    │   │   ├── Upload.jsx      # Drag-and-drop upload + file info
    │   │   ├── Results.jsx     # Score gauge, checks table, issues
    │   │   ├── Dashboard.jsx   # Recharts analytics
    │   │   └── History.jsx     # Searchable history with restore
    │   ├── context/
    │   │   └── ValidationContext.jsx
    │   └── services/
    │       └── api.js          # Axios API client
    └── vite.config.js          # Proxy: /api → localhost:8000
```

---

## 🔌 API Reference

| Method | Endpoint | Description |
|---|---|---|
| `POST` | `/api/validate` | Upload and validate a dataset |
| `GET` | `/api/results/{id}` | Restore full result by session ID |
| `GET` | `/api/report/pdf/{id}` | Download PDF report |
| `GET` | `/api/report/excel/{id}` | Download Excel report |
| `GET` | `/api/history` | List validation history |
| `DELETE` | `/api/history/{id}` | Delete a history entry |
| `DELETE` | `/api/history` | Clear all history |

Interactive API docs: `http://localhost:8000/docs`

---

## 📦 Tech Stack

**Backend:** Python · FastAPI · Pandas · Pillow · librosa · ReportLab · openpyxl  
**Frontend:** React 19 · Vite · Recharts · Axios · react-hot-toast · lucide-react

---

## 📊 Quality Score Formula

| Dimension | Max Points |
|---|---|
| No corrupted files | 25 |
| No missing values | 20 |
| No duplicates | 15 |
| No empty columns/files | 15 |
| No format issues | 10 |
| No class imbalance | 10 |
| Labels present | 5 |
| **Total** | **100** |

Badges: **Excellent** (95–100) · **Good** (80–94) · **Average** (60–79) · **Poor** (< 60)
