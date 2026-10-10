"""Pydantic request and response schemas for the SkillGap REST API.

Strictly typed, validated, and documented for OpenAPI generation.
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


# ============================================================================
# Health & Status
# ============================================================================

class HealthResponse(BaseModel):
    """Health check response schema."""

    status: str = Field(..., description="Service health status", examples=["ok"])
    models_loaded: Dict[str, bool] = Field(
        ...,
        description="Loaded status of all underlying ML models and artifacts",
        examples=[{"spacy": True, "sentence_transformer": True, "taxonomy": True, "profiles": True, "courses": True}],
    )
    use_slm: bool = Field(..., description="Whether SLM integration is enabled in settings")
    ollama_reachable: bool = Field(..., description="Whether local Ollama daemon is currently reachable")


# ============================================================================
# Roles & Taxonomy
# ============================================================================

class RoleItem(BaseModel):
    """Role summary information with posting counts."""

    role: str = Field(..., description="Canonical role title", examples=["Backend Developer"])
    postings_count: int = Field(..., description="Number of job postings backing this profile", examples=[7])
    core_skills_count: int = Field(default=0, description="Count of core-tier required skills", examples=[5])


class SkillItem(BaseModel):
    """Taxonomy skill representation for search and manual selection."""

    skill_id: str = Field(..., description="Canonical skill identifier", examples=["fastapi"])
    name: str = Field(..., description="Display name of the skill", examples=["FastAPI"])
    category: str = Field(..., description="Functional domain category", examples=["web"])
    aliases: List[str] = Field(default_factory=list, description="Common aliases and acronyms", examples=[["fast-api"]])


# ============================================================================
# Analysis & Scoring Schemas
# ============================================================================

class ExtractedSkillItem(BaseModel):
    """Details of a single skill detected on the candidate's resume."""

    skill: str = Field(..., description="Canonical display name of the skill", examples=["Python"])
    skill_id: str = Field(..., description="Canonical ID in taxonomy", examples=["python"])
    category: str = Field(..., description="Skill category", examples=["programming"])
    confidence: float = Field(..., description="Extraction confidence score (0.0 to 1.0)", examples=[1.0])
    source: str = Field(..., description="Extraction mechanism: dict, semantic, slm, manual", examples=["dict"])
    evidence: str = Field(..., description="Sentence or excerpt from resume demonstrating this skill")


class ScoreBreakdown(BaseModel):
    """Explainable scoring components."""

    final: float = Field(..., description="Combined final match score (0-100)", examples=[82.5])
    coverage: float = Field(..., description="Deterministic requirement coverage score (0-100)", examples=[85.0])
    semantic: float = Field(..., description="Semantic text alignment score (0-100)", examples=[72.5])


class CoveredSkillItem(BaseModel):
    """Covered role requirement."""

    skill: str = Field(..., description="Canonical skill name", examples=["Python"])
    skill_id: str = Field(..., description="Canonical skill ID", examples=["python"])
    tier: str = Field(..., description="Importance tier: core, common, bonus", examples=["core"])
    weight: float = Field(..., description="Share of postings requiring this skill", examples=[1.0])
    match_type: str = Field(..., description="Type of match: exact or partial", examples=["exact"])
    earned_weight: float = Field(..., description="Credit earned towards coverage", examples=[1.0])


class PartialSkillItem(BaseModel):
    """Role skill partially covered through semantic similarity."""

    skill: str = Field(..., description="Required skill name", examples=["FastAPI"])
    skill_id: str = Field(..., description="Required skill ID", examples=["fastapi"])
    covered_by: str = Field(..., description="Resume skill providing partial credit", examples=["flask"])
    similarity: float = Field(..., description="Cosine similarity between the two skills", examples=[0.82])


class MissingSkillItem(BaseModel):
    """Unmet skill requirement with quantifiable score impact."""

    skill: str = Field(..., description="Missing skill name", examples=["Docker"])
    skill_id: str = Field(..., description="Missing skill ID", examples=["docker"])
    tier: str = Field(..., description="Importance tier: core, common, bonus", examples=["core"])
    weight: float = Field(..., description="Share of postings requiring this skill", examples=[0.857])
    gain_if_learned: float = Field(
        ...,
        description="Percentage points added to coverage score if candidate acquires this skill",
        examples=[14.28],
    )


class CategoryCoverageItem(BaseModel):
    """Breakdown of skill coverage within a specific domain category."""

    category: str = Field(..., description="Domain category name", examples=["programming"])
    coverage_score: float = Field(..., description="Category coverage percentage (0-100)", examples=[100.0])
    total_weight: float = Field(..., description="Total required weight in this category", examples=[2.5])
    earned_weight: float = Field(..., description="Earned credit in this category", examples=[2.5])
    skills_count: int = Field(..., description="Total skills demanded in this category", examples=[3])
    covered_count: int = Field(..., description="Total skills covered in this category", examples=[3])


class CourseDetail(BaseModel):
    """Recommended course metadata."""

    course_id: str = Field(..., description="Course identifier")
    title: str = Field(..., description="Course title")
    platform: str = Field(..., description="Course platform or provider")
    level: str = Field(..., description="Difficulty level")
    duration_hours: float = Field(..., description="Estimated hours to complete")
    rating: float = Field(..., description="Course rating (1-5)")
    url: str = Field(..., description="URL to course")
    taught_skills: List[str] = Field(default_factory=list, description="Skills covered by course")


class LearningStepItem(BaseModel):
    """Scheduled learning milestone in the recommended curriculum."""

    step_number: int = Field(..., description="Sequence index", examples=[1])
    phase_label: str = Field(..., description="Calendar phase timeframe", examples=["Weeks 1-2"])
    primary_skill_name: str = Field(..., description="Primary skill addressed", examples=["Docker"])
    primary_skill_id: str = Field(..., description="Primary skill ID", examples=["docker"])
    course: CourseDetail = Field(..., description="Recommended course details")
    score_gain: float = Field(..., description="Coverage score points gained", examples=[14.28])
    cumulative_score: float = Field(..., description="Projected coverage score upon completion", examples=[95.0])
    why_chosen: str = Field(..., description="Grounded explanation for course selection")


class AnalyzeResponse(BaseModel):
    """Complete, fully explainable response for /analyze."""

    analysis_id: str = Field(..., description="Session identifier for follow-up what-if scenarios")
    extracted_skills: List[ExtractedSkillItem] = Field(..., description="Skills detected on the resume")
    score: ScoreBreakdown = Field(..., description="Final, coverage, and semantic scores")
    covered: List[CoveredSkillItem] = Field(..., description="Fully or partially covered role requirements")
    partial: List[PartialSkillItem] = Field(..., description="Partial semantic credit matches")
    missing: List[MissingSkillItem] = Field(..., description="Missing skills with point gain potential")
    category_coverage: List[CategoryCoverageItem] = Field(..., description="Domain category breakdowns")
    learning_path: List[LearningStepItem] = Field(..., description="Step-by-step ordered learning roadmap")
    summary_text: str = Field(..., description="Grounded natural-language roadmap summary")


# ============================================================================
# What-If Counterfactual Schemas
# ============================================================================

class WhatIfRequest(BaseModel):
    """Request schema for /whatif score simulations."""

    analysis_id: Optional[str] = Field(
        default=None,
        description="ID of a previous analysis session stored in memory",
        examples=["a1b2c3d4-0000-0000-0000-000000000000"],
    )
    skills: Optional[List[str]] = Field(
        default=None,
        description="Explicit list of candidate skill IDs if no analysis_id is provided",
        examples=[["python", "fastapi", "sql"]],
    )
    role: str = Field(..., description="Canonical role name to simulate against", examples=["Backend Developer"])
    add: List[str] = Field(..., description="List of skill IDs candidate proposes to learn", examples=[["docker", "postgresql"]])


class WhatIfResponse(BaseModel):
    """Response schema for /whatif simulations."""

    original_score: float = Field(..., description="Baseline final score before learning skills")
    original_coverage: float = Field(..., description="Baseline coverage score")
    new_score: float = Field(..., description="Projected final score after acquiring added skills")
    new_coverage: float = Field(..., description="Projected coverage score after acquiring added skills")
    delta_final: float = Field(..., description="Total points gained on final score")
    delta_coverage: float = Field(..., description="Total points gained on coverage score")
    added_skills: List[str] = Field(..., description="List of valid added skills simulated")


# ============================================================================
# Role Comparison Schemas
# ============================================================================

class CompareRequest(BaseModel):
    """Request schema for JSON-based role comparison."""

    analysis_id: Optional[str] = Field(
        default=None,
        description="Cached analysis ID holding candidate skills",
    )
    skills: Optional[List[str]] = Field(
        default=None,
        description="Candidate skill IDs to compare",
        examples=[["python", "docker", "sql", "git"]],
    )
    roles: Optional[List[str]] = Field(
        default=None,
        description="Specific list of roles to rank. If omitted, all canonical roles are compared.",
        examples=[["Backend Developer", "DevOps Engineer", "Data Engineer"]],
    )


class CompareRoleResult(BaseModel):
    """Fit metrics for a single compared role."""

    role: str = Field(..., description="Canonical role name")
    final_score: float = Field(..., description="Weighted match score (0-100)")
    coverage_score: float = Field(..., description="Deterministic coverage score (0-100)")
    semantic_score: float = Field(..., description="Semantic alignment score (0-100)")
    exact_matches_count: int = Field(default=0, description="Number of exact skill matches")
    partial_matches_count: int = Field(default=0, description="Number of partial semantic matches")
    missing_skills_count: int = Field(default=0, description="Count of missing demanded skills")


class CompareResponse(BaseModel):
    """Response schema for /compare endpoint."""

    best_fit_role: Optional[str] = Field(..., description="Top-matching canonical role title")
    best_fit_score: float = Field(..., description="Final score of the best-fit role")
    ranked_roles: List[CompareRoleResult] = Field(..., description="All compared roles ranked by fit")
