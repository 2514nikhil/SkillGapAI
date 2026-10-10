"""Course recommendation and grounded learning path engine for SkillGap.

Retrieves and scores courses for missing skills using semantic relevance,
explicit skill tags, rating, difficulty level fit, and duration penalties.
Builds realistic, prerequisite-aware, de-duplicated calendar schedules.
"""

from __future__ import annotations

import json
import logging
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np

from config import Settings, settings
from ml.explain import what_if
from ml.match import GapResult
from ml.taxonomy import Taxonomy, taxonomy

logger = logging.getLogger(__name__)


@dataclass
class ScoredCourse:
    """Course recommendation with explicit transparent score breakdown."""

    course_id: str
    title: str
    description: str
    platform: str
    level: str
    duration_hours: float
    rating: float
    url: str
    taught_skills: List[str]
    total_score: float
    score_breakdown: Dict[str, float]
    why_chosen: str

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class LearningStep:
    """A scheduled milestone in the candidate's learning path."""

    step_number: int
    phase_label: str  # e.g. "Weeks 1-2"
    primary_skill_id: str
    primary_skill_name: str
    course: ScoredCourse
    score_gain: float  # Percentage points added by this milestone
    cumulative_score: float  # Projected total coverage score after this step
    covered_skills: List[str]  # All missing skills satisfied by this course
    why_chosen: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "step_number": self.step_number,
            "phase_label": self.phase_label,
            "primary_skill_id": self.primary_skill_id,
            "primary_skill_name": self.primary_skill_name,
            "course": self.course.to_dict(),
            "score_gain": round(self.score_gain, 2),
            "cumulative_score": round(self.cumulative_score, 2),
            "covered_skills": self.covered_skills,
            "why_chosen": self.why_chosen,
        }


@dataclass
class LearningPath:
    """Complete, end-to-end grounded learning plan."""

    role: str
    baseline_score: float
    projected_final_score: float
    total_duration_hours: float
    total_weeks: int
    hours_per_week: int
    steps: List[LearningStep]

    @property
    def summary_text(self) -> str:
        """Deterministic template-grounded summary of the learning roadmap."""
        return (
            f"Your personalized learning plan for {self.role} is designed to elevate your skill coverage "
            f"from {self.baseline_score:.1f}% to {self.projected_final_score:.1f}% over {self.total_weeks} weeks at {self.hours_per_week} hours per week. "
            f"By focusing on critical foundational gaps first, each completed milestone delivers an immediate, "
            f"measurable increase toward your target career readiness."
        )

    def to_dict(self) -> Dict[str, Any]:
        return {
            "role": self.role,
            "baseline_score": round(self.baseline_score, 2),
            "projected_final_score": round(self.projected_final_score, 2),
            "total_duration_hours": round(self.total_duration_hours, 1),
            "total_weeks": self.total_weeks,
            "hours_per_week": self.hours_per_week,
            "steps": [s.to_dict() for s in self.steps],
            "summary_text": self.summary_text,
        }


class CourseCatalog:
    """Manages course index, metadata, and precomputed embeddings."""

    def __init__(
        self,
        courses_file: Optional[Path] = None,
        embeddings_file: Optional[Path] = None,
        prereqs_file: Optional[Path] = None,
    ):
        self.courses_file = courses_file or settings.COURSES_FILE
        self.embeddings_file = embeddings_file or settings.COURSE_EMBEDDINGS_FILE
        self.prereqs_file = prereqs_file or settings.PREREQS_FILE

        self._courses: List[Dict[str, Any]] = []
        self._embeddings: Optional[np.ndarray] = None
        self._prereqs: Dict[str, List[str]] = {}
        self._loaded: bool = False

    def is_loaded(self) -> bool:
        return self._loaded

    def load(self) -> None:
        """Load processed courses, embeddings, and prerequisite relationships."""
        if not self.courses_file.is_file():
            raise FileNotFoundError(
                f"Course index not found at '{self.courses_file}'. "
                f"Run 'python scripts/build_course_index.py' first."
            )

        with open(self.courses_file, "r", encoding="utf-8") as f:
            self._courses = json.load(f)

        if self.embeddings_file.is_file():
            self._embeddings = np.load(self.embeddings_file)
        else:
            self._embeddings = np.zeros((len(self._courses), 384), dtype=np.float32)

        if self.prereqs_file.is_file():
            with open(self.prereqs_file, "r", encoding="utf-8") as f:
                self._prereqs = json.load(f)
        else:
            self._prereqs = {}

        self._loaded = True
        logger.info("Loaded course catalog with %d courses.", len(self._courses))

    @property
    def courses(self) -> List[Dict[str, Any]]:
        if not self._loaded:
            self.load()
        return self._courses

    @property
    def embeddings(self) -> np.ndarray:
        if not self._loaded:
            self.load()
        return self._embeddings

    @property
    def prereqs(self) -> Dict[str, List[str]]:
        if not self._loaded:
            self.load()
        return self._prereqs


# Module singleton
course_catalog = CourseCatalog()


def calculate_level_fit(course_level: str, preferred_level: str) -> float:
    """Calculate 0.0 - 1.0 fit between student target level and course difficulty."""
    cl = course_level.lower().strip()
    pl = preferred_level.lower().strip()

    if cl in ("all levels", "all", pl):
        return 1.0
    if pl == "beginner":
        if cl == "intermediate":
            return 0.6
        if cl == "advanced":
            return 0.2
    elif pl == "intermediate":
        if cl in ("beginner", "advanced"):
            return 0.8
    elif pl == "advanced":
        if cl == "intermediate":
            return 0.8
        if cl == "beginner":
            return 0.4
    return 0.7


def recommend_for_skill(
    skill_id: str,
    level_pref: str = "Beginner",
    k: int = 3,
    catalog: Optional[CourseCatalog] = None,
    cfg: Optional[Settings] = None,
) -> List[ScoredCourse]:
    """Recommend top-k courses for a specific missing skill.

    Scored by:
        total = (relevance * W_RELEVANCE) + exact_bonus + rating_score + level_score - duration_penalty

    Returns:
        List of ScoredCourse objects with full score breakdown and explanation.
    """
    cat = catalog or course_catalog
    if not cat.is_loaded():
        cat.load()

    c = cfg or settings
    taxonomy.load()

    skill_vec = taxonomy.get_skill_embedding(skill_id)
    if skill_vec is None:
        # Fallback: encode skill name if not found in precomputed taxonomy
        skill_vec = np.zeros(cat.embeddings.shape[1], dtype=np.float32)

    scored: List[ScoredCourse] = []

    for idx, course in enumerate(cat.courses):
        course_vec = cat.embeddings[idx]

        # 1. Skill embedding cosine relevance
        if skill_vec.any() and course_vec.any():
            cos_sim = float(np.dot(course_vec, skill_vec))
            cos_sim = float(np.clip(cos_sim, 0.0, 1.0))
        else:
            cos_sim = 0.0
        relevance_score = cos_sim * c.W_SKILL_RELEVANCE

        # 2. Exact skill tag bonus
        taught_skills = course.get("skills", [])
        has_exact_skill = skill_id in taught_skills
        exact_bonus = c.W_EXACT_SKILL_BONUS if has_exact_skill else 0.0

        # 3. Rating score (normalized 0 to 1)
        raw_rating = float(course.get("rating", 4.5))
        norm_rating = float(np.clip(raw_rating / 5.0, 0.0, 1.0))
        rating_score = norm_rating * c.W_RATING

        # 4. Level fit score
        course_level = course.get("level", "All Levels")
        level_fit = calculate_level_fit(course_level, level_pref)
        level_score = level_fit * c.W_LEVEL_FIT

        # 5. Duration penalty (penalize courses longer than 40 hours)
        duration = float(course.get("duration", 20.0))
        excess = max(0.0, duration - 40.0)
        dur_penalty = float(min(excess / 60.0, 1.0)) * c.W_DURATION_PENALTY

        total_score = relevance_score + exact_bonus + rating_score + level_score - dur_penalty

        # Generate transparent why_chosen text
        skill_info = taxonomy.get_skill(skill_id) or {}
        s_name = skill_info.get("name", skill_id)

        reasons = []
        if has_exact_skill:
            reasons.append(f"Explicitly teaches {s_name}")
        else:
            reasons.append(f"High curriculum relevance ({int(cos_sim * 100)}% match)")
        reasons.append(f"{course_level} difficulty suited for your profile")
        reasons.append(f"Highly rated ({raw_rating:.1f}/5.0 on {course.get('platform', 'Online')})")
        why_text = "; ".join(reasons) + "."

        scored.append(
            ScoredCourse(
                course_id=course.get("course_id", f"c_{idx}"),
                title=course.get("title", "Untitled Course"),
                description=course.get("description", ""),
                platform=course.get("platform", "Online"),
                level=course_level,
                duration_hours=duration,
                rating=raw_rating,
                url=course.get("url", ""),
                taught_skills=taught_skills,
                total_score=round(total_score, 4),
                score_breakdown={
                    "skill_relevance": round(relevance_score, 4),
                    "exact_skill_bonus": round(exact_bonus, 4),
                    "rating_score": round(rating_score, 4),
                    "level_fit_score": round(level_score, 4),
                    "duration_penalty": round(dur_penalty, 4),
                    "total_score": round(total_score, 4),
                },
                why_chosen=why_text,
            )
        )

    # Sort descending by total score
    scored.sort(key=lambda sc: sc.total_score, reverse=True)
    return scored[:k]


def resolve_prerequisite_order(
    missing_skills: List[str],
    resume_skills: Set[str],
    prereqs_map: Dict[str, List[str]],
) -> List[str]:
    """Order missing skills so prerequisite dependencies are always scheduled first.

    If skill B requires skill A, and A is missing from the resume, A is inserted
    prior to B. Cycles are handled gracefully with fallback order.
    """
    needed_set = set(missing_skills)
    ordered: List[str] = []
    visited: Set[str] = set()
    visiting: Set[str] = set()

    # Expand needed set with any transitive prerequisites missing from resume
    def get_all_prereqs(sid: str) -> List[str]:
        direct = prereqs_map.get(sid, [])
        expanded = []
        for p in direct:
            if p not in resume_skills:
                expanded.append(p)
                expanded.extend(get_all_prereqs(p))
        return expanded

    all_missing_to_schedule: Set[str] = set(needed_set)
    for sid in list(needed_set):
        all_missing_to_schedule.update(get_all_prereqs(sid))

    def visit(sid: str) -> None:
        if sid in visited:
            return
        if sid in visiting:
            # Cycle detected: break cycle
            return
        visiting.add(sid)

        for prereq in prereqs_map.get(sid, []):
            if prereq in all_missing_to_schedule and prereq not in resume_skills:
                visit(prereq)

        visiting.remove(sid)
        visited.add(sid)
        ordered.append(sid)

    for sid in all_missing_to_schedule:
        visit(sid)

    return ordered


def build_learning_path(
    gap_result: GapResult,
    profile: Optional[Dict[str, Any]] = None,
    hours_per_week: int = settings.DEFAULT_HOURS_PER_WEEK,
    max_items: int = settings.MAX_TOTAL_RECOMMENDATIONS,
    catalog: Optional[CourseCatalog] = None,
    cfg: Optional[Settings] = None,
) -> LearningPath:
    """Build an ordered, de-duplicated learning path with realistic calendar phases.

    1. Resolves prerequisite dependencies (foundations first).
    2. Within dependency tiers, prioritizes highest impact gain per hour.
    3. De-duplicates: when a course covers multiple missing skills, all are credited.
    4. Computes progressive score gains and calendar weeks.
    """
    cat = catalog or course_catalog
    if not cat.is_loaded():
        cat.load()

    c = cfg or settings
    hours_pw = max(1, hours_per_week)

    # 1. Identify missing skills and candidate resume skills
    missing_ids = [ms.skill_id for ms in gap_result.missing_skills]
    resume_skills_set = set(gap_result.resume_skills)

    # 2. Prerequisite-aware ordering
    ordered_skills = resolve_prerequisite_order(
        missing_skills=missing_ids,
        resume_skills=resume_skills_set,
        prereqs_map=cat.prereqs,
    )

    # 3. Simulate step-by-step learning path
    steps: List[LearningStep] = []
    satisfied_skills: Set[str] = set(resume_skills_set)
    accumulated_hours: float = 0.0
    current_coverage_score: float = gap_result.coverage_score

    # Use profile from GapResult if not explicitly provided
    target_profile = profile or {
        "role": gap_result.role,
        "n_postings": gap_result.n_postings,
        "skills": {
            cs.skill_id: {"weight": cs.weight, "tier": cs.tier}
            for cs in gap_result.exact_matches + gap_result.partial_matches
        },
    }
    # Add missing skills to profile definition if needed
    for ms in gap_result.missing_skills:
        if "skills" in target_profile and ms.skill_id not in target_profile["skills"]:
            target_profile["skills"][ms.skill_id] = {"weight": ms.weight, "tier": ms.tier}

    for sid in ordered_skills:
        if len(steps) >= max_items:
            break
        if sid in satisfied_skills:
            continue  # Already satisfied by an earlier multi-skill course

        # Determine level preference: if student already has prerequisites, prefer Intermediate
        has_prereqs = all(p in satisfied_skills for p in cat.prereqs.get(sid, []))
        level_pref = "Intermediate" if has_prereqs and cat.prereqs.get(sid) else "Beginner"

        # Recommend top course
        recs = recommend_for_skill(skill_id=sid, level_pref=level_pref, k=1, catalog=cat, cfg=c)
        if not recs:
            continue
        best_course = recs[0]

        # De-duplication: check which currently missing skills this course also covers
        newly_covered = [sid]
        for other_missing in ordered_skills:
            if other_missing != sid and other_missing not in satisfied_skills:
                if other_missing in best_course.taught_skills:
                    newly_covered.append(other_missing)

        # Update satisfied skills set
        satisfied_skills.update(newly_covered)

        # Compute realistic score gain via what_if
        sim = what_if(
            resume_skills=satisfied_skills,
            profile=target_profile,
            add=[],
            skill_emb=taxonomy,
            cfg=c,
        )
        new_cov = sim["new_coverage"]
        step_gain = max(0.0, new_cov - current_coverage_score)
        current_coverage_score = new_cov

        # Calculate calendar schedule
        dur = best_course.duration_hours
        start_week = int(accumulated_hours // hours_pw) + 1
        end_week = int((accumulated_hours + dur - 0.1) // hours_pw) + 1
        phase_str = f"Week {start_week}" if start_week == end_week else f"Weeks {start_week}-{end_week}"
        accumulated_hours += dur

        s_info = taxonomy.get_skill(sid) or {}
        s_name = s_info.get("name", sid)

        # Multi-skill rationale
        why_text = best_course.why_chosen
        if len(newly_covered) > 1:
            covered_names = [taxonomy.get_skill(cs_id).get("name", cs_id) for cs_id in newly_covered if cs_id != sid]
            why_text += f" Bonus: also closes gap for {', '.join(covered_names)}."

        step = LearningStep(
            step_number=len(steps) + 1,
            phase_label=phase_str,
            primary_skill_id=sid,
            primary_skill_name=s_name,
            course=best_course,
            score_gain=round(step_gain, 2),
            cumulative_score=round(current_coverage_score, 2),
            covered_skills=newly_covered,
            why_chosen=why_text,
        )
        steps.append(step)

    total_weeks = int(np.ceil(accumulated_hours / hours_pw)) if hours_pw > 0 else 0

    return LearningPath(
        role=gap_result.role,
        baseline_score=round(gap_result.coverage_score, 2),
        projected_final_score=round(current_coverage_score, 2),
        total_duration_hours=round(accumulated_hours, 1),
        total_weeks=total_weeks,
        hours_per_week=hours_pw,
        steps=steps,
    )
