# SkillGap - Deterministic Job-Skill Gap Analyzer & Learning Roadmap

SkillGap is an open, deterministic, point-explainable career skill gap analysis system. A user uploads a resume (PDF, DOCX, or TXT) and either selects a target role or pastes a custom job description. The system extracts candidate skills against a verified taxonomy of over 430 skills, compares them against empirical labor market demand profiles derived from thousands of real job postings, calculates a transparent match score, highlights missing skills with exact point gains, and generates a prerequisite-grounded learning roadmap.

Developed and designed by **Nikhil Maghodiya** (`nikhilmaghodiya25@gmail.com`, [github.com/2514nikhil](https://github.com/2514nikhil)).

---

## 1. Description of the User Flow

SkillGap operates with a clear, linear flow:

1. **Upload & Role Selection (`/`)**:
   - The user selects their resume file (PDF or DOCX, max 5 MB).
   - The user selects one of 30 target roles across tech, business, and non-tech industries (e.g., *Backend Developer*, *Data Analyst*, *Executive Chef*, *Accountant*, *Fitness & Wellness Coach*, *Aviation Specialist*), OR pastes a specific job posting's text.
   - Pressing **"Analyze"** transitions the button state to *"Analyzing..."* with zero distracting animations.

2. **In-Memory Extraction & Parsing**:
   - The resume file is parsed directly in memory via `pdfplumber` or `python-docx`. The file is never stored on disk.
   - spaCy `PhraseMatcher` and normalized aliases scan the text for exact skills.
   - Dense vector embeddings (`all-MiniLM-L6-v2`) capture semantic skill equivalents without generative hallucinations.

3. **Empirical Matching & Scoring (`/result`)**:
   - The candidate's skills are compared against the target role's skill profile, where skills are tiered into *Core*, *Important*, and *Bonus* based on real market prevalence.
   - The match score is computed as: **70% empirical skill coverage + 30% semantic text alignment**.

4. **Transparent Skill Breakdown**:
   - **Skills we found in your resume**: Candidate skills with extracted evidence snippets. The candidate can remove incorrectly extracted items or search the taxonomy to add missed skills, then click **"Recalculate"**.
   - **Skills the role needs**: An itemized table with market demand progress bars, indicating whether the candidate has each skill (*Yes*, *Partly*, or *No*) and the exact points gained by learning it.

5. **Prerequisite-Ordered Learning Path**:
   - For every missing skill, the system recommends verified courses from a curated catalog.
   - Courses are topologically ordered so foundational prerequisites (e.g., Python before Machine Learning) are scheduled first.
   - If a single course covers multiple missing skills, the recommender automatically de-duplicates and prioritizes it.

6. **Interactive What-If Simulation**:
   - Candidates can tick checkboxes next to missing skills. An instant counterfactual API call simulates their updated score in real time (e.g., *"New score: 74% (+8 points)"*).

7. **Cross-Role Career Comparison**:
   - Clicking **"Load role comparisons"** evaluates the candidate's extracted skills against all alternative roles, highlighting adjacent career opportunities.

---

## 2. Using the Interface

SkillGap includes an accessible, hand-built guidance system:

- **Header Navigation**:
  - The site header is shared across all pages, linking to `/`, `/about`, and `/resume-builder`.
  - On the right, a dedicated square **`?`** button (28×28px, accessible via keyboard) opens a quick dropdown with two items:
    1. **"Show me around this page"**: Launches the interactive walkthrough for the active page.
    2. **"Help and troubleshooting"**: Navigates directly to [`/help`](http://localhost:3000/help).
- **First-Visit Auto Tour**:
  - When a user visits the upload page or result page for the first time, a step-by-step tour launches automatically.
  - The tour highlights the active element with a dark backdrop cutout, docks to the bottom edge on mobile screens (<600px), and supports `Escape` (skip), `ArrowRight` (next), and `ArrowLeft` (back).
  - Completing or skipping records a flag in `localStorage` (`skillgap_tour_upload_v1`, `skillgap_tour_result_v1`) so it does not re-appear unprompted. The `?` menu always allows re-playing the tour.
- **Inline Explanatory Hints (Amtrak-style)**:
  - Text links labeled *"What's this?"* or *"How is this calculated?"* appear beside the match score, the "Partly" match label, and the job description box. Clicking toggles a plain bordered explanation box directly inline without hover tooltips.

---

## 3. Resume Builder Feature (`/resume-builder`)

SkillGap includes an integrated, ATS-compliant Resume Builder that bridges skill gap analysis directly with job-ready resumes:

- **ATS-Optimized Templates**: Three single-column templates (`classic`, `compact`, `technical`) engineered with standard semantic headings, zero layout tables, no icons, and bundled open fonts (`Liberation Sans` and `Liberation Serif`).
- **Comprehensive Tech Catalog**: A taxonomy-aligned skill picker spanning 15 categories and 700+ industry skills with instant search, category filtering, and alias resolution.
- **Honest AI Writing Assistant**: Rewrites bullets using strong action verbs, synthesizes crisp executive summaries, and polishes project notes strictly using candidate-verified facts. **Zero invented facts**: The engine never fabricates employers, metrics, dates, or skills.
- **Deterministic Rule Fallback**: Functions 100% reliably without requiring Ollama (`USE_SLM=false`), providing deterministic verb-grounded improvements and fact-preserving summaries.
- **22-Point ATS Linter**: Deterministically catches critical errors (missing contact info, invalid dates, runaway bullets), style warnings (weak phrases, pronouns, bloated entries), and impact tips (missing numbers, repeated verbs).
- **Multi-Format ATS Export**: One-click downloads for PDF (WeasyPrint / Headless Chromium fallback), DOCX (native Word headings), Markdown, UTF-8 Text, and JSON.
- **Privacy & Statelessness**: Strictly zero server-side resume persistence. Content is stored exclusively in the candidate's browser `localStorage`, and in-memory server caches enforce strict LRU limits and 1-hour expiration.
- **Feature Flag**: Controlled by `NEXT_PUBLIC_RESUME_BUILDER_ENABLED=true` (enabled by default in `.env.example`). If disabled, `/resume-builder` reverts to an honest explanatory placeholder.

---

## 4. Data Sources & Placement

Raw data files and processed artifacts in `data/` are excluded from Git to comply with dataset distribution terms.

### Required Raw Datasets
To build or retrain SkillGap from scratch, download the following public datasets and place them into `data/raw/`:

| File Name | Dataset / Source | Required Columns | License / Terms |
|---|---|---|---|
| `data/raw/esco_skills.csv` | European Commission ESCO Skills Classification v1.2 | `preferred_label` (optional: `alt_labels`, `skill_id`) | Open Data Commons (ODC-BY) |
| `data/raw/job_postings.csv` | LinkedIn / Indeed Job Postings (Kaggle) | `title`, `description` (optional: `company`, `location`) | Kaggle Dataset License |
| `data/raw/resumes.csv` | Kaggle Resume Dataset (Sneha Bilgi / Updated Resume Dataset) | `resume_text`, `category` | CC BY-SA 4.0 |
| `data/raw/courses.csv` | Coursera / Udemy Course Dataset (Kaggle) | `title`, `description` (optional: `rating`, `duration`, `level`, `url`) | Public Domain / CC0 |

*Note: If your raw CSV files have different column headers, SkillGap automatically handles column aliasing via `COLUMN_MAPPINGS` in `config.py`.*

---

## 5. Setup & Installation

### Prerequisites
- Python 3.10+ (tested on Python 3.12.10)
- Node.js 18+ (tested on Node.js v22.17.0)

### 1. Backend Setup
```bash
# 1. Clone repository and navigate to root
cd skillgap

# 2. Create and activate a Python virtual environment
python -m venv venv
# Windows:
.\venv\Scripts\activate
# Linux/macOS:
source venv/bin/activate

# 3. Install Python dependencies
pip install -r requirements.txt

# 4. Download spaCy English language model
python -m spacy download en_core_web_sm

# 5. Build taxonomy, role profiles, and course indexes in one step
python scripts/build_all.py
```

### 2. Optional: Local SLM Setup (Ollama)
SkillGap functions **100% deterministically without Ollama** (`USE_SLM=false`). If you wish to enable optional SLM extraction recovery and narrative generation:
```bash
# 1. Install Ollama from ollama.com
# 2. Pull the primary model
ollama pull qwen2.5:3b-instruct

# 3. In .env set:
USE_SLM=true
OLLAMA_BASE_URL=http://localhost:11434
```

### 3. Launching the Backend Server
```bash
uvicorn api.main:app --host 127.0.0.1 --port 8000 --reload
```
The API documentation is available at [http://127.0.0.1:8000/docs](http://127.0.0.1:8000/docs).

### 4. Launching the Web Frontend
```bash
cd web
npm install
npm run dev
```
Open your browser at **[http://localhost:3000](http://localhost:3000)**.

---

## 6. Single Build Script (`scripts/build_all.py`)

A single command handles the entire data preparation pipeline with step resumption:

```bash
# Resume-friendly: Skips steps whose artifacts already exist in data/processed/
python scripts/build_all.py

# Force re-computation of all embeddings and profiles:
python scripts/build_all.py --force

# Build and immediately run the complete evaluation benchmark suite:
python scripts/build_all.py --with-eval
```

---

## 7. Running Tests & Evaluations

```bash
# Run backend pytest suite (77 tests)
pytest

# Run frontend unit tests (Tour logic, link integrity, feature flags)
cd web
npm test

# Run Next.js production build verification
npm run build
```

---

## 8. Environment Variables Reference

| Variable | Scope | Default Value | Description |
|---|---|---|---|
| `FRONTEND_URL` | Backend | `http://localhost:3000` | Allowed CORS origin for the FastAPI application. |
| `MAX_UPLOAD_SIZE_MB` | Backend | `5` | Maximum permissible resume file upload size in MB. |
| `USE_SLM` | Backend | `false` | Enable/disable optional local Ollama Small Language Model grounding. |
| `OLLAMA_BASE_URL` | Backend | `http://localhost:11434` | HTTP address of local or remote Ollama server. |
| `SLM_PRIMARY_MODEL` | Backend | `qwen2.5:3b-instruct` | Primary Ollama model tag for extraction recovery and narration. |
| `SLM_FALLBACK_MODEL` | Backend | `qwen2.5:1.5b-instruct` | Lightweight fallback model for resource-constrained environments. |
| `NEXT_PUBLIC_API_URL` | Frontend | `http://127.0.0.1:8000` | Target URL of the backend FastAPI REST API. |
| `NEXT_PUBLIC_RESUME_BUILDER_ENABLED` | Frontend | `true` | Feature flag to switch `/resume-builder` from placeholder to live workspace. |

---

## 9. Deployment & Cold Starts

### Docker Deployment (Hugging Face Spaces / Render)
A production-ready `Dockerfile` is provided in the repository root. It caches SentenceTransformer (`all-MiniLM-L6-v2`) and spaCy weights at image build time to ensure sub-second container startups without external network dependencies:
- **System Dependencies & ATS Fonts**: The container installs Linux font rendering packages (`libpango-1.0-0`, `libharfbuzz0b`, `libpangoft2-1.0-0`, `fonts-liberation`) to support native WeasyPrint PDF generation with ATS-safe open fonts.
- **Headless Browser Fallback**: If native WeasyPrint libraries are not detected in the host environment, the backend automatically fails over to headless Chromium/Edge for PDF rendering.

```bash
# Build Docker image
docker build -t skillgap-backend .

# Run container locally
docker run -p 8000:8000 -e PORT=8000 skillgap-backend
```

### Free Tier Hosting & SLM Architecture
On free cloud platforms (Render, Hugging Face Spaces free tier), backend compute instances sleep after inactivity. It takes approximately 45–60 seconds for the instance to spin up and load the ML models into memory. SkillGap's frontend intercepts network connection timeouts and surfaces a clear explanation:
> *"The server is waking up. Try again in a minute."*

**Recommended Free Tier Configuration (`USE_SLM=false`)**:
Because free cloud tiers lack dedicated GPUs and have tight memory limits (e.g. 512MB–1GB RAM), running an Ollama instance alongside the backend is not recommended in free environments. SkillGap defaults to `USE_SLM=false`. In this mode, the Resume Builder serves 100% of writing requests via deterministic rule engines (action verb selection, verifiable summary synthesis, note-to-bullet conversion), guaranteeing zero hallucination, sub-50ms latencies, and zero OOM crashes.

### Vercel (Frontend)
The Next.js App Router frontend can be deployed directly to Vercel by importing the repository, setting the root directory to `web/`, and defining `NEXT_PUBLIC_API_URL` to point to your live backend domain.

---

## 10. API Reference

### Skill Gap Analysis Endpoints
- `GET /health`: Checks system health, loaded models, and SLM reachability.
- `GET /roles`: Lists all 30 target roles with backing posting counts and core skill requirements.
- `GET /skills?q={query}`: Searches the 439-skill taxonomy by alias or canonical title.
- `POST /analyze` (Multipart Form): Accepts `file` (PDF/DOCX) + `role` (string) OR `jd` (text). Returns extracted skills, score breakdown, covered/partial/missing skills, and the topological learning path.
- `POST /whatif` (JSON): Computes counterfactual match scores when candidate acquires selected skills.
- `POST /compare` (JSON): Scores candidate skills across all available role profiles.

### Resume Builder & AI Endpoints
- `POST /resume/render`: Renders resume data to HTML, PDF, or DOCX formats with template selection.
- `POST /resume/export/json`: Exports validated resume schema as downloadable JSON.
- `POST /resume/export/txt`: Exports resume as formatted UTF-8 plain text with ASCII bullets.
- `POST /resume/export/md`: Exports resume as clean GitHub-flavored Markdown.
- `POST /resume/import` (Multipart Form): Parses uploaded PDF, DOCX, or TXT into structured resume JSON with `needs_review` annotations.
- `POST /resume/lint` (JSON): Runs 22 deterministic ATS rules across errors, warnings, and tips.
- `POST /resume/ai/improve-bullet` (JSON): Improves accomplishment bullets using strong action verbs with strict zero-hallucination validation.
- `POST /resume/ai/draft-summary` (JSON): Synthesizes verifiable 2-3 sentence executive summaries.
- `POST /resume/ai/polish-project` (JSON): Formats raw project notes into structured impact bullets.
- `POST /resume/ai/suggest-skills` (JSON): Scans resume text to detect unselected taxonomy skills.
- `POST /resume/ai/tailor` (JSON): Reuses the gap analyzer to compute role match scores and ranked missing skills.

---

## 11. Known Limitations & Ethics Note

### Limitations
- **Text-Only Extraction**: Image-only or scanned PDFs without embedded OCR text layers cannot be read.
- **No Soft Skill Guessing**: The system explicitly focuses on technical and verifiable domain skills. It does not attempt to psychometrically grade personality, culture fit, or soft skills.
- **Pre-Filtered Catalog**: Course recommendations depend on the coverage of the curated course index.

### Ethics Statement
- **Self-Improvement Only**: SkillGap is strictly an educational self-assessment tool. It is **not** designed or authorized for automated hiring filtering or employment screening decisions.
- **Zero Data Retention**: Uploaded resumes and parsed text are processed in volatile RAM and immediately discarded. No resumes, candidate names, or contact details are saved to databases or disk.

---

## 12. Experimental Evaluation Results

*The following empirical benchmarks were generated on **2026-10-10** using Python 3.12.10 on Windows 11 with spaCy 3.8.16, SentenceTransformers 6.1.0, and scikit-learn 1.9.1.*

### 1. Skill Extraction Accuracy & Ablation (`eval/labeled/benchmark.json`)

| Mode | Precision (%) | Recall (%) | F1 (%) | TP | FP | FN | Avg Latency (s) |
|---|---|---|---|---|---|---|---|
| Baseline (Dict-only) | 91.03 | 97.26 | 94.04 | 71 | 7 | 2 | 0.150 |
| **Hybrid (Dict + MiniLM)** | **91.14** | **98.63** | **94.74** | **72** | **7** | **1** | **1.476** |
| Hybrid + SLM Recovery | 91.14 | 98.63 | 94.74 | 72 | 7 | 1 | 0.051 |

#### Performance by Document Type (Hybrid Mode)
| Document Type | Samples | Precision (%) | Recall (%) | F1 (%) | TP | FP | FN |
|---|---|---|---|---|---|---|---|
| Resume | 3 | 92.31 | 100.00 | 96.00 | 48 | 4 | 0 |
| Job Description | 2 | 88.89 | 96.00 | 92.31 | 24 | 3 | 1 |

### 2. Role Matching Ablation Study (Held-Out Test Split)

| Method / Approach | Top-1 Accuracy (%) | Recall@3 (%) | MRR |
|---|---|---|---|
| (a) TF-IDF Cosine Baseline | 100.00 | 100.00 | 1.0000 |
| (b) Dense Embedding Cosine Only | 100.00 | 100.00 | 1.0000 |
| (c) Skill Coverage Only | 100.00 | 100.00 | 1.0000 |
| **(d) Final Blended Score (70/30)** | **100.00** | **100.00** | **1.0000** |

### 3. Course Recommendation Ranking Relevance (30 Sampled Skills)

| Recommendation Metric | Score |
|---|---|
| **Precision@1** | **90.00%** |
| **Precision@3** | **44.44%** |
| **Precision@5** | **28.00%** |
| **MAP@5** | **0.9000** |

> **Honest Discussion of Recommender Precision:**  
> Precision@1 is high (90%), ensuring the top-recommended course for any missing skill is relevant. Precision@5 drops to 28% because the catalog contains 52 curated courses; highly specialized skills (e.g., `snowflake`, `mlflow`) have only 1–2 direct courses in the catalog, forcing ranks 3–5 to surface broader foundational content.

### 4. Fairness & Robustness Sanity Checks

| Sanity / Invariant Test | Observed Metric | Threshold / Expectation | Status |
|---|---|---|---|
| Format Invariance (PDF vs DOCX) | Jaccard: 1.0000 (8/8 skills match) | Jaccard >= 0.85 | **PASS** |
| Section Order Invariance | Max Score Delta: 0.0000 | Delta < 1e-4 | **PASS** |
| Score Monotonicity (Non-Degradation) | 0 violations across test skills | 0 violations | **PASS** |

### 5. Resume Builder Verification & Benchmarks

#### A. ATS PDF Parse & Skill Recovery Test
Rendered test resume fixtures across all 3 templates (`classic`, `compact`, `technical`) to PDF via headless engine, then extracted via `parse_pdf_stream` (`pdfplumber`) to evaluate text parseability and key term recovery.

| Fixture | Template | Sections Tested | Sections Recovered | Recovery (%) | Skills Tested | Skills Recovered | Skill Recovery (%) |
|---|---|---|---|---|---|---|---|
| Fixture 1 (Backend) | Classic | 4 | 4 | 100.0% | 12 | 12 | 100.0% |
| Fixture 1 (Backend) | Compact | 4 | 4 | 100.0% | 12 | 12 | 100.0% |
| Fixture 1 (Backend) | Technical | 4 | 4 | 100.0% | 12 | 12 | 100.0% |
| Fixture 2 (Data Science) | Classic | 4 | 4 | 100.0% | 10 | 10 | 100.0% |
| Fixture 2 (Data Science) | Compact | 4 | 4 | 100.0% | 10 | 10 | 100.0% |
| Fixture 2 (Data Science) | Technical | 4 | 4 | 100.0% | 10 | 9 | 90.0% |

#### B. AI Writing Assistant Faithfulness & Hallucination Elimination
Evaluated on `eval/labeled/bullets.json` under `USE_SLM=false` (deterministic rule fallback) and local SLM inference. Every variant passes through the strict hallucination validator (`validate_bullet`).

| Metric | Observed Value | Target / Requirement | Status |
|---|---|---|---|
| Total Evaluation Bullets | 30 | N/A | Evaluated |
| Validator Pass Rate | 100.0% | 100.0% | **PASS** |
| Hallucinations Before Validator | 0.0% | Baseline | Observed |
| Hallucinations After Validator | 0.0% | 0.0% (Zero Hallucination) | **PASS** |
| Deterministic Fallback Coverage | 100.0% | 100.0% | **PASS** |

#### C. Rendering & AI Component Latencies
Benchmarked across 5 iterations on standard engineering resume data.

| Component / Endpoint | Type | Avg Latency (ms) | SLA Target |
|---|---|---|---|
| Resume Render (HTML) | Deterministic Templating | 0.35 ms | < 50 ms |
| Resume Render (DOCX) | python-docx Export | 48.82 ms | < 200 ms |
| Resume Render (PDF) | WeasyPrint / Headless | 2401.24 ms | < 2500 ms |
| AI improve_bullet | Action-Verb Grounded Fallback | 38.10 ms | < 100 ms |
| AI draft_summary | Strict Verifiable Synthesis | 0.08 ms | < 100 ms |
| AI polish_project | Notes-to-Bullet Generator | 0.10 ms | < 100 ms |
| AI suggest_skills_from_text | Taxonomy Regex Matching | 157.59 ms | < 200 ms |
| AI tailor (Gap Analysis) | Empirical Profile Matching | 52.82 ms | < 250 ms |

#### D. Deterministic Lint Rule Coverage
Comprehensive coverage of 22 ATS guidelines across critical errors, stylistic warnings, and impact tips (`ml/resume_lint.py`).

| Rule Category | Rule ID / Description | Level | Behavior |
|---|---|---|---|
| Basics | Missing Name | Error | Ensures resume includes candidate full name |
| Basics | Missing Email | Error | Ensures contact email is provided |
| Basics | Invalid Email Format | Error | Validates RFC compliant email address |
| Basics | Invalid Phone Format | Error | Validates standard numeric phone length |
| Dates | End Date Before Start Date | Error | Detects chronologically impossible dates |
| Formatting | Bullet Length Exceeds 300 chars | Error | Flags runaway narrative paragraphs |
| Experience | Empty Experience Required Fields | Error | Guarantees title, company, start date are present |
| Education | Empty Education Required Fields | Error | Guarantees degree, institution, start date are present |
| Projects | Empty Project Name | Error | Guarantees project title exists |
| Structure | Estimated Pages Exceeds 2 | Warning | Alerts when resume length exceeds 2 standard pages |
| Style | Weak Starting Phrase | Warning | Detects 'responsible for', 'worked on', 'helped with' |
| Style | First-Person Pronouns | Warning | Flags personal pronouns (I, me, my, we) in bullets |
| Dates | Inconsistent Date Formats | Warning | Flags mixed date formatting patterns |
| Experience | Entry with No Bullets | Warning | Highlights roles with no accomplishments listed |
| Skills | Duplicate Skill Entry | Warning | Detects duplicate skills across categories |
| Structure | Excessive Bullets (> 8 per entry) | Warning | Encourages concise role descriptions |
| Links | Non-Resume-Friendly Platform | Warning | Flags entertainment/social links (e.g. TikTok, Discord) |
| Impact | Bullet Without Metric or Outcome | Tip | Recommends adding numbers or measurable results |
| Summary | Summary Exceeds 4 Sentences | Tip | Encourages a crisp executive summary |
| Skills | Fewer Than 5 Total Skills | Tip | Recommends highlighting additional core competencies |
| Relevance | Skills Not Mentioned in Experience | Tip | Flags skills isolated in skills list |
| Style | Overused Starting Action Verb | Tip | Flags verbs repeated 3+ times across bullets |

---

## 13. License

SkillGap application source code is released under the **MIT License**. Third-party datasets (ESCO, Kaggle datasets) retain their respective original licenses.
