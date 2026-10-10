"""Central configuration for the SkillGap application.

All application paths, thresholds, model identifiers, column mappings,
and environment flags are centralized here. No magic numbers are scattered in the codebase.
"""

from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, List, Set
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


BASE_DIR = Path(__file__).resolve().parent


class Settings(BaseSettings):
    """Application settings loaded from environment variables and .env file."""

    model_config = SettingsConfigDict(
        env_file=str(BASE_DIR / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
    )

    # Project directories
    BASE_DIR: Path = BASE_DIR
    DATA_DIR: Path = BASE_DIR / "data"
    RAW_DATA_DIR: Path = BASE_DIR / "data" / "raw"
    PROCESSED_DATA_DIR: Path = BASE_DIR / "data" / "processed"
    CACHE_DIR: Path = BASE_DIR / "cache"
    TESTS_DIR: Path = BASE_DIR / "tests"
    FIXTURES_DIR: Path = BASE_DIR / "tests" / "fixtures"

    # Raw dataset paths in data/raw/
    RAW_ESCO_SKILLS_FILE: Path = BASE_DIR / "data" / "raw" / "esco_skills.csv"
    RAW_ONET_SKILLS_FILE: Path = BASE_DIR / "data" / "raw" / "onet_skills.csv"
    RAW_JOB_POSTINGS_FILE: Path = BASE_DIR / "data" / "raw" / "job_postings.csv"
    RAW_RESUMES_FILE: Path = BASE_DIR / "data" / "raw" / "resumes.csv"
    RAW_COURSES_FILE: Path = BASE_DIR / "data" / "raw" / "courses.csv"

    # Processed data outputs in data/processed/
    SKILLS_FILE: Path = BASE_DIR / "data" / "processed" / "skills.json"
    SKILL_EMBEDDINGS_FILE: Path = BASE_DIR / "data" / "processed" / "skill_embeddings.npy"
    SKILL_IDS_FILE: Path = BASE_DIR / "data" / "processed" / "skill_ids.json"
    TAXONOMY_FILE: Path = BASE_DIR / "data" / "processed" / "skills_taxonomy.parquet"
    ROLE_PROFILES_FILE: Path = BASE_DIR / "data" / "processed" / "role_profiles.json"
    ROLE_RULES_FILE: Path = BASE_DIR / "data" / "processed" / "role_rules.json"
    ROLE_EMBEDDINGS_FILE: Path = BASE_DIR / "data" / "processed" / "role_embeddings.npy"
    POSTING_SKILLS_CACHE_FILE: Path = BASE_DIR / "data" / "processed" / "posting_skills.parquet"
    COURSES_FILE: Path = BASE_DIR / "data" / "processed" / "courses.json"
    COURSE_EMBEDDINGS_FILE: Path = BASE_DIR / "data" / "processed" / "course_embeddings.npy"
    PREREQS_FILE: Path = BASE_DIR / "data" / "processed" / "prereqs.json"
    EMBEDDINGS_CACHE_FILE: Path = BASE_DIR / "cache" / "taxonomy_embeddings.parquet"

    # Role Profile Parameters
    MIN_SKILL_SHARE: float = Field(default=0.05, description="Minimum frequency share of postings for a skill to be retained")
    CORE_SKILL_SHARE_THRESHOLD: float = Field(default=0.50, description="Minimum share for core tier skills")
    COMMON_SKILL_SHARE_THRESHOLD: float = Field(default=0.20, description="Minimum share for common tier skills")
    MIN_POSTINGS_PER_ROLE: int = Field(default=5, description="Minimum postings required to maintain a role profile")
    ROLE_TITLE_SIMILARITY_CUTOFF: float = Field(default=0.65, description="Cosine similarity cutoff for embedding-based title matching")

    # Canonical Roles (15-25 standard industry roles)
    CANONICAL_ROLES: List[str] = [
        "Data Analyst",
        "Data Scientist",
        "ML Engineer",
        "Data Engineer",
        "Backend Developer",
        "Frontend Developer",
        "Full Stack Developer",
        "DevOps Engineer",
        "Cloud Engineer",
        "QA Engineer",
        "Product Manager",
        "Project Manager",
        "UI/UX Designer",
        "Business Analyst",
        "Mobile Developer",
        "Security Engineer",
        "Systems Administrator",
    ]

    # Seniority keywords for title stripping
    SENIORITY_KEYWORDS: Set[str] = {
        "senior",
        "sr",
        "junior",
        "jr",
        "lead",
        "principal",
        "staff",
        "intern",
        "internship",
        "entry level",
        "associate",
        "mid",
        "mid-level",
        "head of",
        "vp",
    }

    # Taxonomy curation sources
    SEED_SKILLS_FILE: Path = BASE_DIR / "data" / "raw" / "seed_skills.csv"
    SKILL_ALLOWLIST_FILE: Path = BASE_DIR / "data" / "raw" / "skill_allowlist.txt"

    # Taxonomy categories and validation
    SKILL_CATEGORIES: List[str] = [
        "programming",
        "data",
        "ml",
        "web",
        "cloud",
        "devops",
        "design",
        "business",
        "finance",
        "healthcare",
        "soft skills",
        "tools",
    ]

    AMBIGUOUS_SKILL_NAMES: Set[str] = {
        "c",
        "r",
        "go",
        "swift",
        "rust",
        "spark",
        "word",
        "excel",
        "git",
        "bash",
        "scala",
        "dart",
        "perl",
        "ruby",
        "net",
        "next",
        "vue",
        "rest",
        "sas",
        "spss",
        "jira",
        "ci",
        "cd",
        "reach",
        "shell",
        "signal",
        "pilot",
        "spring",
        "unity",
    }

    NON_SKILL_WORDS: Set[str] = {
        "work",
        "team",
        "working",
        "job",
        "career",
        "skill",
        "skills",
        "experience",
        "years",
        "responsible",
        "opportunity",
        "environment",
        "ability",
        "daily",
        "duties",
        "task",
        "tasks",
        "role",
        "roles",
        "project",
        "projects",
        "candidate",
        "candidates",
    }

    # Parsing & Upload limits
    MAX_UPLOAD_SIZE_MB: int = Field(default=5, description="Max uploaded file size in MB")
    ALLOWED_EXTENSIONS: Set[str] = {".pdf", ".docx", ".txt"}
    FRONTEND_URL: str = Field(default="http://localhost:3000", description="Frontend CORS origin")
    ANALYSIS_CACHE_TTL_SECONDS: int = Field(default=3600, description="TTL for in-memory analysis cache in seconds")

    # ML & Extraction models
    EMBEDDING_MODEL_NAME: str = "all-MiniLM-L6-v2"
    SPACY_MODEL_NAME: str = "en_core_web_sm"

    # Deterministic Matching & Scoring Thresholds
    SEM_MATCH_THRESHOLD: float = Field(
        default=0.75,
        description="Cosine similarity threshold for Stage B semantic skill extraction",
    )
    SEMANTIC_SIMILARITY_THRESHOLD: float = Field(
        default=0.72,
        description="Cosine similarity threshold to consider two skills semantically equivalent in gap matching",
    )
    PARTIAL_THRESHOLD: float = Field(
        default=0.80,
        description="Cosine similarity threshold for awarding partial credit between skills",
    )
    PARTIAL_CREDIT: float = Field(
        default=0.5,
        description="Fraction of weight credited for a partial/semantically similar skill match",
    )
    W_COVERAGE: float = Field(
        default=0.8,
        description="Weight of skill coverage score in final match score",
    )
    W_SEMANTIC: float = Field(
        default=0.2,
        description="Weight of role description semantic similarity in final match score",
    )
    SEMANTIC_MIN_COSINE: float = Field(
        default=0.15,
        description="Empirical min cosine similarity calibration for 0% semantic score",
    )
    SEMANTIC_MAX_COSINE: float = Field(
        default=0.85,
        description="Empirical max cosine similarity calibration for 100% semantic score",
    )
    EXACT_MATCH_SCORE: float = Field(default=1.0, description="Score weight for exact skill matches")
    FUZZY_MATCH_THRESHOLD: float = Field(
        default=0.85,
        description="Token similarity threshold for string fuzzy match",
    )
    CORE_SKILL_WEIGHT: float = Field(
        default=0.7,
        description="Weight given to required/core role skills in total match score",
    )
    SECONDARY_SKILL_WEIGHT: float = Field(
        default=0.3,
        description="Weight given to optional/secondary skills in total match score",
    )

    # Ambiguity Cue Words for extraction
    AMBIGUOUS_CUE_WORDS: Set[str] = {
        "programming",
        "language",
        "framework",
        "library",
        "experience",
        "proficient",
        "proficient in",
        "using",
        "developed",
        "built",
        "developer",
        "engineer",
        "code",
        "coding",
        "written in",
        "stack",
        "technologies",
        "tools",
        "script",
        "scripting",
        "database",
        "query",
        "queries",
    }

    # Recommendation Settings
    MAX_COURSE_RECOMMENDATIONS_PER_SKILL: int = 3
    MAX_TOTAL_RECOMMENDATIONS: int = 10
    DEFAULT_HOURS_PER_WEEK: int = 10
    W_SKILL_RELEVANCE: float = Field(default=0.50, description="Weight for skill-to-course embedding similarity")
    W_EXACT_SKILL_BONUS: float = Field(default=0.20, description="Bonus when course explicitly teaches the skill")
    W_RATING: float = Field(default=0.15, description="Weight for normalized course rating (0-1)")
    W_LEVEL_FIT: float = Field(default=0.15, description="Weight for student level alignment")
    W_DURATION_PENALTY: float = Field(default=0.10, description="Penalty weight for excessive course duration")

    # SLM (Phase 7 - Ollama)
    USE_SLM: bool = Field(default=False, description="Enable local Ollama SLM grounding")
    OLLAMA_BASE_URL: str = "http://localhost:11434"
    SLM_PRIMARY_MODEL: str = "qwen2.5:3b-instruct"
    SLM_FALLBACK_MODEL: str = "qwen2.5:1.5b-instruct"
    SLM_TIMEOUT_SECONDS: int = 30
    SLM_VALIDATE_THRESHOLD: float = Field(
        default=0.80,
        description="Cosine similarity threshold for validating SLM proposed skills against taxonomy",
    )
    SLM_CACHE_DIR: Path = BASE_DIR / "cache" / "slm"

    # Column mappings: Map user CSV column names to canonical names
    COLUMN_MAPPINGS: Dict[str, Dict[str, str]] = {
        "esco_skills": {
            "preferredLabel": "preferred_label",
            "preferred_label": "preferred_label",
            "altLabels": "alt_labels",
            "alt_labels": "alt_labels",
            "conceptUri": "skill_id",
            "skill_id": "skill_id",
            "skillType": "skill_type",
            "skill_type": "skill_type",
        },
        "job_postings": {
            "title": "title",
            "job_title": "title",
            "position": "title",
            "description": "description",
            "job_description": "description",
            "company": "company",
            "company_name": "company",
            "location": "location",
        },
        "resumes": {
            "resume_text": "resume_text",
            "Resume_str": "resume_text",
            "Resume": "resume_text",
            "text": "resume_text",
            "category": "category",
            "Category": "category",
            "label": "category",
        },
        "courses": {
            "title": "title",
            "course_title": "title",
            "Course Name": "title",
            "name": "title",
            "description": "description",
            "course_description": "description",
            "Course Description": "description",
            "rating": "rating",
            "Course Rating": "rating",
            "level": "level",
            "Difficulty Level": "level",
            "duration": "duration",
            "Duration": "duration",
            "url": "url",
            "Course URL": "url",
            "platform": "platform",
            "Platform": "platform",
        },
    }

    # Minimum required canonical columns for validation
    REQUIRED_COLUMNS: Dict[str, List[str]] = {
        "esco_skills": ["preferred_label"],
        "job_postings": ["title", "description"],
        "resumes": ["resume_text", "category"],
        "courses": ["title", "description"],
    }

    def ensure_directories(self) -> None:
        """Create required directories if they do not exist."""
        for path in (
            self.DATA_DIR,
            self.RAW_DATA_DIR,
            self.PROCESSED_DATA_DIR,
            self.CACHE_DIR,
            self.SLM_CACHE_DIR,
            self.FIXTURES_DIR,
        ):
            path.mkdir(parents=True, exist_ok=True)


# Global settings singleton
settings = Settings()
settings.ensure_directories()
