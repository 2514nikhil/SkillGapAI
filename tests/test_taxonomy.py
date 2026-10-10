"""Unit tests for skills taxonomy and precomputed embeddings."""

import json
from pathlib import Path
import numpy as np
import pytest

from config import settings
from ml.taxonomy import (
    Taxonomy,
    is_ambiguous_skill,
    is_valid_skill_term,
    normalize_skill_name,
)


@pytest.fixture(scope="module")
def loaded_taxonomy():
    """Load taxonomy singleton once for module tests."""
    tax = Taxonomy()
    tax.load()
    return tax


def test_taxonomy_files_exist():
    """Verify that skills.json, skill_embeddings.npy, and skill_ids.json exist on disk."""
    assert settings.SKILLS_FILE.is_file(), f"Missing {settings.SKILLS_FILE}"
    assert settings.SKILL_EMBEDDINGS_FILE.is_file(), f"Missing {settings.SKILL_EMBEDDINGS_FILE}"
    assert settings.SKILL_IDS_FILE.is_file(), f"Missing {settings.SKILL_IDS_FILE}"


def test_skills_json_structure(loaded_taxonomy):
    """Verify that every entry in skills.json conforms to the required schema."""
    skills = loaded_taxonomy.skills
    assert len(skills) > 0

    for skill_id, data in skills.items():
        assert isinstance(skill_id, str) and len(skill_id) > 0
        assert "name" in data and isinstance(data["name"], str) and len(data["name"].strip()) > 0
        assert "category" in data and data["category"] in settings.SKILL_CATEGORIES
        assert "aliases" in data and isinstance(data["aliases"], list)
        assert "ambiguous" in data and isinstance(data["ambiguous"], bool)

        # Names should not exceed 5 words
        assert len(data["name"].split()) <= 5


def test_no_duplicate_aliases_across_skills(loaded_taxonomy):
    """Verify that no alias is shared between multiple skills or collides with canonical names."""
    skills = loaded_taxonomy.skills
    seen_aliases: dict[str, str] = {}
    canonical_names = {normalize_skill_name(s["name"]): sid for sid, s in skills.items()}

    for skill_id, data in skills.items():
        for alias in data.get("aliases", []):
            norm_alias = normalize_skill_name(alias)
            # Alias should not collide with another skill's canonical name
            if norm_alias in canonical_names and canonical_names[norm_alias] != skill_id:
                pytest.fail(
                    f"Alias '{norm_alias}' of skill '{skill_id}' collides with canonical name of '{canonical_names[norm_alias]}'"
                )

            # Alias should not be registered to another skill
            if norm_alias in seen_aliases:
                pytest.fail(
                    f"Duplicate alias '{norm_alias}' found in '{skill_id}' and '{seen_aliases[norm_alias]}'"
                )
            seen_aliases[norm_alias] = skill_id


def test_ambiguous_flags(loaded_taxonomy):
    """Verify that ambiguous short/polysemous skills are flagged correctly."""
    skills = loaded_taxonomy.skills

    # Must be ambiguous
    expected_ambiguous = ["c", "r", "go", "swift", "rust", "spark", "word", "excel"]
    for term in expected_ambiguous:
        sid = loaded_taxonomy.find_skill_id(term)
        assert sid is not None, f"Expected ambiguous skill '{term}' to exist in taxonomy"
        assert skills[sid]["ambiguous"] is True, f"Expected '{term}' to have ambiguous=True"

    # Must NOT be ambiguous
    expected_unambiguous = ["python", "kubernetes", "postgresql", "fastapi", "machine learning"]
    for term in expected_unambiguous:
        sid = loaded_taxonomy.find_skill_id(term)
        assert sid is not None, f"Expected skill '{term}' to exist in taxonomy"
        assert skills[sid]["ambiguous"] is False, f"Expected '{term}' to have ambiguous=False"


def test_embeddings_shape_and_normalization(loaded_taxonomy):
    """Verify embeddings shape (N, 384) and L2 normalization."""
    embeddings = loaded_taxonomy.embeddings
    skill_ids = loaded_taxonomy.skill_ids
    skills = loaded_taxonomy.skills

    num_skills = len(skills)
    assert embeddings.shape == (num_skills, 384), f"Unexpected shape {embeddings.shape}"
    assert len(skill_ids) == num_skills

    # Every embedding vector must have L2 norm close to 1.0
    norms = np.linalg.norm(embeddings, axis=1)
    np.testing.assert_allclose(norms, 1.0, atol=1e-3)


def test_nearest_neighbors_semantic_coherence(loaded_taxonomy):
    """Verify nearest neighbor search produces relevant skills."""
    # PyTorch top neighbors should contain deep learning / ML frameworks
    pt_neighbors = [name for name, score in loaded_taxonomy.find_nearest_skills("pytorch", top_k=10)]
    assert any(term in pt_neighbors for term in ["TensorFlow", "Keras", "Deep Learning", "scikit-learn"])

    # SQL top neighbors should contain database/query tools
    sql_neighbors = [name for name, score in loaded_taxonomy.find_nearest_skills("sql", top_k=10)]
    assert any(term in sql_neighbors for term in ["T-SQL", "PL/SQL", "MySQL", "PostgreSQL", "Microsoft SQL Server"])


def test_taxonomy_helper_methods(loaded_taxonomy):
    """Verify category filtering and alias resolution."""
    ml_skills = loaded_taxonomy.get_by_category("ml")
    assert len(ml_skills) > 0
    assert any(s["name"] == "Machine Learning" for s in ml_skills)

    # Alias lookup
    assert loaded_taxonomy.find_skill_id("py") == "python"
    assert loaded_taxonomy.find_skill_id("golang") == "go"
    assert loaded_taxonomy.find_skill_id("k8s") == "kubernetes"
    assert loaded_taxonomy.find_skill_id("non_existent_random_term_xyz") is None


def test_skill_term_validation():
    """Verify is_valid_skill_term and normalize_skill_name edge cases."""
    assert is_valid_skill_term("Python") is True
    assert is_valid_skill_term("C++") is True
    assert is_valid_skill_term("Node.js") is True
    # Too long (> 5 words)
    assert is_valid_skill_term("this is an absurdly long phrase that cannot possibly be a skill name") is False
    # Generic stop words
    assert is_valid_skill_term("team") is False
    assert is_valid_skill_term("work") is False
    assert is_valid_skill_term("") is False
