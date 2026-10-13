"""Resume Builder API Endpoints for SkillGap.

Provides stateless, Zero-PII endpoints for:
- Catalog and social platform lookups
- Deterministic ATS lint checks
- Multi-format resume rendering (PDF, HTML, DOCX, Markdown, Text, JSON)
- Document importing (PDF, DOCX, TXT)
"""

from __future__ import annotations

import json
import logging
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional

from fastapi import APIRouter, File, HTTPException, Response, UploadFile, status
from pydantic import BaseModel, Field

from config import settings
from ml.parse import (
    CorruptDocumentError,
    DocumentParsingError,
    EmptyDocumentError,
    FileTooLargeError,
    UnsupportedFileFormatError,
)
from ml.resume_import import import_resume
from ml.resume_lint import lint
from ml.resume_render import (
    export_json,
    render_docx,
    render_html,
    render_markdown,
    render_pdf,
    render_text,
)
from ml.resume_schema import Resume

logger = logging.getLogger("skillgap.resume_api")

router = APIRouter(prefix="/resume", tags=["Resume Builder"])

CATALOG_FILE = settings.DATA_DIR / "processed" / "tech_catalog.json"
PLATFORMS_FILE = settings.DATA_DIR / "processed" / "social_platforms.json"


class RenderRequest(BaseModel):
    resume: Resume
    format: Literal["pdf", "html", "docx", "txt", "md", "json"] = "pdf"
    template: Literal["classic", "compact", "technical"] = "classic"
    page_size: Literal["A4", "Letter"] = "A4"


class LintIssue(BaseModel):
    level: Literal["error", "warning", "tip"]
    section: str
    message: str
    path: str


class ImportResponse(BaseModel):
    resume: Dict[str, Any]
    needs_review: List[Dict[str, str]]


@router.get(
    "/catalog",
    summary="Get standard technology catalog",
    description="Retrieve categorized technical skills, platforms, and canonical taxonomy mappings.",
)
async def get_tech_catalog() -> Dict[str, Any]:
    if not CATALOG_FILE.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Technology catalog data file not found.",
        )
    with open(CATALOG_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@router.get(
    "/socials",
    summary="Get supported social & professional platforms",
    description="Retrieve definitions, URL templates, and validators for social links.",
)
async def get_social_platforms() -> List[Dict[str, Any]]:
    if not PLATFORMS_FILE.exists():
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Social platforms data file not found.",
        )
    with open(PLATFORMS_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@router.post(
    "/lint",
    response_model=List[LintIssue],
    summary="Stateless ATS resume linting",
    description="Evaluates resume against professional ATS rules and structural guidelines in memory without storing.",
)
async def lint_resume(resume: Resume) -> List[Dict[str, str]]:
    # Stateless backend: never log resume content
    logger.info("Executing stateless resume linting check")
    issues = lint(resume)
    return issues


@router.post(
    "/render",
    summary="Render resume to specified format",
    description="Generates ATS-safe document in PDF, HTML, DOCX, Markdown, Text, or JSON format.",
)
async def render_resume_endpoint(request: RenderRequest):
    # Stateless backend: never log resume content
    logger.info(
        "Rendering resume to format=%s, template=%s, page_size=%s",
        request.format,
        request.template,
        request.page_size,
    )
    fmt = request.format.lower()
    tmpl = request.template.lower()
    page_sz = request.page_size

    try:
        if fmt == "pdf":
            pdf_bytes = render_pdf(request.resume, template_name=tmpl, page_size=page_sz)
            return Response(
                content=pdf_bytes,
                media_type="application/pdf",
                headers={"Content-Disposition": 'attachment; filename="resume.pdf"'},
            )
        elif fmt == "html":
            html_str = render_html(request.resume, template_name=tmpl, page_size=page_sz)
            return Response(
                content=html_str,
                media_type="text/html; charset=utf-8",
                headers={"Content-Disposition": 'inline; filename="resume.html"'},
            )
        elif fmt == "docx":
            docx_bytes = render_docx(request.resume)
            return Response(
                content=docx_bytes,
                media_type="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                headers={"Content-Disposition": 'attachment; filename="resume.docx"'},
            )
        elif fmt == "txt":
            txt_str = render_text(request.resume)
            return Response(
                content=txt_str,
                media_type="text/plain; charset=utf-8",
                headers={"Content-Disposition": 'attachment; filename="resume.txt"'},
            )
        elif fmt == "md":
            md_str = render_markdown(request.resume)
            return Response(
                content=md_str,
                media_type="text/markdown; charset=utf-8",
                headers={"Content-Disposition": 'attachment; filename="resume.md"'},
            )
        elif fmt == "json":
            json_str = export_json(request.resume)
            return Response(
                content=json_str,
                media_type="application/json; charset=utf-8",
                headers={"Content-Disposition": 'attachment; filename="resume.json"'},
            )
        else:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unsupported format '{fmt}'. Choose 'pdf', 'html', 'docx', 'txt', 'md', or 'json'.",
            )
    except Exception as exc:
        logger.error(f"Error rendering resume: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to render resume: {exc}",
        )


@router.post(
    "/import",
    response_model=ImportResponse,
    summary="Import resume file into draft",
    description="Parses an uploaded PDF, DOCX, or TXT document in-memory into a draft resume with review notes.",
)
async def import_resume_endpoint(file: UploadFile = File(...)) -> ImportResponse:
    filename = file.filename or "uploaded_resume.pdf"
    logger.info("Importing resume document filename=%s", filename)

    try:
        content = await file.read()
        if not content:
            raise EmptyDocumentError("Uploaded file is empty.")

        result = import_resume(content, filename)
        return ImportResponse(**result)

    except EmptyDocumentError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    except FileTooLargeError as exc:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(exc))
    except UnsupportedFileFormatError as exc:
        raise HTTPException(status_code=status.HTTP_415_UNSUPPORTED_MEDIA_TYPE, detail=str(exc))
    except CorruptDocumentError as exc:
        raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail=str(exc))
    except Exception as exc:
        logger.error(f"Unexpected error during resume import: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to parse resume document.",
        )
