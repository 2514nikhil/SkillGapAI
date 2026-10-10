"""Deterministic gap matching engine for SkillGap.

Compares resume skills against empirical role demand profiles or custom JDs.
Provides explainable coverage, partial semantic credit, semantic role alignment,
and per-category coverage breakdowns.
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple, Union

import numpy as np

from config import Settings, settings
from ml.taxonomy import Taxonomy, taxonomy

logger = logging.getLogger(__name__)


@dataclass
class CoveredSkill:
    """Skill demanded by the role that is covered by the candidate."""

    skill_id: str
    name: str
    tier: str  # "core", "common", "bonus"
    weight: float  # Share of role postings demanding this skill
    match_type: str  # "exact" or "partial"
    earned_weight: float  # Weight credited towards coverage
    covered_by: Optional[str] = None  # Resume skill providing coverage if partial
    covered_by_name: Optional[str] = None
    similarity: float = 1.0  # 1.0 for exact, cosine similarity for partial

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class MissingSkill:
    """Skill demanded by the role that is missing from the candidate's resume."""

    skill_id: str
    name: str
    tier: str  # "core", "common", "bonus"
    weight: float  # Share of role postings demanding this skill
    category: str = "tools"
    potential_gain: float = 0.0  # Percentage points gained if acquired

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class CategoryCoverage:
    """Skill coverage metrics within a specific skill domain."""

    category: str
    total_weight: float
    earned_weight: float
    coverage_score: float  # 0 - 100 percentage
    skills_count: int
    covered_count: int

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GapResult:
    """Comprehensive, fully explainable result of gap analysis."""

    role: str
    final_score: float  # 0 - 100 weighted combined score
    coverage_score: float  # 0 - 100 deterministic skill coverage score
    semantic_score: float  # 0 - 100 calibrated text semantic similarity score
    raw_cosine: Optional[float]
    total_weight: float
    earned_weight: float
    exact_matches: List[CoveredSkill]
    partial_matches: List[CoveredSkill]
    missing_skills: List[MissingSkill]
    categories: Dict[str, CategoryCoverage]
    resume_skills: List[str]
    n_postings: int = 1

    @property
    def all_covered(self) -> List[CoveredSkill]:
        """All covered skills (exact + partial)."""
        return self.exact_matches + self.partial_matches

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "final_score": round(self.final_score, 2),
            "coverage_score": round(self.coverage_score, 2),
            "semantic_score": round(self.semantic_score, 2),
            "raw_cosine": round(self.raw_cosine, 4) if self.raw_cosine is not None else None,
            "total_weight": round(self.total_weight, 4),
            "earned_weight": round(self.earned_weight, 4),
            "exact_matches": [s.to_dict() for s in self.exact_matches],
            "partial_matches": [s.to_dict() for s in self.partial_matches],
            "missing_skills": [s.to_dict() for s in self.missing_skills],
            "categories": {cat: data.to_dict() for cat, data in self.categories.items()},
            "resume_skills": self.resume_skills,
            "n_postings": self.n_postings,
        }


def _get_vector(
    skill_id: str,
    skill_emb: Optional[Union[Dict[str, np.ndarray], Taxonomy]],
) -> Optional[np.ndarray]:
    """Retrieve normalized embedding vector for a skill ID from various source types."""
    if skill_emb is None:
        return taxonomy.get_skill_embedding(skill_id)
    if isinstance(skill_emb, dict):
        return skill_emb.get(skill_id)
    if hasattr(skill_emb, "get_skill_embedding"):
        return skill_emb.get_skill_embedding(skill_id)
    return None


def calibrate_semantic_score(
    raw_cosine: float,
    min_cos: float = settings.SEMANTIC_MIN_COSINE,
    max_cos: float = settings.SEMANTIC_MAX_COSINE,
) -> float:
    """Rescale raw cosine similarity to an explainable 0-100 score.

    Calibration maps empirical min cosine (random unrelated text ~0.15) to 0.0,
    and empirical max cosine (strong job description alignment ~0.85) to 100.0.
    """
    if max_cos <= min_cos:
        return float(np.clip(raw_cosine, 0.0, 1.0) * 100.0)
    clamped = float(np.clip((raw_cosine - min_cos) / (max_cos - min_cos), 0.0, 1.0))
    return clamped * 100.0


def gap_analysis(
    resume_skills: List[str] | Set[str],
    profile: Dict[str, Any],
    skill_emb: Optional[Union[Dict[str, np.ndarray], Taxonomy]] = None,
    cfg: Optional[Settings] = None,
    resume_text_emb: Optional[np.ndarray] = None,
    role_text_emb: Optional[np.ndarray] = None,
) -> GapResult:
    """Perform deterministic gap analysis between candidate skills and role demands.

    Args:
        resume_skills: List or set of canonical skill IDs extracted from resume.
        profile: Role profile dict (from role_profiles.json or profile_from_jd).
        skill_emb: Embedding source (dict or Taxonomy instance) for partial matching.
        cfg: Configuration settings instance (defaults to global settings).
        resume_text_emb: Precomputed sentence embedding of resume text.
        role_text_emb: Precomputed sentence embedding of role description text.

    Returns:
        GapResult with deterministic scores, match breakdowns, and explanations.
    """
    c = cfg or settings
    resume_set: Set[str] = set(resume_skills)

    # Extract role metadata and skills map
    role_name = profile.get("role", "Target Role")
    n_postings = profile.get("n_postings", 1)
    profile_skills_map: Dict[str, Dict[str, Any]] = profile.get("skills", {})

    exact_matches: List[CoveredSkill] = []
    partial_matches: List[CoveredSkill] = []
    missing_skills: List[MissingSkill] = []

    total_weight: float = 0.0
    earned_weight: float = 0.0

    # Per-category aggregation buffers: category -> [total_w, earned_w, total_cnt, covered_cnt]
    category_metrics: Dict[str, List[float]] = {}

    # Pre-fetch candidate embedding vectors for partial credit comparison
    candidate_vectors: List[Tuple[str, np.ndarray]] = []
    for rs_id in resume_set:
        vec = _get_vector(rs_id, skill_emb)
        if vec is not None:
            candidate_vectors.append((rs_id, vec))

    for req_id, skill_meta in profile_skills_map.items():
        w = float(skill_meta.get("weight", 1.0))
        tier = str(skill_meta.get("tier", "bonus"))
        total_weight += w

        skill_info = taxonomy.get_skill(req_id) or {}
        skill_name = skill_meta.get("name") or skill_info.get("name", req_id)
        skill_category = skill_meta.get("category") or skill_info.get("category", "tools")

        if skill_category not in category_metrics:
            category_metrics[skill_category] = [0.0, 0.0, 0.0, 0.0]
        category_metrics[skill_category][0] += w
        category_metrics[skill_category][2] += 1.0

        if req_id in resume_set:
            # 1. Exact match -> Full weight credit
            earned_weight += w
            category_metrics[skill_category][1] += w
            category_metrics[skill_category][3] += 1.0
            exact_matches.append(
                CoveredSkill(
                    skill_id=req_id,
                    name=skill_name,
                    tier=tier,
                    weight=w,
                    match_type="exact",
                    earned_weight=w,
                    covered_by=req_id,
                    covered_by_name=skill_name,
                    similarity=1.0,
                )
            )
        else:
            # 2. Check for partial semantic match
            req_vec = _get_vector(req_id, skill_emb)
            best_sim = 0.0
            best_candidate_id: Optional[str] = None

            if req_vec is not None and candidate_vectors:
                for cand_id, cand_vec in candidate_vectors:
                    sim = float(np.dot(req_vec, cand_vec))
                    if sim > best_sim:
                        best_sim = sim
                        best_candidate_id = cand_id

            if best_sim >= c.PARTIAL_THRESHOLD and best_candidate_id is not None:
                # Partial match -> partial weight credit
                earned_credit = w * c.PARTIAL_CREDIT
                earned_weight += earned_credit
                category_metrics[skill_category][1] += earned_credit
                category_metrics[skill_category][3] += 0.5  # fractional count

                cand_info = taxonomy.get_skill(best_candidate_id) or {}
                cand_name = cand_info.get("name", best_candidate_id)

                partial_matches.append(
                    CoveredSkill(
                        skill_id=req_id,
                        name=skill_name,
                        tier=tier,
                        weight=w,
                        match_type="partial",
                        earned_weight=earned_credit,
                        covered_by=best_candidate_id,
                        covered_by_name=cand_name,
                        similarity=round(best_sim, 4),
                    )
                )
            else:
                # 3. Missing skill
                missing_skills.append(
                    MissingSkill(
                        skill_id=req_id,
                        name=skill_name,
                        tier=tier,
                        weight=w,
                        category=skill_category,
                    )
                )

    # Sort missing skills by weight descending
    missing_skills.sort(key=lambda s: s.weight, reverse=True)

    # Compute coverage score (0 - 100)
    if total_weight > 0:
        coverage_score = float((earned_weight / total_weight) * 100.0)
    else:
        coverage_score = 100.0 if not profile_skills_map else 0.0

    # Calculate potential gain for each missing skill
    for ms in missing_skills:
        if total_weight > 0:
            ms.potential_gain = round((ms.weight / total_weight) * 100.0, 2)
        else:
            ms.potential_gain = 0.0

    # Compute semantic score (0 - 100) from text embeddings if available
    raw_cosine: Optional[float] = None
    if resume_text_emb is not None and role_text_emb is not None:
        norm_r = float(np.linalg.norm(resume_text_emb))
        norm_t = float(np.linalg.norm(role_text_emb))
        if norm_r > 0 and norm_t > 0:
            raw_cosine = float(np.dot(resume_text_emb, role_text_emb) / (norm_r * norm_t))
            semantic_score = calibrate_semantic_score(
                raw_cosine, min_cos=c.SEMANTIC_MIN_COSINE, max_cos=c.SEMANTIC_MAX_COSINE
            )
        else:
            semantic_score = coverage_score
    else:
        semantic_score = coverage_score

    # Compute final combined score
    final_score = float((c.W_COVERAGE * coverage_score) + (c.W_SEMANTIC * semantic_score))

    # Build per-category coverage breakdown
    categories: Dict[str, CategoryCoverage] = {}
    for cat, (cat_tot_w, cat_ear_w, cat_tot_cnt, cat_cov_cnt) in category_metrics.items():
        cat_cov = (cat_ear_w / cat_tot_w * 100.0) if cat_tot_w > 0 else 0.0
        categories[cat] = CategoryCoverage(
            category=cat,
            total_weight=round(cat_tot_w, 4),
            earned_weight=round(cat_ear_w, 4),
            coverage_score=round(cat_cov, 2),
            skills_count=int(cat_tot_cnt),
            covered_count=int(round(cat_cov_cnt)),
        )

    return GapResult(
        role=role_name,
        final_score=round(final_score, 2),
        coverage_score=round(coverage_score, 2),
        semantic_score=round(semantic_score, 2),
        raw_cosine=raw_cosine,
        total_weight=round(total_weight, 4),
        earned_weight=round(earned_weight, 4),
        exact_matches=exact_matches,
        partial_matches=partial_matches,
        missing_skills=missing_skills,
        categories=categories,
        resume_skills=sorted(list(resume_set)),
        n_postings=n_postings,
    )
