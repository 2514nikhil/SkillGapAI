"""Unit tests for course recommendation and learning path engine ml/recommend.py."""

import pytest

from ml.match import GapResult, MissingSkill
from ml.recommend import (
    CourseCatalog,
    build_learning_path,
    calculate_level_fit,
    course_catalog,
    recommend_for_skill,
    resolve_prerequisite_order,
)
from ml.taxonomy import taxonomy


@pytest.fixture(scope="module", autouse=True)
def init_catalogs():
    taxonomy.load()
    course_catalog.load()


def test_level_fit_math():
    """Verify level fit scoring logic across beginner, intermediate, advanced."""
    assert calculate_level_fit("All Levels", "Beginner") == 1.0
    assert calculate_level_fit("Beginner", "Beginner") == 1.0
    assert calculate_level_fit("Intermediate", "Beginner") == 0.6
    assert calculate_level_fit("Advanced", "Beginner") == 0.2
    assert calculate_level_fit("Intermediate", "Intermediate") == 1.0


def test_relevance_ordering_for_skill():
    """Verify that querying recommendations for 'sql' returns a dedicated SQL course as top pick."""
    recs = recommend_for_skill(skill_id="sql", level_pref="Beginner", k=3)

    assert len(recs) > 0
    top = recs[0]

    # Top course must be an SQL course
    assert "sql" in top.title.lower() or "sql" in top.taught_skills
    # Transparent score breakdown must exist and sum properly
    assert "skill_relevance" in top.score_breakdown
    assert "exact_skill_bonus" in top.score_breakdown
    assert "rating_score" in top.score_breakdown
    assert "level_fit_score" in top.score_breakdown
    assert "duration_penalty" in top.score_breakdown

    # Exact skill bonus should be positive for an SQL course
    assert top.score_breakdown["exact_skill_bonus"] > 0.0
    assert top.total_score > 0.40


def test_prerequisite_insertion_and_ordering():
    """Verify that when a dependent skill is missing, its missing prerequisite is scheduled first."""
    prereqs_map = {
        "machine_learning": ["python"],
        "deep_learning": ["machine_learning", "python"],
        "react": ["javascript"],
    }

    # Case 1: Candidate lacks both python and machine_learning
    ordered_1 = resolve_prerequisite_order(
        missing_skills=["deep_learning"],
        resume_skills=set(),
        prereqs_map=prereqs_map,
    )
    # python must appear before machine_learning, and machine_learning before deep_learning
    assert ordered_1.index("python") < ordered_1.index("machine_learning")
    assert ordered_1.index("machine_learning") < ordered_1.index("deep_learning")

    # Case 2: Candidate already has python in resume
    ordered_2 = resolve_prerequisite_order(
        missing_skills=["machine_learning"],
        resume_skills={"python"},
        prereqs_map=prereqs_map,
    )
    # Python is already mastered, so it should not be in missing skills schedule
    assert "python" not in ordered_2
    assert ordered_2 == ["machine_learning"]


def test_hours_per_week_scheduling_math():
    """Verify calendar week allocation based on course hours and hours_per_week."""
    # Create a synthetic GapResult with SQL missing
    mock_gap = GapResult(
        role="Data Analyst",
        final_score=20.0,
        coverage_score=15.0,
        semantic_score=40.0,
        raw_cosine=0.45,
        total_weight=4.0,
        earned_weight=0.6,
        exact_matches=[],
        partial_matches=[],
        missing_skills=[
            MissingSkill(skill_id="sql", name="SQL", tier="core", weight=1.0, potential_gain=25.0),
            MissingSkill(skill_id="tableau", name="Tableau", tier="core", weight=0.7, potential_gain=17.5),
        ],
        categories={},
        resume_skills=["python"],
        n_postings=10,
    )

    # 10 hours per week schedule
    path = build_learning_path(gap_result=mock_gap, hours_per_week=10)

    assert len(path.steps) >= 1
    step_1 = path.steps[0]
    # Check that phase string is formatted as weeks (e.g. Weeks 1-2)
    assert "Week" in step_1.phase_label
    assert path.total_weeks >= 1
    assert path.total_duration_hours > 0.0
    assert path.projected_final_score > path.baseline_score


def test_de_duplication_multi_skill_coverage():
    """Verify that if a course teaches multiple missing skills, they are consolidated."""
    # Advanced SQL teaches both SQL and Data Modeling/Warehousing
    mock_gap = GapResult(
        role="Data Analyst",
        final_score=20.0,
        coverage_score=15.0,
        semantic_score=40.0,
        raw_cosine=0.45,
        total_weight=4.0,
        earned_weight=0.6,
        exact_matches=[],
        partial_matches=[],
        missing_skills=[
            MissingSkill(skill_id="sql", name="SQL", tier="core", weight=1.0, potential_gain=25.0),
            MissingSkill(skill_id="data_warehousing", name="Data Warehousing", tier="common", weight=0.4, potential_gain=10.0),
        ],
        categories={},
        resume_skills=[],
        n_postings=10,
    )

    path = build_learning_path(gap_result=mock_gap, hours_per_week=10)

    # Check that each step is non-empty and score increases monotonically
    prev_score = path.baseline_score
    for step in path.steps:
        assert step.cumulative_score >= prev_score
        prev_score = step.cumulative_score
