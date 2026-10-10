"""Unit tests for ml/data_io.py data loading and schema validation."""

from pathlib import Path
import pandas as pd
import pytest

from ml.data_io import (
    DatasetNotFoundError,
    EmptyDatasetError,
    SchemaValidationError,
    clean_text_cell,
    load_and_validate_csv,
    load_courses,
    load_esco_skills,
    load_job_postings,
    load_resumes,
)


def test_clean_text_cell():
    """Verify whitespace normalization and NA handling on individual cells."""
    assert clean_text_cell("  hello   world  \n ") == "hello world"
    assert clean_text_cell(None) == ""
    assert clean_text_cell(float("nan")) == ""
    assert clean_text_cell(123) == "123"


def test_load_and_validate_csv_success(tmp_path: Path):
    """Verify loading, deduplication, whitespace cleaning, and column mapping."""
    csv_file = tmp_path / "sample_postings.csv"
    data = (
        "job_title,job_description,company_name\n"
        "Python Engineer,  Develop REST APIs with FastAPI  ,  Acme Corp  \n"
        "Python Engineer,  Develop REST APIs with FastAPI  ,  Acme Corp  \n"  # Duplicate
        "Data Analyst,,DataCorp\n"  # Empty description (required column)
        "ML Engineer,Build NLP models,AI Lab\n"
    )
    csv_file.write_text(data, encoding="utf-8")

    df = load_and_validate_csv(csv_file, dataset_name="job_postings")

    # Canonical columns expected
    assert "title" in df.columns
    assert "description" in df.columns
    assert "company" in df.columns

    # 4 rows originally -> 1 duplicate dropped, 1 empty description dropped -> 2 valid rows
    assert len(df) == 2
    assert df.iloc[0]["title"] == "Python Engineer"
    assert df.iloc[0]["description"] == "Develop REST APIs with FastAPI"
    assert df.iloc[0]["company"] == "Acme Corp"


def test_missing_file_raises(tmp_path: Path):
    """Verify DatasetNotFoundError when target file does not exist."""
    missing_file = tmp_path / "nonexistent.csv"
    with pytest.raises(DatasetNotFoundError) as exc_info:
        load_and_validate_csv(missing_file, dataset_name="esco_skills")
    assert "not found" in str(exc_info.value)
    assert "check_data.py" in str(exc_info.value)


def test_missing_required_column_raises(tmp_path: Path):
    """Verify SchemaValidationError when a required column is not present."""
    csv_file = tmp_path / "invalid_columns.csv"
    # job_postings requires title and description; here description is missing
    csv_file.write_text("title,salary\nDeveloper,100000\n", encoding="utf-8")

    with pytest.raises(SchemaValidationError) as exc_info:
        load_and_validate_csv(csv_file, dataset_name="job_postings")
    assert "missing required column" in str(exc_info.value)
    assert "description" in str(exc_info.value)


def test_empty_dataset_raises(tmp_path: Path):
    """Verify EmptyDatasetError on empty CSV or all rows invalid."""
    empty_csv = tmp_path / "empty.csv"
    empty_csv.write_text("title,description\n", encoding="utf-8")

    with pytest.raises(EmptyDatasetError):
        load_and_validate_csv(empty_csv, dataset_name="job_postings")

    # CSV with only blank rows
    blanks_csv = tmp_path / "blanks.csv"
    blanks_csv.write_text("title,description\n  ,  \n", encoding="utf-8")
    with pytest.raises(EmptyDatasetError):
        load_and_validate_csv(blanks_csv, dataset_name="job_postings")


def test_specific_loaders_fail_when_raw_file_missing(tmp_path: Path, monkeypatch):
    """Verify specific loader functions raise DatasetNotFoundError when raw file is missing."""
    monkeypatch.setattr("config.settings.RAW_DATA_DIR", tmp_path)
    monkeypatch.setattr("config.settings.RAW_ESCO_SKILLS_FILE", tmp_path / "esco_skills.csv")
    monkeypatch.setattr("config.settings.RAW_JOB_POSTINGS_FILE", tmp_path / "job_postings.csv")
    monkeypatch.setattr("config.settings.RAW_RESUMES_FILE", tmp_path / "resumes.csv")
    monkeypatch.setattr("config.settings.RAW_COURSES_FILE", tmp_path / "courses.csv")

    with pytest.raises(DatasetNotFoundError):
        load_esco_skills()
    with pytest.raises(DatasetNotFoundError):
        load_job_postings()
    with pytest.raises(DatasetNotFoundError):
        load_resumes()
    with pytest.raises(DatasetNotFoundError):
        load_courses()
