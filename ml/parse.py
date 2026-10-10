"""Resume and document parsing module for SkillGap.

Extracts text from PDF, DOCX, and TXT files in-memory without saving
uploaded files to disk. Adheres strictly to zero disk persistence.
"""

from __future__ import annotations

import io
import re
from pathlib import Path
from typing import BinaryIO, Union

import docx
import pdfplumber

from config import settings


class DocumentParsingError(Exception):
    """Base exception for all document parsing errors."""


class UnsupportedFileFormatError(DocumentParsingError):
    """Raised when an uploaded file is not one of the supported formats."""


class FileTooLargeError(DocumentParsingError):
    """Raised when file content exceeds the configured size limit."""


class EmptyDocumentError(DocumentParsingError):
    """Raised when extracted document text is empty or PDF is scanned."""


class CorruptDocumentError(DocumentParsingError):
    """Raised when a document cannot be parsed due to corrupt data."""


def clean_page_numbers(text: str) -> str:
    """Remove common header/footer page number patterns from extracted text."""
    if not text:
        return ""

    # Remove patterns like 'Page 1 of 5', 'Page 1', 'page 3 / 10'
    text = re.sub(
        r"(?i)\bpage\s+\d+(\s*(?:of|/)\s*\d+)?\b",
        "",
        text,
    )

    # Remove standalone page numbers on isolated lines (e.g., '1', '- 2 -', '3 / 4')
    cleaned_lines: list[str] = []
    for line in text.split("\n"):
        stripped = line.strip()
        if re.match(r"^[-–—]?\s*\d+\s*[-–—]?$", stripped) or re.match(r"^\d+\s*/\s*\d+$", stripped):
            continue
        cleaned_lines.append(line)

    return "\n".join(cleaned_lines)


def clean_hyphenated_line_breaks(text: str) -> str:
    """Rejoin words split across line breaks by hyphens.

    Example: 'archi-\\ntecture' -> 'architecture'
    """
    if not text:
        return ""
    # Rejoin lower/mixed-case words split across line break
    return re.sub(r"([A-Za-z]{2,})-\s*\n\s*([A-Za-z]{2,})", r"\1\2", text)


def normalize_whitespace(text: str) -> str:
    """Normalize extracted text whitespace and structure.

    Cleans hyphenated line breaks, removes page numbers, normalizes
    unicode spaces, collapses internal multiple spaces, and limits
    consecutive newlines.

    Args:
        text: Raw extracted string from the document parser.

    Returns:
        Cleaned, normalized string.
    """
    if not text:
        return ""

    # Rejoin words broken across lines by hyphens
    cleaned = clean_hyphenated_line_breaks(text)

    # Strip page numbers
    cleaned = clean_page_numbers(cleaned)

    # Replace non-breaking spaces, form feeds, and line separators
    cleaned = cleaned.replace("\xa0", " ").replace("\r\n", "\n").replace("\r", "\n")
    # Replace non-printable ASCII characters except newline and tab
    cleaned = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", cleaned)

    # Clean per line: collapse multiple spaces/tabs into a single space and trim
    cleaned_lines = [re.sub(r"[ \t]+", " ", line).strip() for line in cleaned.split("\n")]
    result = "\n".join(cleaned_lines)

    # Collapse multiple consecutive newlines (max 2)
    result = re.sub(r"\n{3,}", "\n\n", result)
    return result.strip()


def parse_pdf_stream(stream: BinaryIO) -> str:
    """Extract text from a PDF stream in-memory.

    Args:
        stream: A binary stream pointing to PDF bytes.

    Returns:
        Extracted text as a string.

    Raises:
        CorruptDocumentError: If PDF structure is invalid or unreadable.
        EmptyDocumentError: If no readable text is present or PDF is scanned.
    """
    try:
        pages_text: list[str] = []
        with pdfplumber.open(stream) as pdf:
            if not pdf.pages:
                raise EmptyDocumentError("The PDF document contains no pages.")
            for page in pdf.pages:
                page_text = page.extract_text()
                if page_text:
                    pages_text.append(page_text)

        full_text = "\n\n".join(pages_text).strip()
        cleaned_text = normalize_whitespace(full_text)
        if not cleaned_text:
            raise EmptyDocumentError("No text found; the PDF may be scanned.")
        return cleaned_text
    except EmptyDocumentError:
        raise
    except Exception as exc:
        raise CorruptDocumentError(f"Failed to parse PDF document: {exc}") from exc


def parse_docx_stream(stream: BinaryIO) -> str:
    """Extract text from a DOCX stream in-memory.

    Reads paragraphs and table cells to ensure complete skill capture.

    Args:
        stream: A binary stream pointing to DOCX bytes.

    Returns:
        Extracted text as a string.

    Raises:
        CorruptDocumentError: If DOCX structure is invalid or corrupt.
        EmptyDocumentError: If document contains no readable text.
    """
    try:
        doc = docx.Document(stream)
        elements: list[str] = []

        # Extract paragraphs
        for p in doc.paragraphs:
            text = p.text.strip()
            if text:
                elements.append(text)

        # Extract table contents (frequently used for skills/experience in resumes)
        for table in doc.tables:
            for row in table.rows:
                row_cells = [cell.text.strip() for cell in row.cells if cell.text.strip()]
                if row_cells:
                    # Deduplicate adjacent cells if merged
                    deduped_cells: list[str] = []
                    for c in row_cells:
                        if not deduped_cells or c != deduped_cells[-1]:
                            deduped_cells.append(c)
                    elements.append(" | ".join(deduped_cells))

        full_text = "\n".join(elements).strip()
        cleaned_text = normalize_whitespace(full_text)
        if not cleaned_text:
            raise EmptyDocumentError("The DOCX document contains no readable text.")
        return cleaned_text
    except EmptyDocumentError:
        raise
    except Exception as exc:
        raise CorruptDocumentError(f"Failed to parse DOCX document: {exc}") from exc


def parse_txt_stream(stream: BinaryIO) -> str:
    """Extract text from a plain text stream in-memory.

    Args:
        stream: A binary stream pointing to text bytes.

    Returns:
        Decoded and normalized string.

    Raises:
        CorruptDocumentError: If text cannot be decoded using supported encodings.
        EmptyDocumentError: If stream contains only whitespace.
    """
    raw_bytes = stream.read()
    if not raw_bytes:
        raise EmptyDocumentError("The text file is completely empty.")

    decoded: str | None = None
    for encoding in ("utf-8", "utf-8-sig", "latin-1", "cp1252"):
        try:
            decoded = raw_bytes.decode(encoding)
            break
        except UnicodeDecodeError:
            continue

    if decoded is None:
        raise CorruptDocumentError("Could not decode text file using supported encodings.")

    cleaned = normalize_whitespace(decoded)
    if not cleaned:
        raise EmptyDocumentError("The text file contains no readable content.")
    return cleaned


def parse_resume(file_bytes: bytes, filename: str) -> str:
    """Parse resume document from raw in-memory bytes with plain-text fallback.

    Args:
        file_bytes: In-memory byte array of the uploaded resume.
        filename: Original file name used to determine format.

    Returns:
        Cleaned, normalized text content.

    Raises:
        FileTooLargeError: If byte size exceeds MAX_UPLOAD_SIZE_MB.
        EmptyDocumentError: If document has 0 bytes, is empty, or is a scanned PDF.
        CorruptDocumentError: If file is malformed or unreadable.
        UnsupportedFileFormatError: If file cannot be parsed.
    """
    if not file_bytes:
        raise EmptyDocumentError("Uploaded file is empty (0 bytes).")

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(file_bytes) > max_bytes:
        raise FileTooLargeError(
            f"File exceeds maximum allowed size of {settings.MAX_UPLOAD_SIZE_MB}MB "
            f"({len(file_bytes)} bytes provided)."
        )

    suffix = Path(filename).suffix.lower()
    stream = io.BytesIO(file_bytes)

    if suffix == ".pdf":
        return parse_pdf_stream(stream)
    elif suffix == ".docx":
        return parse_docx_stream(stream)
    elif suffix == ".txt":
        return parse_txt_stream(stream)
    else:
        # Fallback to plain-text decoding attempt for unspecified or text-compatible formats
        try:
            return parse_txt_stream(stream)
        except Exception:
            raise UnsupportedFileFormatError(
                f"Unsupported file format '{suffix}'. Allowed formats: {sorted(settings.ALLOWED_EXTENSIONS)}"
            )


# Backward compatibility aliases
parse_document_bytes = parse_resume


def parse_document_path(file_path: Union[str, Path]) -> str:
    """Parse resume document from a file path without keeping it in memory longer than needed."""
    path = Path(file_path)
    if not path.is_file():
        raise FileNotFoundError(f"File not found: {path}")

    raw_bytes = path.read_bytes()
    return parse_resume(raw_bytes, path.name)
