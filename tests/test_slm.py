"""Unit tests for local SLM integration and validation ml/slm.py."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from config import settings
from ml.slm import (
    OllamaClient,
    extract_skills_slm,
    narrate_learning_path,
    verify_grounded_narration,
)
from ml.taxonomy import taxonomy


@pytest.fixture(scope="module", autouse=True)
def load_taxonomy():
    taxonomy.load()


def test_json_parsing_robustness():
    """Verify that JSON extraction handles clean JSON, markdown-wrapped JSON, and malformed text."""
    # 1. Mock client returning clean JSON
    mock_client = MagicMock(spec=OllamaClient)
    mock_client.is_enabled_and_ready.return_value = True

    mock_client.generate.return_value = '{"skills": ["React", "TypeScript"]}'
    res_clean = extract_skills_slm(
        text_chunk="Built user interfaces using React and TypeScript for web applications.",
        client=mock_client,
    )
    extracted_ids = [sid for sid, surface in res_clean]
    assert "react" in extracted_ids
    assert "typescript" in extracted_ids

    # 2. Mock client returning Markdown-wrapped JSON
    mock_client.generate.return_value = '```json\n{"skills": ["React"]}\n```'
    res_md = extract_skills_slm(
        text_chunk="Focused on modern React component architectures.",
        client=mock_client,
    )
    assert len(res_md) == 1
    assert res_md[0][0] == "react"

    # 3. Mock client returning completely invalid non-JSON
    mock_client.generate.return_value = "I found the following skills: Python, Docker."
    res_invalid = extract_skills_slm(
        text_chunk="Worked with Python and Docker on backend services.",
        client=mock_client,
    )
    # Malformed response safely discards without raising an exception
    assert res_invalid == []


def test_hallucination_rejection():
    """Verify that skills proposed by SLM that DO NOT appear in source text are rejected."""
    mock_client = MagicMock(spec=OllamaClient)
    mock_client.is_enabled_and_ready.return_value = True

    # Source text only mentions Python and PostgreSQL
    source_text = "Maintained relational database queries in PostgreSQL and scripted data pipelines with Python."

    # Hallucinating SLM returns Kubernetes, Deep Learning, and C++, plus genuine Python
    mock_client.generate.return_value = json.dumps({
        "skills": ["Python", "Kubernetes", "Deep Learning", "C++"]
    })

    res = extract_skills_slm(
        text_chunk=source_text,
        client=mock_client,
    )
    extracted_ids = [sid for sid, surface in res]

    # Only Python was physically present in the excerpt
    assert "python" in extracted_ids
    # Hallucinations MUST be dropped
    assert "kubernetes" not in extracted_ids
    assert "deep_learning" not in extracted_ids
    assert "c" not in extracted_ids


def test_fallback_when_ollama_is_down():
    """Verify system falls back silently without errors when Ollama is unreachable."""
    client = OllamaClient()
    # Force client to report unavailable
    client._is_available = False

    # 1. Extraction recovery returns empty list silently
    res = extract_skills_slm("Some technical excerpt with Python.", client=client)
    assert res == []

    # 2. Plan narration falls back to deterministic template
    sample_plan = {
        "role": "Data Analyst",
        "baseline_score": 25.0,
        "projected_final_score": 85.0,
        "total_weeks": 10,
        "hours_per_week": 10,
        "steps": [
            {
                "phase_label": "Weeks 1-2",
                "primary_skill_name": "SQL",
                "course": {"title": "SQL for Data Science"},
                "score_gain": 20.0,
            }
        ],
    }
    narrative = narrate_learning_path(sample_plan, client=client)
    assert "Data Analyst" in narrative
    assert "25.0%" in narrative
    assert "85.0%" in narrative
    assert "10 weeks" in narrative


def test_slm_caching(tmp_path):
    """Verify that repeated SLM calls write to and read from disk cache."""
    cache_dir = tmp_path / "slm_cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    client = OllamaClient()
    client.cfg = settings.model_copy(update={"USE_SLM": True})
    client.cache_dir = cache_dir
    client._is_available = True

    # First call: simulate network call
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_response = MagicMock()
        mock_response.status = 200
        mock_response.read.return_value = json.dumps({"response": '{"skills": ["SQL"]}'}).encode("utf-8")
        mock_urlopen.return_value.__enter__.return_value = mock_response

        text_1 = client.generate(prompt="Extract skills from text", format_json=True)
        assert text_1 == '{"skills": ["SQL"]}'
        assert mock_urlopen.call_count == 1

        # Second call with identical prompt: should read directly from disk cache without network call
        text_2 = client.generate(prompt="Extract skills from text", format_json=True)
        assert text_2 == '{"skills": ["SQL"]}'
        # Network call count should remain 1
        assert mock_urlopen.call_count == 1


def test_grounding_post_check_rejects_hallucinated_numbers():
    """Verify that narration fails verification if SLM hallucinates numbers not in input facts."""
    allowed_numbers = {"10", "20", "85", "85.0"}
    allowed_courses = {"sql for data science"}

    # Case 1: Valid grounded narration
    grounded_text = "In step 1, you will spend 10 hours learning SQL to gain 20 points."
    assert verify_grounded_narration(grounded_text, allowed_numbers | {"1"}, allowed_courses) is True

    # Case 2: Ungrounded hallucinated claim (e.g. 99.9% guarantee, 500 hours)
    hallucinated_text = "This course guarantees 99.9% match in 500 hours."
    assert verify_grounded_narration(hallucinated_text, allowed_numbers, allowed_courses) is False
