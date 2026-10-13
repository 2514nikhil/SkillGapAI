# SkillGap: Comprehensive Evaluation & Experimental Results

**Evaluation Date:** 2026-10-13 11:55:43  
**Python Version:** 3.12.10  
**Platform:** Windows 11 (AMD64)  

### Environment & Key Package Versions
| Package | Version |
|---|---|
| `spacy` | 3.8.16 |
| `sentence-transformers` | 6.1.0 |
| `torch` | 2.14.1 |
| `transformers` | 5.19.0 |
| `scikit-learn` | 1.9.1 |
| `fastapi` | 0.143.0 |
| `pydantic` | 2.14.0 |
| `pdfplumber` | 0.11.10 |
| `python-docx` | 1.2.0 |
| `pandas` | 3.0.6 |
| `numpy` | 2.5.3 |
| `uvicorn` | 0.54.0 |
| `httpx` | 0.28.1 |

---

## 1. Skill Extraction Accuracy & Ablation

Evaluated across ground-truth annotated engineering and data resumes and job descriptions (`eval/labeled/benchmark.json`).

| Mode | Precision (%) | Recall (%) | F1 (%) | TP | FP | FN | Avg Latency (s) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| baseline | 89.87 | 97.26 | 93.42 | 71 | 8 | 2 | 0.141 |
| hybrid | 90.00 | 98.63 | 94.12 | 72 | 8 | 1 | 1.186 |
| hybrid+slm | 90.00 | 98.63 | 94.12 | 72 | 8 | 1 | 0.058 |

### Performance by Document Type (Hybrid Mode)
| Document Type | Samples | Precision (%) | Recall (%) | F1 (%) | TP | FP | FN |
| --- | --- | --- | --- | --- | --- | --- | --- |
| resume | 3 | 90.57 | 100.00 | 95.05 | 48 | 5 | 0 |
| job_description | 2 | 88.89 | 96.00 | 92.31 | 24 | 3 | 1 |

### Per-Category Recall Breakdown (Hybrid Mode)
| Category | Ground Truth Count | Detected Count | Recall (%) |
| --- | --- | --- | --- |
| cloud | 2 | 2 | 100.00 |
| data | 11 | 10 | 90.91 |
| design | 1 | 1 | 100.00 |
| devops | 16 | 16 | 100.00 |
| ml | 9 | 9 | 100.00 |
| programming | 15 | 15 | 100.00 |
| tools | 7 | 7 | 100.00 |
| web | 12 | 12 | 100.00 |

### Extraction Error Analysis (Root Cause Breakdown)
| Error Type | Skill ID | Root Cause | Category | Document ID | Context |
| --- | --- | --- | --- | --- | --- |
| FP | microservices | phrasing | - | doc_01_backend_resume | TECHNICAL SKILLS Programming: Python, JavaScript, SQL, Bash  |
| FP | mentoring | phrasing | - | doc_02_mle_jd | Job Title: Machine Learning Engineer Company: AI Innovations |
| FP | artificial_intelligence | phrasing | - | doc_02_mle_jd | Job Title: Machine Learning Engineer Company: AI Innovations |
| FP | jest | phrasing | - | doc_03_frontend_resume | TypeScript, JavaScript, HTML5, CSS3, Sass Frameworks: React, |
| FP | seo | ambiguous alias | - | doc_03_frontend_resume | TypeScript, JavaScript, HTML5, CSS3, Sass Frameworks: React, |
| FP | team_leadership | phrasing | - | doc_04_data_analyst_jd | Position: Senior Data Analyst Department: Business Analytics |
| FP | amazon_eks | phrasing | - | doc_05_devops_resume | Kubernetes, Docker, Helm Infrastructure as Code: Terraform,  |
| FP | microservices | phrasing | - | doc_06_ambiguous_context_test | TECHNICAL SKILLS Programming Languages: C, Go, Rust, Swift,  |
| FN | data_warehousing | phrasing | data | doc_04_data_analyst_jd | - |

---

## 2. Role Matching Ablation Study

Evaluated on held-out test resumes (60/40 train/test split, random seed 42) mapped to empirical role demand profiles (`data/processed/role_profiles.json`).

| Method / Approach | Top-1 Accuracy (%) | Recall@3 (%) | MRR |
| --- | --- | --- | --- |
| (a) TF-IDF Cosine | 95.83 | 100.00 | 0.9792 |
| (b) Dense Embedding Cosine | 79.17 | 95.83 | 0.8713 |
| (c) Skill Coverage Only | 100.00 | 100.00 | 1.0000 |
| (d) Final Blended Score | 100.00 | 100.00 | 1.0000 |

---

## 3. Course Recommendation Ranking Relevance

Evaluated across 30 sampled missing skills with top-5 recommended learning courses scored by skill semantic relevance, taught-skill matching, rating, and duration penalty (`eval/results/rec_eval_samples.csv`).

| Recommendation Metric | Score |
| --- | --- |
| Precision@1 | 90.00% |
| Precision@3 | 44.44% |
| Precision@5 | 28.00% |
| MAP@5 | 0.9000 |
| Sampled Missing Skills | 30 |
| Total Recommendations Evaluated | 150 |

> **Critical Observation & Weakness Discussion:**  
> While **Precision@1** is high at **90.00%**, **Precision@5** drops to **28.00%**.  
> *Reason:* The raw course catalog contains 26 curated courses. For highly specific modern skills (e.g., `snowflake`, `mlflow`, `a_b_testing`), only 1 to 2 courses directly address the skill in the catalog. Ranks 3 through 5 therefore inevitably retrieve broader adjacent foundational courses (e.g., general Data Engineering or Python). Expanding the course catalog with more targeted modular content will immediately improve lower-rank precision.

---

## 4. Hyperparameter Sensitivity Sweeps

### A. Semantic Partial Credit Threshold (`PARTIAL_THRESHOLD`)
Measures how score and partial matches vary as the cosine threshold for 50% partial credit sweeps from 0.70 to 0.90.

| PARTIAL_THRESHOLD | Avg Coverage Score (%) | Avg Partial Matches |
| --- | --- | --- |
| 0.70 | 73.89 | 0.00 |
| 0.75 | 73.89 | 0.00 |
| 0.80 | 73.89 | 0.00 |
| 0.85 | 73.89 | 0.00 |
| 0.90 | 73.89 | 0.00 |

### B. Empirical Role Skill Share Cutoff (`MIN_SKILL_SHARE`)
Measures how the number of core skills in the role profile and candidate coverage vary with filtering threshold.

| MIN_SKILL_SHARE | Skills in Profile | Avg Coverage Score (%) |
| --- | --- | --- |
| 0.05 | 15 | 73.89 |
| 0.10 | 15 | 73.89 |
| 0.15 | 10 | 81.94 |
| 0.20 | 10 | 81.94 |
| 0.25 | 10 | 81.94 |

### C. Blended Weight Balance (`W_COVERAGE` vs `W_SEMANTIC`)
Evaluates the trade-off between deterministic skill coverage and dense embedding cosine similarity.

| W_COVERAGE | W_SEMANTIC | Avg Final Score (%) | Coverage (%) | Semantic (%) |
| --- | --- | --- | --- | --- |
| 0.50 | 0.50 | 66.14 | 73.89 | 58.39 |
| 0.60 | 0.40 | 67.69 | 73.89 | 58.39 |
| 0.70 | 0.30 | 69.24 | 73.89 | 58.39 |
| 0.80 | 0.20 | 70.79 | 73.89 | 58.39 |
| 0.90 | 0.10 | 72.34 | 73.89 | 58.39 |
| 1.00 | 0.00 | 73.89 | 73.89 | 58.39 |

---

## 5. Fairness & Robustness Sanity Checks

Verifies structural invariance and behavioral integrity across document representations.

| Sanity / Invariant Test | Observed Value | Threshold / Expectation | Status |
| --- | --- | --- | --- |
| Format Invariance (PDF vs DOCX) | Jaccard: 1.0000 (8/8 skills) | Jaccard >= 0.85 | PASS |
| Section Order Invariance | Max Delta: 0.0000 | Delta < 1e-4 | PASS |
| Score Monotonicity (Non-Degradation) | 0 violations across test skills | 0 violations | PASS |

---

## 6. ATS Resume Builder Verification & Benchmarks

### A. ATS PDF Parse & Skill Recovery Test
Rendered test resume fixtures across all 3 templates (`classic`, `compact`, `technical`) to PDF via headless engine, then extracted via `parse_pdf_stream` (`pdfplumber`) to evaluate text parseability and key term recovery.

| Fixture | Template | Sections Tested | Sections Recovered | Recovery (%) | Skills Tested | Skills Recovered | Skill Recovery (%) |
| --- | --- | --- | --- | --- | --- | --- | --- |
| Fixture 1 (Backend) | Classic | 4 | 4 | 100.0% | 12 | 12 | 100.0% |
| Fixture 1 (Backend) | Compact | 4 | 4 | 100.0% | 12 | 12 | 100.0% |
| Fixture 1 (Backend) | Technical | 4 | 4 | 100.0% | 12 | 12 | 100.0% |
| Fixture 2 (Data Science) | Classic | 4 | 4 | 100.0% | 10 | 10 | 100.0% |
| Fixture 2 (Data Science) | Compact | 4 | 4 | 100.0% | 10 | 10 | 100.0% |
| Fixture 2 (Data Science) | Technical | 4 | 4 | 100.0% | 10 | 9 | 90.0% |

### B. AI Writing Assistant Faithfulness & Hallucination Elimination
Evaluated on `eval/labeled/bullets.json` under `USE_SLM=false` (deterministic rule fallback) and local SLM inference. Every variant passes through the strict hallucination validator (`validate_bullet`).

| Metric | Observed Value | Target / Requirement | Status |
| --- | --- | --- | --- |
| Total Evaluation Bullets | 30 | N/A | Evaluated |
| Validator Pass Rate | 100.0% | 100.0% | Pass |
| Hallucinations Before Validator | 0.0% | Baseline | Observed |
| Hallucinations After Validator | 0.0% | 0.0% (Zero Hallucination) | Pass |
| Deterministic Fallback Coverage | 100.0% | 100.0% | Pass |

### C. Rendering & AI Component Latencies
Benchmarked across 5 iterations on standard engineering resume data.

| Component / Endpoint | Type | Avg Latency (ms) | SLA Target |
| --- | --- | --- | --- |
| Resume Render (HTML) | Deterministic Templating | 0.35 ms | < 50 ms |
| Resume Render (DOCX) | python-docx Export | 48.82 ms | < 200 ms |
| Resume Render (PDF) | WeasyPrint / Headless | 2401.24 ms | < 2500 ms |
| AI improve_bullet | Action-Verb Grounded Fallback | 38.10 ms | < 100 ms |
| AI draft_summary | Strict Verifiable Synthesis | 0.08 ms | < 100 ms |
| AI polish_project | Notes-to-Bullet Generator | 0.10 ms | < 100 ms |
| AI suggest_skills_from_text | Taxonomy Regex Matching | 157.59 ms | < 100 ms |
| AI tailor (Gap Analysis) | Empirical Profile Matching | 52.82 ms | < 250 ms |

### D. Deterministic Lint Rule Coverage
Comprehensive coverage of 22 ATS guidelines across critical errors, stylistic warnings, and impact tips (`ml/resume_lint.py`).

| Rule Category | Rule ID / Description | Level | Behavior |
| --- | --- | --- | --- |
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
*Report generated automatically by `scripts/make_report_tables.py`.*
