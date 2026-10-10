"""Tests for resume and document parser ml/parse.py."""

from pathlib import Path
import pytest

from config import settings
from ml.parse import (
    CorruptDocumentError,
    DocumentParsingError,
    EmptyDocumentError,
    FileTooLargeError,
    UnsupportedFileFormatError,
    clean_hyphenated_line_breaks,
    clean_page_numbers,
    normalize_whitespace,
    parse_resume,
    parse_document_path,
)


def test_clean_hyphenated_line_breaks():
    """Verify rejoining words split across line breaks by hyphens."""
    raw = "Senior soft-\nware deve-\n loper with strong background."
    cleaned = clean_hyphenated_line_breaks(raw)
    assert "software" in cleaned
    assert "developer" in cleaned


def test_clean_page_numbers():
    """Verify removal of page numbers and pagination strings."""
    raw = "Skills Summary\nPage 1 of 4\nPython, Docker\n2 / 4\nExperience\n- 3 -\nSenior Engineer"
    cleaned = clean_page_numbers(raw)
    assert "Page 1 of 4" not in cleaned
    assert "2 / 4" not in cleaned
    assert "- 3 -" not in cleaned
    assert "Python, Docker" in cleaned


def test_normalize_whitespace():
    """Verify whitespace cleaning, hyphen rejoining, and pagination removal."""
    raw = "  Hello   \xa0 world!  \r\nPage 1 of 2\r\n\r\n\r\nsoft-\nware. \t "
    cleaned = normalize_whitespace(raw)
    assert cleaned == "Hello world!\n\nsoftware."


def test_normalize_empty_text():
    """Verify normalize_whitespace handles empty and whitespace-only text."""
    assert normalize_whitespace("") == ""
    assert normalize_whitespace("   \n\n  \t ") == ""


def test_parse_resume_txt_and_fallback(tmp_path: Path):
    """Test parsing a plain text resume from bytes and plain-text fallback."""
    sample_text = "John Doe\nSoftware Engineer\nSkills: Python, SQL"
    raw_bytes = sample_text.encode("utf-8")

    # Regular .txt
    extracted = parse_resume(raw_bytes, "resume.txt")
    assert "John Doe" in extracted
    assert "Skills: Python, SQL" in extracted

    # Extension-less fallback
    extracted_fallback = parse_resume(raw_bytes, "resume_no_ext")
    assert "John Doe" in extracted_fallback


def test_parse_resume_pdf_fixture():
    """Test parsing the generated sample PDF fixture."""
    pdf_path = settings.FIXTURES_DIR / "sample_resume.pdf"
    assert pdf_path.exists(), "sample_resume.pdf fixture must exist"

    extracted = parse_resume(pdf_path.read_bytes(), "sample_resume.pdf")
    assert "Alice Johnson" in extracted
    assert "Machine Learning Engineer" in extracted
    assert "TensorFlow" in extracted


def test_parse_resume_docx_fixture():
    """Test parsing the generated sample DOCX fixture."""
    docx_path = settings.FIXTURES_DIR / "sample_resume.docx"
    assert docx_path.exists(), "sample_resume.docx fixture must exist"

    extracted = parse_resume(docx_path.read_bytes(), "sample_resume.docx")
    assert "Jane Smith" in extracted
    assert "Data Scientist" in extracted
    assert "Python" in extracted
    assert "scikit-learn" in extracted


def test_scanned_or_empty_pdf_raises():
    """Verify that an empty or scanned PDF with no text stream raises clear error."""
    # A valid PDF with a single empty page
    empty_pdf = (
        b"%PDF-1.4\n"
        b"1 0 obj\n<< /Type /Catalog /Pages 2 0 R >>\nendobj\n"
        b"2 0 obj\n<< /Type /Pages /Kids [3 0 R] /Count 1 >>\nendobj\n"
        b"3 0 obj\n<< /Type /Page /Parent 2 0 R /MediaBox [0 0 612 792] >>\nendobj\n"
        b"xref\n0 4\n0000000000 65535 f \n0000000009 00000 n \n0000000058 00000 n \n0000000115 00000 n \n"
        b"trailer\n<< /Size 4 /Root 1 0 R >>\nstartxref\n185\n%%EOF"
    )
    with pytest.raises(EmptyDocumentError) as exc_info:
        parse_resume(empty_pdf, "scanned.pdf")
    assert "No text found; the PDF may be scanned" in str(exc_info.value)


def test_file_too_large_raises(monkeypatch):
    """Verify that files exceeding the configured size limit trigger FileTooLargeError."""
    monkeypatch.setattr(settings, "MAX_UPLOAD_SIZE_MB", 1)
    large_bytes = b"a" * (2 * 1024 * 1024)
    with pytest.raises(FileTooLargeError):
        parse_resume(large_bytes, "large.txt")


def test_corrupt_pdf_raises():
    """Verify that corrupt PDF bytes trigger CorruptDocumentError."""
    corrupt_bytes = b"%PDF-1.4 corrupt junk data that cannot be parsed by pdfplumber"
    with pytest.raises(CorruptDocumentError):
        parse_resume(corrupt_bytes, "corrupt.pdf")


def test_corrupt_docx_raises():
    """Verify that non-zip corrupt docx bytes trigger CorruptDocumentError."""
    corrupt_bytes = b"PK not a real docx zip archive"
    with pytest.raises(CorruptDocumentError):
        parse_resume(corrupt_bytes, "corrupt.docx")


def test_nonexistent_file_path():
    """Verify FileNotFoundError when attempting to parse nonexistent file path."""
    with pytest.raises(FileNotFoundError):
        parse_document_path("non_existent_file_12345.pdf")
