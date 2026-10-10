"""Data ingestion, validation, and normalization module for raw datasets.

Loads raw CSV datasets (ESCO/O*NET skills, job postings, resumes, courses),
validates schema, maps column names, drops duplicates and empty entries,
normalizes text fields, and logs row counts before and after cleaning.
"""

from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Union
import pandas as pd

from config import settings

logger = logging.getLogger(__name__)
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("[%(asctime)s] [%(levelname)s] %(name)s: %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class DataLoadError(Exception):
    """Base exception for data loading and validation failures."""


class DatasetNotFoundError(DataLoadError, FileNotFoundError):
    """Raised when a requested dataset file is missing from data/raw/."""


class SchemaValidationError(DataLoadError, ValueError):
    """Raised when a dataset is missing one or more required columns."""


class EmptyDatasetError(DataLoadError, ValueError):
    """Raised when a dataset contains no rows after cleaning."""


def clean_text_cell(val: object) -> str:
    """Normalize a single cell value by collapsing whitespace and stripping edges."""
    if pd.isna(val):
        return ""
    text = str(val)
    # Collapse multiple spaces, tabs, and newlines into single spaces
    text = re.sub(r"\s+", " ", text)
    return text.strip()


def load_and_validate_csv(
    file_path: Union[str, Path],
    dataset_name: str,
    required_columns: Optional[List[str]] = None,
    column_mapping: Optional[Dict[str, str]] = None,
) -> pd.DataFrame:
    """Load, validate, map columns, and clean a CSV dataset.

    Args:
        file_path: Path to the target CSV file.
        dataset_name: Identifier of the dataset (e.g., 'esco_skills', 'job_postings').
        required_columns: Canonical column names required for this dataset.
            If None, loaded from settings.REQUIRED_COLUMNS.
        column_mapping: Mapping from raw CSV headers to canonical names.
            If None, loaded from settings.COLUMN_MAPPINGS.

    Returns:
        Cleaned pandas DataFrame with canonical column names.

    Raises:
        DatasetNotFoundError: If file does not exist on disk.
        SchemaValidationError: If required columns cannot be satisfied.
        EmptyDatasetError: If dataset has 0 rows before or after cleaning.
    """
    path = Path(file_path)
    if not path.is_file():
        raise DatasetNotFoundError(
            f"Dataset '{dataset_name}' not found at '{path}'. "
            f"Run 'python scripts/check_data.py' for download instructions."
        )

    # Resolve column mappings and required columns from settings if not supplied
    mapping = column_mapping if column_mapping is not None else settings.COLUMN_MAPPINGS.get(dataset_name, {})
    req_cols = required_columns if required_columns is not None else settings.REQUIRED_COLUMNS.get(dataset_name, [])

    # Read CSV
    try:
        df = pd.read_csv(path, encoding="utf-8", on_bad_lines="skip")
    except UnicodeDecodeError:
        df = pd.read_csv(path, encoding="latin-1", on_bad_lines="skip")

    initial_row_count = len(df)
    logger.info(
        "Loading dataset '%s' from %s. Initial row count: %d, Raw columns: %s",
        dataset_name,
        path.name,
        initial_row_count,
        list(df.columns),
    )

    if initial_row_count == 0:
        raise EmptyDatasetError(f"Dataset '{dataset_name}' at '{path}' is empty (0 rows).")

    # Rename columns using mapping
    df = df.rename(columns=mapping)

    # Validate required columns
    missing_cols = [c for c in req_cols if c not in df.columns]
    if missing_cols:
        raise SchemaValidationError(
            f"Dataset '{dataset_name}' is missing required column(s): {missing_cols}. "
            f"Detected columns after mapping: {list(df.columns)}. "
            f"Update 'COLUMN_MAPPINGS[\"{dataset_name}\"]' in config.py if headers differ."
        )

    # Drop fully duplicate rows
    df = df.drop_duplicates()

    # Normalize whitespace for string/object columns
    for col in df.columns:
        if df[col].dtype == object or pd.api.types.is_string_dtype(df[col]):
            df[col] = df[col].apply(clean_text_cell)

    # Drop rows where any required column is empty or NA
    for col in req_cols:
        df = df[df[col].notna() & (df[col] != "")]

    # Deduplicate again based on required text columns
    if req_cols:
        df = df.drop_duplicates(subset=req_cols)

    final_row_count = len(df)
    dropped_count = initial_row_count - final_row_count
    logger.info(
        "Dataset '%s' cleaned. Rows retained: %d, Dropped (empty/duplicates): %d",
        dataset_name,
        final_row_count,
        dropped_count,
    )

    if final_row_count == 0:
        raise EmptyDatasetError(
            f"Dataset '{dataset_name}' contains 0 valid rows after dropping empty/duplicate entries."
        )

    # Reset index
    df = df.reset_index(drop=True)
    return df


def load_esco_skills(file_path: Optional[Union[str, Path]] = None) -> pd.DataFrame:
    """Load ESCO skills dataset."""
    path = file_path if file_path is not None else settings.RAW_ESCO_SKILLS_FILE
    return load_and_validate_csv(path, "esco_skills")


def load_onet_skills(file_path: Optional[Union[str, Path]] = None) -> pd.DataFrame:
    """Load O*NET skills dataset (optional)."""
    path = file_path if file_path is not None else settings.RAW_ONET_SKILLS_FILE
    return load_and_validate_csv(path, "onet_skills", required_columns=["preferred_label"])


def load_job_postings(file_path: Optional[Union[str, Path]] = None) -> pd.DataFrame:
    """Load job postings dataset."""
    path = file_path if file_path is not None else settings.RAW_JOB_POSTINGS_FILE
    return load_and_validate_csv(path, "job_postings")


def load_resumes(file_path: Optional[Union[str, Path]] = None) -> pd.DataFrame:
    """Load resumes dataset."""
    path = file_path if file_path is not None else settings.RAW_RESUMES_FILE
    return load_and_validate_csv(path, "resumes")


def load_courses(file_path: Optional[Union[str, Path]] = None) -> pd.DataFrame:
    """Load courses dataset."""
    path = file_path if file_path is not None else settings.RAW_COURSES_FILE
    return load_and_validate_csv(path, "courses")
