"""Deterministic explainability and impact engine for SkillGap.

Translates gap analysis into signed point contributions, evidence grounding,
what-if counterfactual scenario simulations, and impact-ranked learning priorities.
All reasons and explanations are deterministic and template-grounded (no LLM hallucinations).
"""

from __future__ import annotations

import logging
from dataclasses import asdict, dataclass
from typing import Any, Dict, List, Optional, Set, Union

import numpy as np

from config import Settings, settings
from ml.match import CoveredSkill, GapResult, gap_analysis
from ml.profiles import RoleProfileManager
from ml.taxonomy import Taxonomy, taxonomy

logger = logging.getLogger(__name__)


@dataclass
class SkillContribution:
    """Exact point contribution of a skill to the coverage score."""

    skill_id: str
    skill_name: str
    status: str  # "covered", "partial", "missing"
    tier: str  # "core", "common", "bonus"
    weight: float  # Empirical demand weight (e.g. 0.70)
    points: float  # Points added to coverage score (+X.XX for covered/partial, 0.0 for missing)
    points_lost: float  # Points lost from maximum potential (-X.XX for missing/partial, 0.0 for covered)
    signed_points: float  # Positive if earned, negative if missing
    reason: str  # Deterministic plain-English explanation

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class GapImpact:
    """Potential score gain from acquiring a missing skill."""

    skill_id: str
    skill_name: str
    tier: str
    weight: float
    demand_share_pct: float
    score_gain: float  # Percentage points increase in coverage score
    reason: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def generate_reason(
    skill_id: str,
    role_name: str,
    status: str,
    weight: float,
    tier: str,
    covered_by_name: Optional[str] = None,
    similarity: Optional[float] = None,
) -> str:
    """Generate deterministic, plain-English explanation based on empirical demand."""
    info = taxonomy.get_skill(skill_id) or {}
    skill_name = info.get("name", skill_id)
    share_pct = int(round(weight * 100))

    if status == "covered":
        if tier == "core":
            return f"{skill_name} is a core requirement ({share_pct}% demand in {role_name}) and is verified on your resume."
        elif tier == "common":
            return f"{skill_name} is a common skill ({share_pct}% demand in {role_name}) and is verified on your resume."
        else:
            return f"{skill_name} is an advantageous bonus skill ({share_pct}% demand) and is verified on your resume."

    elif status == "partial":
        sim_pct = int(round((similarity or 0.8) * 100))
        cand_str = f"'{covered_by_name}'" if covered_by_name else "a related skill"
        return (
            f"You list {cand_str}, which is closely related to {skill_name} "
            f"({sim_pct}% semantic match). Partial credit awarded."
        )

    else:  # status == "missing"
        if tier == "core":
            return f"{skill_name} appears in {share_pct}% of {role_name} postings. You don't list it."
        elif tier == "common":
            return f"{skill_name} appears in {share_pct}% of {role_name} postings. Adding it will strengthen your competitive edge."
        else:
            return f"{skill_name} appears in {share_pct}% of postings as an optional or bonus qualification."


def explain_contributions(
    gap_result: GapResult,
    profile: Dict[str, Any],
) -> List[SkillContribution]:
    """Calculate the exact signed point contribution of every role skill.

    Guarantees:
    - Points earned from covered and partial skills sum EXACTLY to gap_result.coverage_score.
    - Points lost from missing and partial skills sum to 100.0 - gap_result.coverage_score.
    """
    total_w = gap_result.total_weight
    if total_w <= 0:
        return []

    profile_skills = profile.get("skills", {})
    exact_ids = {s.skill_id: s for s in gap_result.exact_matches}
    partial_ids = {s.skill_id: s for s in gap_result.partial_matches}
    missing_ids = {s.skill_id: s for s in gap_result.missing_skills}

    contributions: List[SkillContribution] = []

    for sid, skill_meta in profile_skills.items():
        w = float(skill_meta.get("weight", 1.0))
        tier = str(skill_meta.get("tier", "bonus"))
        skill_info = taxonomy.get_skill(sid) or {}
        name = skill_meta.get("name") or skill_info.get("name", sid)

        if sid in exact_ids:
            # Full credit
            pts = (w / total_w) * 100.0
            pts_lost = 0.0
            signed_pts = pts
            status = "covered"
            reason = generate_reason(sid, gap_result.role, "covered", w, tier)
        elif sid in partial_ids:
            # Partial credit (half weight)
            part_match = partial_ids[sid]
            pts = (part_match.earned_weight / total_w) * 100.0
            pts_lost = -((w - part_match.earned_weight) / total_w) * 100.0
            signed_pts = pts
            status = "partial"
            reason = generate_reason(
                sid,
                gap_result.role,
                "partial",
                w,
                tier,
                covered_by_name=part_match.covered_by_name,
                similarity=part_match.similarity,
            )
        else:
            # Missing skill
            pts = 0.0
            pts_lost = -(w / total_w) * 100.0
            signed_pts = pts_lost
            status = "missing"
            reason = generate_reason(sid, gap_result.role, "missing", w, tier)

        contributions.append(
            SkillContribution(
                skill_id=sid,
                skill_name=name,
                status=status,
                tier=tier,
                weight=round(w, 4),
                points=round(pts, 4),
                points_lost=round(pts_lost, 4),
                signed_points=round(signed_pts, 4),
                reason=reason,
            )
        )

    # Sort: covered first by points descending, then partial, then missing by points_lost ascending (most negative first)
    status_order = {"covered": 0, "partial": 1, "missing": 2}
    contributions.sort(key=lambda c: (status_order[c.status], -c.points, c.points_lost))
    return contributions


def get_skill_evidence(
    covered_skills: List[CoveredSkill],
    best_sentences: Dict[str, str],
) -> Dict[str, str]:
    """Retrieve the exact sentence from the resume demonstrating each covered skill."""
    evidence_map: Dict[str, str] = {}
    for cs in covered_skills:
        # If exact match, look for the skill's own evidence
        if cs.skill_id in best_sentences:
            evidence_map[cs.skill_id] = best_sentences[cs.skill_id]
        # If partial match, look for the covering skill's evidence
        elif cs.covered_by and cs.covered_by in best_sentences:
            evidence_map[cs.skill_id] = (
                f"(Via related skill '{cs.covered_by_name}'): {best_sentences[cs.covered_by]}"
            )
        else:
            evidence_map[cs.skill_id] = "Identified from candidate skill keywords."
    return evidence_map


def what_if(
    resume_skills: List[str] | Set[str],
    profile: Dict[str, Any],
    add: List[str] | Set[str],
    skill_emb: Optional[Union[Dict[str, np.ndarray], Taxonomy]] = None,
    cfg: Optional[Settings] = None,
    resume_text_emb: Optional[np.ndarray] = None,
    role_text_emb: Optional[np.ndarray] = None,
) -> Dict[str, Any]:
    """Simulate the score delta if the candidate learns one or more additional skills.

    Reuses the exact same deterministic gap_analysis function (no approximations).
    Guaranteed: delta is non-negative when valid skills are added.
    """
    baseline_result = gap_analysis(
        resume_skills=resume_skills,
        profile=profile,
        skill_emb=skill_emb,
        cfg=cfg,
        resume_text_emb=resume_text_emb,
        role_text_emb=role_text_emb,
    )

    augmented_skills = set(resume_skills) | set(add)
    updated_result = gap_analysis(
        resume_skills=augmented_skills,
        profile=profile,
        skill_emb=skill_emb,
        cfg=cfg,
        resume_text_emb=resume_text_emb,
        role_text_emb=role_text_emb,
    )

    delta_coverage = updated_result.coverage_score - baseline_result.coverage_score
    delta_final = updated_result.final_score - baseline_result.final_score

    return {
        "original_score": baseline_result.final_score,
        "original_coverage": baseline_result.coverage_score,
        "new_score": updated_result.final_score,
        "new_coverage": updated_result.coverage_score,
        "delta_coverage": round(max(0.0, delta_coverage), 2),
        "delta_final": round(max(0.0, delta_final), 2),
        "added_skills": sorted(list(add)),
        "updated_result": updated_result,
    }


def rank_gaps_by_impact(
    gap_result: GapResult,
    profile: Dict[str, Any],
    skill_emb: Optional[Union[Dict[str, np.ndarray], Taxonomy]] = None,
    cfg: Optional[Settings] = None,
) -> List[GapImpact]:
    """Rank all missing skills by their immediate score impact if learned.

    This directly drives candidate learning priorities: high-impact core skills
    appear at the top.
    """
    impacts: List[GapImpact] = []

    for ms in gap_result.missing_skills:
        sim = what_if(
            resume_skills=gap_result.resume_skills,
            profile=profile,
            add=[ms.skill_id],
            skill_emb=skill_emb,
            cfg=cfg,
        )
        score_gain = sim["delta_coverage"]
        reason = generate_reason(ms.skill_id, gap_result.role, "missing", ms.weight, ms.tier)

        impacts.append(
            GapImpact(
                skill_id=ms.skill_id,
                skill_name=ms.name,
                tier=ms.tier,
                weight=ms.weight,
                demand_share_pct=round(ms.weight * 100, 1),
                score_gain=score_gain,
                reason=reason,
            )
        )

    # Sort descending by score gain
    impacts.sort(key=lambda x: (x.score_gain, x.weight), reverse=True)
    return impacts


def compare_roles(
    resume_skills: List[str] | Set[str],
    roles: Optional[List[str]] = None,
    profile_manager: Optional[RoleProfileManager] = None,
    skill_emb: Optional[Union[Dict[str, np.ndarray], Taxonomy]] = None,
    cfg: Optional[Settings] = None,
    resume_text_emb: Optional[np.ndarray] = None,
) -> Dict[str, Any]:
    """Evaluate candidate skills across multiple roles to rank career fit.

    Args:
        resume_skills: Extracted candidate skills.
        roles: Specific roles to compare. If None, evaluates all canonical roles.
        profile_manager: RoleProfileManager instance.
        skill_emb: Embeddings for partial credit.
        cfg: Settings instance.
        resume_text_emb: Candidate's resume text embedding.

    Returns:
        Dictionary containing side-by-side role comparisons and ranked best-fit roles.
    """
    pm = profile_manager or RoleProfileManager()
    available_roles = roles or pm.get_canonical_roles()

    ranked_results: List[Dict[str, Any]] = []

    for role_name in available_roles:
        prof = pm.get_role_profile(role_name)
        if not prof:
            continue

        role_emb = pm.get_role_embedding(role_name)
        res = gap_analysis(
            resume_skills=resume_skills,
            profile=prof,
            skill_emb=skill_emb,
            cfg=cfg,
            resume_text_emb=resume_text_emb,
            role_text_emb=role_emb,
        )

        ranked_results.append(
            {
                "role": role_name,
                "final_score": res.final_score,
                "coverage_score": res.coverage_score,
                "semantic_score": res.semantic_score,
                "exact_matches_count": len(res.exact_matches),
                "partial_matches_count": len(res.partial_matches),
                "missing_skills_count": len(res.missing_skills),
                "gap_result": res,
            }
        )

    # Rank by final_score descending, then coverage_score descending
    ranked_results.sort(key=lambda r: (r["final_score"], r["coverage_score"]), reverse=True)

    best_fit = ranked_results[0] if ranked_results else None

    return {
        "best_fit_role": best_fit["role"] if best_fit else None,
        "best_fit_score": best_fit["final_score"] if best_fit else 0.0,
        "ranked_roles": ranked_results,
    }
