"""Tests for central configuration module."""

from pathlib import Path
from config import Settings, settings


def test_config_defaults():
    """Verify default configuration values adhere to system rules."""
    assert settings.USE_SLM is False
    assert settings.MAX_UPLOAD_SIZE_MB > 0
    assert ".pdf" in settings.ALLOWED_EXTENSIONS
    assert ".docx" in settings.ALLOWED_EXTENSIONS
    assert ".txt" in settings.ALLOWED_EXTENSIONS
    assert 0.0 < settings.SEMANTIC_SIMILARITY_THRESHOLD <= 1.0
    assert 0.0 < settings.CORE_SKILL_WEIGHT <= 1.0
    assert 0.0 < settings.SECONDARY_SKILL_WEIGHT <= 1.0
    assert abs((settings.CORE_SKILL_WEIGHT + settings.SECONDARY_SKILL_WEIGHT) - 1.0) < 1e-5


def test_directory_structure_exists():
    """Ensure required application directories are created."""
    assert settings.DATA_DIR.is_dir()
    assert settings.RAW_DATA_DIR.is_dir()
    assert settings.PROCESSED_DATA_DIR.is_dir()
    assert settings.CACHE_DIR.is_dir()
    assert settings.FIXTURES_DIR.is_dir()


def test_column_mappings_and_required_columns_defined():
    """Verify column mappings and required columns dictionaries are configured."""
    for key in ("esco_skills", "job_postings", "resumes", "courses"):
        assert key in settings.COLUMN_MAPPINGS
        assert key in settings.REQUIRED_COLUMNS
        assert len(settings.REQUIRED_COLUMNS[key]) > 0


def test_custom_settings_override(tmp_path: Path):
    """Test that custom environment variables override defaults safely."""
    custom = Settings(
        BASE_DIR=tmp_path,
        USE_SLM=True,
        SEMANTIC_SIMILARITY_THRESHOLD=0.85,
    )
    assert custom.USE_SLM is True
    assert custom.SEMANTIC_SIMILARITY_THRESHOLD == 0.85
    assert custom.BASE_DIR == tmp_path
