"""SkillGap FastAPI Backend Application.

Provides REST endpoints for resume skill extraction, deterministic gap matching,
point-explainable scoring, what-if counterfactual simulation, career role comparisons,
and learning path recommendations.
"""

from __future__ import annotations

import json
import logging
import time
from contextlib import asynccontextmanager
from typing import Any, Dict, List, Optional, Set

from fastapi import (
    FastAPI,
    File,
    Form,
    HTTPException,
    Query,
    Request,
    Response,
    UploadFile,
    status,
)
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from api.cache import analysis_cache
from api.schemas import (
    AnalyzeResponse,
    CategoryCoverageItem,
    CompareRequest,
    CompareResponse,
    CompareRoleResult,
    CoveredSkillItem,
    ExtractedSkillItem,
    HealthResponse,
    LearningStepItem,
    MissingSkillItem,
    PartialSkillItem,
    RoleItem,
    ScoreBreakdown,
    SkillItem,
    WhatIfRequest,
    WhatIfResponse,
)
from config import settings
from ml.explain import compare_roles, what_if
from ml.extract import extract_skills, extractor
from ml.match import GapResult, gap_analysis
from ml.parse import (
    CorruptDocumentError,
    DocumentParsingError,
    EmptyDocumentError,
    FileTooLargeError,
    UnsupportedFileFormatError,
    parse_resume,
)
from ml.profiles import parse_job_description, role_manager
from ml.recommend import CourseCatalog, build_learning_path, course_catalog
from ml.slm import narrate_learning_path, ollama_client
from ml.taxonomy import is_ambiguous_skill, taxonomy

# Configure API logging: never log raw resume content or user PII
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("skillgap.api")

# Startup lifecycle state
api_state: Dict[str, bool] = {
    "taxonomy": False,
    "spacy": False,
    "sentence_transformer": False,
    "profiles": False,
    "courses": False,
}


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Load models, taxonomy, profiles, and indexes once at application startup."""
    logger.info("Initializing SkillGap backend services and pre-loading ML artifacts...")
    t0 = time.perf_counter()

    try:
        # 1. Load taxonomy and embeddings
        taxonomy.load()
        api_state["taxonomy"] = True

        # 2. Warm up spaCy and SentenceTransformer
        _ = extractor.nlp
        _ = extractor.matcher
        api_state["spacy"] = True

        _ = taxonomy.model
        api_state["sentence_transformer"] = True

        # 3. Load empirical role demand profiles
        role_manager.load()
        api_state["profiles"] = True

        # 4. Load course catalog and embeddings
        course_catalog.load()
        api_state["courses"] = True

        elapsed = time.perf_counter() - t0
        logger.info("All models and indexes successfully pre-loaded in %.2f seconds.", elapsed)
    except Exception as exc:
        logger.error("Error during startup pre-loading: %s", exc, exc_info=True)
        raise

    yield

    logger.info("Shutting down SkillGap backend services...")
    analysis_cache.clear()


app = FastAPI(
    title="SkillGap API",
    description=(
        "Deterministic, explainable job-skill gap analyzer. "
        "Extracts skills from resumes, scores match against real market demand, "
        "and generates grounded learning paths."
    ),
    version="1.0.0",
    lifespan=lifespan,
)

# CORS configuration strictly restricted to configured frontend origin
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL, "http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["*"],
)


@app.middleware("http")
async def add_process_time_and_log(request: Request, call_next):
    """Timing middleware: attaches X-Process-Time header and logs request metrics without PII."""
    start_time = time.perf_counter()
    response = await call_next(request)
    process_time = time.perf_counter() - start_time
    response.headers["X-Process-Time"] = f"{process_time:.4f}s"

    # Log route, status code, and latency (strictly omitting resume/form bodies)
    logger.info(
        "%s %s -> %d (%.4fs)",
        request.method,
        request.url.path,
        response.status_code,
        process_time,
    )
    return response


# ============================================================================
# Helper Functions
# ============================================================================

def parse_string_list(value: Optional[str]) -> List[str]:
    """Parse comma-separated or JSON array strings into a cleaned list of strings."""
    if not value or not value.strip():
        return []
    val = value.strip()
    if val.startswith("[") and val.endswith("]"):
        try:
            parsed = json.loads(val)
            if isinstance(parsed, list):
                return [str(item).strip() for item in parsed if str(item).strip()]
        except Exception:
            pass
    return [item.strip() for item in val.split(",") if item.strip()]


# ============================================================================
# Endpoints
# ============================================================================

@app.get("/health", response_model=HealthResponse, tags=["System"])
def get_health() -> HealthResponse:
    """Return health status, pre-loaded ML models, SLM state, and Ollama connectivity."""
    ollama_ok = False
    if settings.USE_SLM:
        try:
            ollama_ok = ollama_client.check_health()
        except Exception:
            ollama_ok = False

    return HealthResponse(
        status="ok",
        models_loaded=api_state,
        use_slm=settings.USE_SLM,
        ollama_reachable=ollama_ok,
    )


@app.get("/roles", response_model=List[RoleItem], tags=["Taxonomy & Roles"])
def list_roles() -> List[RoleItem]:
    """List all available canonical roles with backed job posting counts and core skills."""
    profiles = role_manager.profiles
    results: List[RoleItem] = []
    for role_name in sorted(profiles.keys()):
        p_data = profiles[role_name]
        n_postings = p_data.get("n_postings", 0)
        skills = p_data.get("skills", {})
        core_count = sum(1 for s in skills.values() if s.get("tier") == "core")
        results.append(
            RoleItem(
                role=role_name,
                postings_count=n_postings,
                core_skills_count=core_count,
            )
        )
    return results


@app.get("/skills", response_model=List[SkillItem], tags=["Taxonomy & Roles"])
def search_skills(
    q: str = Query("", description="Skill search prefix or substring"),
    limit: int = Query(20, ge=1, le=100, description="Maximum number of skills to return"),
) -> List[SkillItem]:
    """Search canonical taxonomy by skill ID, preferred label, or alias."""
    query = q.strip().lower()
    matches: List[SkillItem] = []

    for sid, info in taxonomy.skills.items():
        name = info.get("name", sid)
        category = info.get("category", "tools")
        aliases = info.get("aliases", [])

        if not query:
            matches.append(SkillItem(skill_id=sid, name=name, category=category, aliases=aliases))
        else:
            # Check match against ID, display name, or any alias
            if (
                query in sid.lower()
                or query in name.lower()
                or any(query in a.lower() for a in aliases)
            ):
                matches.append(SkillItem(skill_id=sid, name=name, category=category, aliases=aliases))

        if len(matches) >= limit:
            break

    return matches


@app.post(
    "/analyze",
    response_model=AnalyzeResponse,
    tags=["Analysis"],
    status_code=status.HTTP_200_OK,
)
async def analyze_resume(
    file: UploadFile = File(..., description="Resume file in PDF, DOCX, or TXT format (max 5 MB)"),
    role: Optional[str] = Form(None, description="Target canonical role name (e.g. 'Backend Developer')"),
    jd: Optional[str] = Form(None, description="Custom job description text if no role is selected"),
    manual_skills_add: Optional[str] = Form(None, description="Comma-separated or JSON list of skill IDs to manually add"),
    manual_skills_remove: Optional[str] = Form(None, description="Comma-separated or JSON list of skill IDs to manually remove"),
    manual_add: Optional[str] = Form(None, description="Alias for manual_skills_add"),
    manual_remove: Optional[str] = Form(None, description="Alias for manual_skills_remove"),
) -> AnalyzeResponse:
    """Analyze a candidate's resume against a role or custom job description.

    - Extracts skills in-memory without saving file to disk.
    - Deterministically scores requirement coverage and semantic alignment.
    - Generates grounded learning path with transparent point-gain explanations.
    """
    # 1. Validate role / JD inputs
    if not role and not jd:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'role' or 'jd' must be provided.",
        )

    target_profile: Dict[str, Any]
    role_name: str

    if role:
        prof = role_manager.get_role_profile(role)
        if not prof:
            avail = ", ".join(role_manager.get_canonical_roles())
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Unknown role '{role}'. Available roles: {avail}",
            )
        target_profile = prof
        role_name = role
    else:
        assert jd is not None
        if not jd.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Provided job description text is empty.",
            )
        target_profile = parse_job_description(jd, role_title="Custom Job Description")
        role_name = "Custom Job Description"

    # 2. Validate file format and size
    filename = file.filename or "resume.pdf"
    suffix = "." + filename.split(".")[-1].lower() if "." in filename else ""
    if suffix not in settings.ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unsupported file format '{suffix}'. Allowed formats: {sorted(settings.ALLOWED_EXTENSIONS)}",
        )

    # Read file content into memory
    content = await file.read()
    if not content:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Uploaded file is empty (0 bytes).",
        )

    max_bytes = settings.MAX_UPLOAD_SIZE_MB * 1024 * 1024
    if len(content) > max_bytes:
        raise HTTPException(
            status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
            detail=f"File size exceeds maximum allowed limit of {settings.MAX_UPLOAD_SIZE_MB} MB ({len(content)} bytes uploaded).",
        )

    # 3. Parse resume in memory
    try:
        resume_text = parse_resume(content, filename)
    except EmptyDocumentError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))
    except FileTooLargeError as err:
        raise HTTPException(status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE, detail=str(err))
    except (UnsupportedFileFormatError, CorruptDocumentError, DocumentParsingError) as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err))

    # 4. Extract skills from resume
    mode = "hybrid+slm" if settings.USE_SLM else "hybrid"
    extraction = extract_skills(resume_text, mode=mode)
    detected_skills: Set[str] = set(extraction.skills)

    # Process manual overrides (add / remove)
    to_add = set(parse_string_list(manual_skills_add) + parse_string_list(manual_add))
    to_remove = set(parse_string_list(manual_skills_remove) + parse_string_list(manual_remove))

    # Normalize manual adds
    valid_manual_adds: Set[str] = set()
    for item in to_add:
        info = taxonomy.get_skill(item)
        if info:
            valid_manual_adds.add(item)
        else:
            # Check if alias
            alias_id = taxonomy.lookup_alias(item)
            if alias_id:
                valid_manual_adds.add(alias_id)

    final_skills = (detected_skills - to_remove) | valid_manual_adds

    # 5. Build extracted skill items list for response
    extracted_items: List[ExtractedSkillItem] = []
    for sid in sorted(final_skills):
        s_info = taxonomy.get_skill(sid) or {}
        disp_name = s_info.get("name", sid)
        cat = s_info.get("category", "tools")

        if sid in valid_manual_adds and sid not in detected_skills:
            extracted_items.append(
                ExtractedSkillItem(
                    skill=disp_name,
                    skill_id=sid,
                    category=cat,
                    confidence=1.0,
                    source="manual",
                    evidence="Manually confirmed by candidate.",
                )
            )
        else:
            hits = extraction.skill_hits_by_id.get(sid, [])
            best_hit = hits[0] if hits else None
            conf = extraction.confidence_by_skill.get(sid, 1.0)
            evidence = extraction.best_sentences.get(sid, best_hit.sentence if best_hit else "")
            source = best_hit.source if best_hit else "dict"

            extracted_items.append(
                ExtractedSkillItem(
                    skill=disp_name,
                    skill_id=sid,
                    category=cat,
                    confidence=round(conf, 2),
                    source=source,
                    evidence=evidence,
                )
            )

    # 6. Deterministic gap analysis
    gap_result: GapResult = gap_analysis(
        resume_skills=final_skills,
        profile=target_profile,
        skill_emb=taxonomy,
    )

    # 7. Build learning path recommendations
    path = build_learning_path(
        gap_result=gap_result,
        profile=target_profile,
        hours_per_week=settings.DEFAULT_HOURS_PER_WEEK,
        catalog=course_catalog,
    )

    # 8. Generate summary narration
    if settings.USE_SLM:
        summary_text = narrate_learning_path(path.to_dict())
    else:
        summary_text = path.summary_text

    # 9. Store candidate skills in transient session cache (NO resume content stored)
    analysis_id = analysis_cache.set(
        skills=final_skills,
        role=role_name,
        jd_profile=target_profile if jd else None,
    )

    # 10. Format and assemble response
    covered_items = [
        CoveredSkillItem(
            skill=cs.name,
            skill_id=cs.skill_id,
            tier=cs.tier,
            weight=round(cs.weight, 3),
            match_type=cs.match_type,
            earned_weight=round(cs.earned_weight, 3),
        )
        for cs in gap_result.all_covered
    ]

    partial_items = [
        PartialSkillItem(
            skill=ps.name,
            skill_id=ps.skill_id,
            covered_by=ps.covered_by_name or ps.covered_by or "",
            similarity=ps.similarity,
        )
        for ps in gap_result.partial_matches
    ]

    missing_items = [
        MissingSkillItem(
            skill=ms.name,
            skill_id=ms.skill_id,
            tier=ms.tier,
            weight=round(ms.weight, 3),
            gain_if_learned=ms.potential_gain,
        )
        for ms in gap_result.missing_skills
    ]

    category_items = [
        CategoryCoverageItem(
            category=cat_data.category,
            coverage_score=cat_data.coverage_score,
            total_weight=cat_data.total_weight,
            earned_weight=cat_data.earned_weight,
            skills_count=cat_data.skills_count,
            covered_count=cat_data.covered_count,
        )
        for cat_data in gap_result.categories.values()
    ]

    learning_step_items = [
        LearningStepItem(
            step_number=step.step_number,
            phase_label=step.phase_label,
            primary_skill_name=step.primary_skill_name,
            primary_skill_id=step.primary_skill_id,
            course=step.course.to_dict(),
            score_gain=round(step.score_gain, 2),
            cumulative_score=round(step.cumulative_score, 2),
            why_chosen=step.why_chosen,
        )
        for step in path.steps
    ]

    return AnalyzeResponse(
        analysis_id=analysis_id,
        extracted_skills=extracted_items,
        score=ScoreBreakdown(
            final=gap_result.final_score,
            coverage=gap_result.coverage_score,
            semantic=gap_result.semantic_score,
        ),
        covered=covered_items,
        partial=partial_items,
        missing=missing_items,
        category_coverage=category_items,
        learning_path=learning_step_items,
        summary_text=summary_text,
    )


@app.post("/whatif", response_model=WhatIfResponse, tags=["Analysis"])
def simulate_whatif(payload: WhatIfRequest) -> WhatIfResponse:
    """Simulate score delta if candidate learns proposed additional skills.

    Uses analysis_id from previous session or explicit skills list.
    """
    resume_skills: List[str]

    if payload.analysis_id:
        cached = analysis_cache.get(payload.analysis_id)
        if not cached:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Analysis session '{payload.analysis_id}' not found or expired. Please re-run analysis.",
            )
        resume_skills = cached["skills"]
    elif payload.skills is not None:
        resume_skills = payload.skills
    else:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Either 'analysis_id' or 'skills' list must be provided.",
        )

    # Retrieve target role profile
    prof = role_manager.get_role_profile(payload.role)
    if not prof:
        # Check if matching cached custom JD profile
        if payload.analysis_id:
            cached = analysis_cache.get(payload.analysis_id)
            if cached and cached.get("jd_profile"):
                prof = cached["jd_profile"]

    if not prof:
        avail = ", ".join(role_manager.get_canonical_roles())
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Unknown role '{payload.role}'. Available roles: {avail}",
        )

    sim = what_if(
        resume_skills=resume_skills,
        profile=prof,
        add=payload.add,
        skill_emb=taxonomy,
    )

    return WhatIfResponse(
        original_score=sim["original_score"],
        original_coverage=sim["original_coverage"],
        new_score=sim["new_score"],
        new_coverage=sim["new_coverage"],
        delta_final=sim["delta_final"],
        delta_coverage=sim["delta_coverage"],
        added_skills=sim["added_skills"],
    )


@app.post("/compare", response_model=CompareResponse, tags=["Analysis"])
async def compare_candidate_roles(request: Request) -> CompareResponse:
    """Compare candidate skills across multiple roles to rank career fit.

    Accepts either:
    1. JSON request body: { analysis_id, skills, roles }
    2. Multipart form data: resume file or analysis_id + roles
    """
    content_type = request.headers.get("content-type", "").lower()
    candidate_skills: List[str] = []
    target_roles: Optional[List[str]] = None

    if "multipart/form-data" in content_type:
        form = await request.form()
        file_obj = form.get("file")
        analysis_id = form.get("analysis_id")
        skills_str = form.get("skills")
        roles_str = form.get("roles")

        if roles_str:
            target_roles = parse_string_list(str(roles_str))

        if file_obj and hasattr(file_obj, "read"):
            upload: UploadFile = file_obj  # type: ignore
            raw_bytes = await upload.read()
            if raw_bytes:
                fname = upload.filename or "resume.pdf"
                resume_text = parse_resume(raw_bytes, fname)
                ext = extract_skills(resume_text, mode="hybrid")
                candidate_skills = ext.skills
        elif analysis_id:
            cached = analysis_cache.get(str(analysis_id))
            if not cached:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Analysis session '{analysis_id}' not found or expired.",
                )
            candidate_skills = cached["skills"]
        elif skills_str:
            candidate_skills = parse_string_list(str(skills_str))

    else:
        # JSON request body
        try:
            body = await request.json()
            payload = CompareRequest(**body)
        except Exception as exc:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Invalid JSON request body: {exc}",
            )

        target_roles = payload.roles
        if payload.analysis_id:
            cached = analysis_cache.get(payload.analysis_id)
            if not cached:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Analysis session '{payload.analysis_id}' not found or expired.",
                )
            candidate_skills = cached["skills"]
        elif payload.skills is not None:
            candidate_skills = payload.skills

    if not candidate_skills:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No candidate skills found. Provide a resume file, analysis_id, or skills list.",
        )

    # Perform role comparison
    comp = compare_roles(
        resume_skills=candidate_skills,
        roles=target_roles,
        profile_manager=role_manager,
        skill_emb=taxonomy,
    )

    ranked_items: List[CompareRoleResult] = []
    for item in comp["ranked_roles"]:
        ranked_items.append(
            CompareRoleResult(
                role=item["role"],
                final_score=item["final_score"],
                coverage_score=item["coverage_score"],
                semantic_score=item["semantic_score"],
                exact_matches_count=item.get("exact_matches_count", 0),
                partial_matches_count=item.get("partial_matches_count", 0),
                missing_skills_count=item.get("missing_skills_count", 0),
            )
        )

    return CompareResponse(
        best_fit_role=comp["best_fit_role"],
        best_fit_score=comp["best_fit_score"],
        ranked_roles=ranked_items,
    )
