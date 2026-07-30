# 🤖 AI Resume-to-Job Matching Agent

> Match a PDF or DOCX resume against public **Greenhouse** and **Lever** job postings using structured LLM extraction and semantic similarity.

---

## ✨ What It Does

1. **Upload** a PDF or DOCX resume
2. **Review and edit** a validated candidate profile
3. **Fetch** up to 100 live job postings from Greenhouse and Lever
4. **Rank** every normalized description using local sentence-transformer embeddings
5. **Display** the top matches with scores, skill gaps, optional LLM explanations, and application links

---

## 🗺️ Workflow

```
Upload Resume
      ↓
Extract and analyze resume (configured LLM provider)
      ↓
Create structured candidate profile
      ↓
Retrieve job descriptions (Greenhouse + Lever APIs)
      ↓
Normalize job descriptions and requirements
      ↓
Semantic comparison (sentence-transformers)
      ↓
Calculate match scores
      ↓
Rank and display top 10 jobs
```

---

## 🚀 Quick Start

### 1. Open the project
```bash
cd ai-job-matcher
```

### 2. Create a virtual environment
```bash
python -m venv venv
source venv/bin/activate        # macOS / Linux
# venv\Scripts\activate         # Windows
```

### 3. Install dependencies
```bash
pip install -r requirements.txt
```

### 4. Configure environment variables
```bash
cp .env.example .env
# Choose ollama, gemini, openai, azure, or groq and configure its settings
```

### 5. Run the app
```bash
streamlit run app.py
```

Open [http://localhost:8501](http://localhost:8501) in your browser.

---

## 📁 Project Structure

```
ai-job-matcher/
├── app.py                    # Streamlit entry point
├── config.py                 # Environment & settings loader
├── agents/
│   ├── resume_analyzer.py    # LLM agent: resume → CandidateProfile
│   ├── job_analyzer.py       # LLM agent: job text → requirements
│   └── match_explainer.py    # LLM agent: candidate + job → MatchResult
├── services/
│   ├── resume_parser.py      # PDF / DOCX text extraction
│   ├── job_search.py         # Orchestrates Greenhouse + Lever fetching
│   ├── matcher.py            # Semantic similarity ranking
│   └── embeddings.py         # sentence-transformers wrapper
├── job_sources/
│   ├── base.py               # Abstract BaseJobSource interface
│   ├── greenhouse.py         # Greenhouse Job Board API adapter
│   └── lever.py              # Lever Postings API adapter
├── models/
│   ├── candidate.py          # CandidateProfile Pydantic model
│   ├── job.py                # JobPosting Pydantic model
│   └── match.py              # MatchResult Pydantic model
├── prompts/
│   ├── resume_analysis.txt   # LLM prompt for resume extraction
│   ├── job_analysis.txt      # LLM prompt for job analysis
│   └── match_explanation.txt # LLM prompt for match explanation
├── data/
│   ├── companies.json        # Greenhouse / Lever company board IDs
│   └── sample_jobs.json      # Offline sample jobs for testing
├── tests/
│   ├── test_resume_parser.py
│   ├── test_job_parser.py
│   └── test_matcher.py
├── .env.example
├── .gitignore
├── requirements.txt
└── README.md
```

---

## 🛠️ Tech Stack

| Component | Technology |
|---|---|
| UI | Streamlit |
| LLM | Ollama, Gemini, OpenAI, Azure AI/OpenAI, or Groq |
| Resume parsing | PyMuPDF (PDF), python-docx (DOCX) |
| Semantic matching | sentence-transformers + scikit-learn |
| Data validation | Pydantic v2 |
| Database | SQLite via SQLAlchemy (planned persistence phase) |
| Job sources | Greenhouse Job Board API, Lever Postings API |
| Testing | pytest |

---

## 🔑 Environment Variables

| Variable | Required | Description |
|---|---|---|
| `LLM_PROVIDER` | No | `ollama` by default; also supports `gemini`, `openai`, `azure`, and `groq` |
| Provider API key | Cloud only | Key required by the selected cloud provider |
| `OPENAI_MODEL` | No | OpenAI default: `gpt-4o-mini` |
| `GREENHOUSE_API_KEY` | No | Only needed for private boards |
| `LEVER_API_KEY` | No | Only needed for Lever Data API |
| `EMBEDDING_MODEL` | No | Default: `all-MiniLM-L6-v2` |
| `MAX_JOBS_TO_FETCH` | No | Default: `100` |
| `TOP_MATCHES_TO_SHOW` | No | Default: `10` |

---

## 📋 Roadmap

- [x] **Phase 1** — Project scaffold and Streamlit home page
- [x] **Phase 2** — PDF/DOCX resume parsing and quality checks
- [x] **Phase 3** — Validated candidate profile schema
- [x] **Phase 4** — LLM resume analysis and editable human review
- [x] **Phase 5** — Normalized Greenhouse and Lever source adapters
- [x] **Matching workflow** — Live search, semantic ranking, skill gaps, and optional explanations
- [ ] **Phase 6** — SQLite caching, history, LangGraph orchestration

---

## 🧪 Running Tests

```bash
pytest tests/ -v
```

---

## 📄 License

MIT
