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
    resume: Dict[str, Any]
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
async def lint_resume(resume: Dict[str, Any]) -> List[Dict[str, str]]:
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


# =========================================================================
# AI Writing Assistant Endpoints (Phase 12C)
# =========================================================================

from fastapi import Request
import time
from ml.resume_ai import (
    draft_summary,
    improve_bullet,
    polish_project,
    suggest_skills_from_text,
    tailor,
)

# Lightweight in-memory rate limiter per IP: max 60 req/min
_RATE_LIMIT_STORE: Dict[str, List[float]] = {}
MAX_AI_REQUESTS_PER_MINUTE = 60


def _enforce_rate_limit(request: Request):
    client_ip = request.client.host if request.client else "127.0.0.1"
    now = time.time()
    history = _RATE_LIMIT_STORE.setdefault(client_ip, [])
    # Prune timestamps older than 60s
    _RATE_LIMIT_STORE[client_ip] = [t for t in history if now - t < 60.0]
    if len(_RATE_LIMIT_STORE[client_ip]) >= MAX_AI_REQUESTS_PER_MINUTE:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail="Rate limit exceeded for AI writing assistant (max 60 requests per minute).",
        )
    _RATE_LIMIT_STORE[client_ip].append(now)


class BulletImproveRequest(BaseModel):
    text: str = Field(..., min_length=3, max_length=500)
    context: Optional[Dict[str, Any]] = None


class ProjectPolishRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=120)
    tech: List[str] = Field(default_factory=list, max_length=30)
    notes: str = Field(..., min_length=3, max_length=2000)


class TailorRequest(BaseModel):
    resume: Dict[str, Any]
    target: str = Field(..., min_length=2, max_length=5000)


@router.post(
    "/ai/bullet",
    summary="Improve bullet point",
    description="Rewrites bullet point into strong ATS variants with zero invented facts.",
)
async def improve_bullet_endpoint(req: BulletImproveRequest, request: Request):
    _enforce_rate_limit(request)
    logger.info("Executing AI bullet improvement")
    try:
        result = improve_bullet(req.text, req.context)
        return result
    except Exception as exc:
        logger.error(f"Error in improve_bullet: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to improve bullet: {exc}",
        )


@router.post(
    "/ai/summary",
    summary="Draft resume summary",
    description="Generates executive summary strictly from verified candidate resume data.",
)
async def draft_summary_endpoint(resume: Dict[str, Any], request: Request):
    _enforce_rate_limit(request)
    logger.info("Executing AI summary drafting")
    try:
        result = draft_summary(resume)
        return result
    except Exception as exc:
        logger.error(f"Error in draft_summary: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to draft summary: {exc}",
        )


@router.post(
    "/ai/project",
    summary="Polish project notes into bullets",
    description="Transforms raw project notes into concise bullets without introducing new tools.",
)
async def polish_project_endpoint(req: ProjectPolishRequest, request: Request):
    _enforce_rate_limit(request)
    logger.info("Executing AI project polish")
    try:
        result = polish_project(req.name, req.tech, req.notes)
        return result
    except Exception as exc:
        logger.error(f"Error in polish_project: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to polish project: {exc}",
        )


@router.post(
    "/ai/suggest-skills",
    summary="Discover unlisted skills from resume text",
    description="Deterministically identifies skills present in bullets/descriptions that are not in selected skills.",
)
async def suggest_skills_endpoint(resume: Dict[str, Any], request: Request):
    _enforce_rate_limit(request)
    logger.info("Executing AI skill suggestions from text")
    try:
        suggestions = suggest_skills_from_text(resume)
        return {"suggestions": suggestions}
    except Exception as exc:
        logger.error(f"Error in suggest_skills_from_text: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to suggest skills: {exc}",
        )


@router.post(
    "/ai/tailor",
    summary="Tailor resume against target role or job description",
    description="Evaluates match and gap impact against target role without mutates the candidate's resume.",
)
async def tailor_endpoint(req: TailorRequest, request: Request):
    _enforce_rate_limit(request)
    logger.info("Executing AI resume tailoring analysis")
    try:
        result = tailor(req.resume, req.target)
        return result
    except Exception as exc:
        logger.error(f"Error in tailor: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to tailor resume: {exc}",
        )

