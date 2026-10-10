"""Unit tests for skill extraction engine ml/extract.py."""

import pytest
import spacy

from ml.extract import (
    SkillExtractor,
    detect_sections,
    extract_baseline,
    extract_semantic,
    extract_skills,
    has_ambiguous_context,
)
from ml.taxonomy import taxonomy


@pytest.fixture(scope="module")
def extractor():
    """Ensure taxonomy is loaded and return extractor instance."""
    taxonomy.load()
    return SkillExtractor()


def test_section_detection():
    """Verify that section headers are identified and segmented correctly."""
    resume_text = (
        "John Doe\n\n"
        "TECHNICAL SKILLS\n"
        "Python, Docker, SQL\n\n"
        "PROFESSIONAL EXPERIENCE\n"
        "Senior Software Engineer at Tech Corp\n\n"
        "EDUCATION\n"
        "B.S. in Computer Science\n"
    )
    sections = detect_sections(resume_text)
    assert len(sections) >= 3

    sec_names = [s[2] for s in sections]
    assert "skills" in sec_names
    assert "experience" in sec_names
    assert "education" in sec_names


def test_ambiguous_skill_context_rule(extractor):
    """Verify context rule: ambiguous skills are accepted only with cue words or in skills section."""
    nlp = extractor.nlp

    # 1. In skills section -> ALWAYS ACCEPT
    doc_skills = nlp("C, Go, Rust, Swift")
    # For token 'C' (index 0) in 'skills' section:
    assert has_ambiguous_context(doc_skills, 0, 1, section="skills") is True

    # 2. Outside skills section WITH cue word ('programming', 'written in', 'developer', etc.) -> ACCEPT
    doc_with_cue = nlp("He is experienced in programming in C and Go.")
    # 'C' is token 6
    assert has_ambiguous_context(doc_with_cue, 6, 7, section="experience") is True

    # 3. Outside skills section WITHOUT cue word -> REJECT
    doc_no_cue = nlp("He took route C to get to the office.")
    # 'C' is token 3
    assert has_ambiguous_context(doc_no_cue, 3, 4, section="experience") is False

    # 4. Word / Excel without context -> REJECT
    doc_word_reject = nlp("A word of advice from the team.")
    assert has_ambiguous_context(doc_word_reject, 1, 2, section="other") is False

    # 5. Word with context -> ACCEPT
    doc_word_accept = nlp("Proficient in Microsoft Word and documentation.")
    assert has_ambiguous_context(doc_word_accept, 3, 4, section="experience") is True


def test_ambiguous_extraction_end_to_end():
    """End-to-end test verifying ambiguous skills are not falsely extracted from ordinary sentences."""
    # Ordinary English sentences using ambiguous terms colloquially
    noise_text = "There was a spark of hope. Take route C. In other words, we must go."
    res = extract_skills(noise_text, mode="baseline")
    assert "c" not in res.skills
    assert "spark" not in res.skills
    assert "go" not in res.skills

    # Technical sentences with context
    tech_text = "Proficient in C programming and Apache Spark for data engineering."
    res_tech = extract_skills(tech_text, mode="baseline")
    assert "c" in res_tech.skills
    assert "apache_spark" in res_tech.skills


def test_longest_match_resolution():
    """Verify that longest matches take precedence over substring matches."""
    text = "We specialize in Machine Learning and Natural Language Processing pipelines."
    res = extract_skills(text, mode="baseline")

    assert "machine_learning" in res.skills
    assert "natural_language_processing" in res.skills


def test_alias_resolution():
    """Verify that aliases resolve to their canonical skill IDs."""
    text = "Core stack: js, ts, k8s, postgres, and py."
    res = extract_skills(text, mode="baseline")

    # Canonical skill IDs expected
    assert "javascript" in res.skills
    assert "typescript" in res.skills
    assert "kubernetes" in res.skills
    assert "postgresql" in res.skills
    assert "python" in res.skills


def test_no_crash_on_empty_text():
    """Verify that empty, None-like, or whitespace strings handle gracefully without crashing."""
    assert extract_baseline("") == []
    assert extract_baseline("   \n\t  ") == []
    assert extract_semantic("") == []

    res = extract_skills("", mode="baseline")
    assert res.skills == []
    assert res.hits == []
    assert res.best_sentences == {}

    res_hybrid = extract_skills("   \n\t  ", mode="hybrid")
    assert res_hybrid.skills == []


def test_hybrid_mode_superset_of_baseline():
    """Verify that hybrid mode captures at least all baseline hits."""
    text = "SKILLS\nPython, Docker, React, FastAPI, SQL"
    res_baseline = extract_skills(text, mode="baseline")
    res_hybrid = extract_skills(text, mode="hybrid")

    for skill in res_baseline.skills:
        assert skill in res_hybrid.skills


def test_extraction_result_metadata():
    """Verify ExtractionResult contains confidence, best sentences, and hit lists."""
    text = (
        "EXPERIENCE\n"
        "Built responsive frontend dashboards with React and Redux.\n"
        "Deployed containerized services using Docker."
    )
    res = extract_skills(text, mode="baseline")

    assert "react" in res.skills
    assert "docker" in res.skills
    assert "react" in res.best_sentences
    assert "React" in res.best_sentences["react"]
    assert res.confidence_by_skill["react"] > 0.0

    serialized = res.to_dict()
    assert isinstance(serialized, dict)
    assert "skills" in serialized
    assert "best_sentences" in serialized
