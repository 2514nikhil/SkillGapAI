# SkillGap - Job-Skill Gap Analyzer

SkillGap is a deterministic, explainable job-skill gap analysis system. A user uploads a resume (PDF/DOCX/TXT) and either selects a target role or pastes a job description. The system extracts their skills, compares them against what the role demands (derived from real job postings), computes an explainable match score, highlights skill gaps, and generates a structured learning plan with course recommendations.

## Project Structure

```text
skillgap/
  data/
    raw/                 # Raw datasets (job postings, course catalogs)
    processed/           # Processed taxonomy, profiles, and courses
  ml/
    __init__.py
    parse.py             # In-memory resume/document parsing (PDF, DOCX, TXT)
    taxonomy.py          # Skills taxonomy & hierarchy
    extract.py           # Skill extraction engine
    profiles.py          # Role profiles learned from job postings
    match.py             # Deterministic gap & match engine
    recommend.py         # Course recommendation engine
    explain.py           # Explainability breakdown & rationale
    slm.py               # Small Language Model integration (Phase 7)
  api/
    main.py              # FastAPI endpoints
    schemas.py           # Request & response schemas
  eval/
    labeled/             # Gold evaluation datasets
    extract_eval.py      # Skill extraction benchmark
    match_eval.py        # Match precision & recall benchmark
    rec_eval.py          # Recommendation relevance benchmark
  tests/
    fixtures/            # Minimal synthetic test resumes & files
    test_config.py       # Configuration tests
    test_parse.py        # Parser unit tests
  scripts/
    generate_fixtures.py # Generate test PDF/DOCX fixtures
  config.py              # Single source of truth configuration
  requirements.txt       # Core dependencies
```

## Setup & Installation

1. Create and activate a Python virtual environment:
```bash
python -m venv venv
.\venv\Scripts\activate   # Windows
source venv/bin/activate  # Linux/macOS
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Download the spaCy English model:
```bash
python -m spacy download en_core_web_sm
```

4. Run test suite:
```bash
pytest
```

## Optional: Local SLM Setup (Ollama)

SkillGap works 100% in pure deterministic mode without any LLM (`USE_SLM=false`). If you wish to enable optional SLM-powered extraction recovery and first-person learning plan narration:

1. **Install Ollama**:
   - Download and install Ollama from [ollama.com](https://ollama.com).

2. **Pull the Primary Model**:
   ```bash
   ollama pull qwen2.5:3b-instruct
   ```

3. **Low-Resource / Fast Fallback**:
   If your machine has limited VRAM or CPU power, pull the lightweight 1.5B parameter variant:
   ```bash
   ollama pull qwen2.5:1.5b-instruct
   ```

4. **Enable in Configuration**:
   In `.env` or environment variables, set:
   ```env
   USE_SLM=true
   SLM_PRIMARY_MODEL=qwen2.5:3b-instruct
   SLM_FALLBACK_MODEL=qwen2.5:1.5b-instruct
   OLLAMA_BASE_URL=http://localhost:11434
   ```
   If Ollama is ever stopped or unreachable, SkillGap automatically and gracefully falls back to deterministic rule-based execution.

