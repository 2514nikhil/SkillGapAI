# SkillGap: Comprehensive Evaluation & Experimental Results

**Evaluation Date:** 2026-10-10 22:02:56  
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
| baseline | 91.03 | 97.26 | 94.04 | 71 | 7 | 2 | 0.150 |
| hybrid | 91.14 | 98.63 | 94.74 | 72 | 7 | 1 | 1.476 |
| hybrid+slm | 91.14 | 98.63 | 94.74 | 72 | 7 | 1 | 0.051 |

### Performance by Document Type (Hybrid Mode)
| Document Type | Samples | Precision (%) | Recall (%) | F1 (%) | TP | FP | FN |
| --- | --- | --- | --- | --- | --- | --- | --- |
| resume | 3 | 92.31 | 100.00 | 96.00 | 48 | 4 | 0 |
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
| (a) TF-IDF Cosine | 100.00 | 100.00 | 1.0000 |
| (b) Dense Embedding Cosine | 100.00 | 100.00 | 1.0000 |
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
| 0.50 | 0.50 | 85.40 | 73.89 | 96.91 |
| 0.60 | 0.40 | 83.10 | 73.89 | 96.91 |
| 0.70 | 0.30 | 80.80 | 73.89 | 96.91 |
| 0.80 | 0.20 | 78.50 | 73.89 | 96.91 |
| 0.90 | 0.10 | 76.19 | 73.89 | 96.91 |
| 1.00 | 0.00 | 73.89 | 73.89 | 96.91 |

---

## 5. Fairness & Robustness Sanity Checks

Verifies structural invariance and behavioral integrity across document representations.

| Sanity / Invariant Test | Observed Value | Threshold / Expectation | Status |
| --- | --- | --- | --- |
| Format Invariance (PDF vs DOCX) | Jaccard: 1.0000 (8/8 skills) | Jaccard >= 0.85 | PASS |
| Section Order Invariance | Max Delta: 0.0000 | Delta < 1e-4 | PASS |
| Score Monotonicity (Non-Degradation) | 0 violations across test skills | 0 violations | PASS |

---
*Report generated automatically by `scripts/make_report_tables.py`.*
