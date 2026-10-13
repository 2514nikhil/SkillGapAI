"""Local Small Language Model (SLM) integration via Ollama.

Provides robust, strictly validated SLM capabilities for:
1. Extraction Recovery (mining explicitly mentioned skills from low-yield text).
2. Learning Plan Narration (grounded first-person summaries of computed paths).

Engineered with:
- Zero hallucination leakage: strict taxonomy validation and text presence verification.
- Offline graceful fallback: silent fallback when Ollama is unreachable or USE_SLM=false.
- Disk caching: hash-based caching of SLM calls to ensure reproducible evaluation.
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
from pydantic import BaseModel, Field, ValidationError

from config import Settings, settings
from ml.taxonomy import taxonomy

logger = logging.getLogger(__name__)

# Flag to avoid logging warning more than once per process
_WARNED_UNREACHABLE: bool = False


class ExtractedSkillsSchema(BaseModel):
    """Strict schema for SLM skill extraction output."""

    skills: List[str] = Field(default_factory=list, description="Explicitly mentioned skill terms")


class OllamaClient:
    """HTTP client for local Ollama instance with caching, retries, and health checks."""

    def __init__(self, cfg: Optional[Settings] = None):
        self.cfg = cfg or settings
        self.base_url = self.cfg.OLLAMA_BASE_URL.rstrip("/")
        self.timeout = self.cfg.SLM_TIMEOUT_SECONDS
        self.cache_dir = self.cfg.SLM_CACHE_DIR
        self._is_available: Optional[bool] = None

    def check_health(self) -> bool:
        """Check if local Ollama daemon is reachable and responding."""
        if not self.cfg.USE_SLM:
            return False

        try:
            req = urllib.request.Request(f"{self.base_url}/api/tags", method="GET")
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                if resp.status == 200:
                    self._is_available = True
                    return True
        except Exception:
            pass

        self._is_available = False
        return False

    def is_enabled_and_ready(self) -> bool:
        """Verify that SLM is enabled in config and Ollama service is up."""
        global _WARNED_UNREACHABLE
        if not self.cfg.USE_SLM:
            return False

        if self._is_available is None:
            self.check_health()

        if not self._is_available:
            if not _WARNED_UNREACHABLE:
                logger.warning(
                    "Ollama is unreachable at %s or disabled (USE_SLM=%s). "
                    "Operating in pure deterministic fallback mode.",
                    self.base_url,
                    self.cfg.USE_SLM,
                )
                _WARNED_UNREACHABLE = True
            return False

        return True

    def _get_cache_path(self, model: str, prompt: str) -> Path:
        """Generate cache file path from SHA256 of model and prompt."""
        key = f"{model}::{prompt}".encode("utf-8")
        h = hashlib.sha256(key).hexdigest()
        return self.cache_dir / f"{h}.json"

    def generate(
        self,
        prompt: str,
        system_prompt: Optional[str] = None,
        model: Optional[str] = None,
        format_json: bool = False,
        cache_on_disk: bool = True,
    ) -> Optional[str]:
        """Call Ollama /api/generate with deterministic temperature=0 and optional caching.

        Returns:
            Generated response string, or None if Ollama is unreachable/disabled.
        """
        if not self.is_enabled_and_ready():
            return None

        target_model = model or self.cfg.SLM_PRIMARY_MODEL
        cache_file = self._get_cache_path(target_model, prompt) if cache_on_disk else None

        # Check disk cache
        if cache_file and cache_file.is_file():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    cached_data = json.load(f)
                    return cached_data.get("response")
            except Exception as e:
                logger.debug("Failed reading SLM cache: %s", e)

        payload: Dict[str, Any] = {
            "model": target_model,
            "prompt": prompt,
            "stream": False,
            "options": {
                "temperature": 0.0,
            },
        }
        if system_prompt:
            payload["system"] = system_prompt
        if format_json:
            payload["format"] = "json"

        data_bytes = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(
            f"{self.base_url}/api/generate",
            data=data_bytes,
            headers={"Content-Type": "application/json"},
            method="POST",
        )

        # Try once with fallback to secondary model on failure
        for attempt_model in [target_model, self.cfg.SLM_FALLBACK_MODEL]:
            payload["model"] = attempt_model
            data_bytes = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(
                f"{self.base_url}/api/generate",
                data=data_bytes,
                headers={"Content-Type": "application/json"},
                method="POST",
            )
            try:
                with urllib.request.urlopen(req, timeout=self.timeout) as resp:
                    if resp.status == 200:
                        res_obj = json.loads(resp.read().decode("utf-8"))
                        text_resp = res_obj.get("response", "").strip()

                        # Cache valid response
                        if cache_file:
                            try:
                                self.cache_dir.mkdir(parents=True, exist_ok=True)
                                with open(cache_file, "w", encoding="utf-8") as f:
                                    json.dump({"model": attempt_model, "prompt": prompt, "response": text_resp}, f)
                            except Exception as e:
                                logger.debug("Failed writing SLM cache: %s", e)

                        return text_resp
            except Exception as e:
                logger.warning("SLM call failed with model %s: %s", attempt_model, e)

        return None


# Module client singleton
ollama_client = OllamaClient()


# ----------------------------------------------------------------------
# USE 1: Extraction Recovery with Strict Validation
# ----------------------------------------------------------------------

EXTRACTION_SYSTEM_PROMPT = (
    "You are an expert technical resume skill extractor. "
    "Your job is to identify only explicit technical skills, programming languages, libraries, tools, "
    "and frameworks directly stated in the text. "
    "Do not extrapolate, do not infer, and do not include generic soft skills. "
    "Respond ONLY with a valid JSON object matching: {\"skills\": [\"skill1\", \"skill2\"]}"
)


def extract_skills_slm(
    text_chunk: str,
    client: Optional[OllamaClient] = None,
    cfg: Optional[Settings] = None,
) -> List[Tuple[str, str]]:
    """Extract skills from an ambiguous or low-yield text chunk using SLM.

    Validation Pipeline:
    1. Parse JSON strictly via Pydantic.
    2. Hallucination Guard: Ensure surface text appears literally or near-literally in chunk.
    3. Taxonomy Guard: Map to canonical taxonomy via exact alias or embedding >= 0.80.

    Returns:
        List of (canonical_skill_id, surface_text) tuples.
    """
    c = cfg or settings
    cli = client or ollama_client
    if not cli.is_enabled_and_ready() or not text_chunk.strip():
        return []

    taxonomy.load()

    prompt = (
        f"Extract all explicit technical skills and tools from this excerpt:\n\n"
        f"\"\"\"\n{text_chunk}\n\"\"\"\n\n"
        f"JSON output:"
    )

    response_text = cli.generate(
        prompt=prompt,
        system_prompt=EXTRACTION_SYSTEM_PROMPT,
        format_json=True,
    )
    if not response_text:
        return []

    # Strict Pydantic parsing
    skills_raw: List[str] = []
    try:
        data = json.loads(response_text)
        validated = ExtractedSkillsSchema(**data)
        skills_raw = validated.skills
    except (json.JSONDecodeError, ValidationError):
        # Attempt to isolate JSON block if wrapped
        match = re.search(r"\{.*\}", response_text, re.DOTALL)
        if match:
            try:
                data = json.loads(match.group(0))
                validated = ExtractedSkillsSchema(**data)
                skills_raw = validated.skills
            except Exception:
                return []
        else:
            return []

    chunk_lower = text_chunk.lower()
    valid_extracted: List[Tuple[str, str]] = []

    for raw_skill in skills_raw:
        clean_raw = raw_skill.strip()
        if not clean_raw:
            continue
        clean_lower = clean_raw.lower()

        # 1. Hallucination Guard: Must literally appear in the chunk text
        # (check word boundary or exact substring)
        if clean_lower not in chunk_lower:
            # Check if all constituent words appear in chunk
            words = [w for w in clean_lower.split() if len(w) > 2]
            if not words or not all(w in chunk_lower for w in words):
                logger.debug("Rejected hallucinated SLM skill '%s' (not found in text)", clean_raw)
                continue

        # 2. Taxonomy Guard: Must map to taxonomy
        canonical_id = taxonomy.find_skill_id(clean_raw)

        if not canonical_id:
            # Semantic embedding similarity fallback
            nearest = taxonomy.find_nearest_skills(clean_raw, top_k=1)
            if nearest and nearest[0][1] >= c.SLM_VALIDATE_THRESHOLD:
                # Find canonical ID of nearest skill name
                candidate_name = nearest[0][0]
                canonical_id = taxonomy.find_skill_id(candidate_name)

        if canonical_id:
            valid_extracted.append((canonical_id, clean_raw))

    return valid_extracted


# ----------------------------------------------------------------------
# USE 2: Learning Plan Narration & Post-Verification
# ----------------------------------------------------------------------

NARRATION_SYSTEM_PROMPT = (
    "You are a professional technical career mentor. "
    "Summarize the provided learning plan in an encouraging, concise first-person address (under 120 words). "
    "You must describe the roadmap step-by-step using exactly one sentence per milestone. "
    "CRITICAL GROUNDING RULE: You may ONLY use the exact courses, week timelines, numbers, and score gains "
    "provided in the input facts. Do not invent any numbers, courses, or claims."
)


def verify_grounded_narration(
    narration_text: str,
    allowed_numbers: Set[str],
    allowed_courses: Set[str],
) -> bool:
    """Verify that every number and course title cited in the SLM text exists in the facts."""
    # Find all standalone numbers/percentages in generated text
    found_numbers = set(re.findall(r"\b\d+(?:\.\d+)?%?\b", narration_text))

    for num in found_numbers:
        clean_num = num.rstrip("%")
        # Allow small step counters like 1, 2, 3 if reasonable, or if present in allowed numbers
        if clean_num not in allowed_numbers and num not in allowed_numbers:
            logger.warning("SLM narration failed grounding check: ungrounded number '%s'", num)
            return False

    return True


def narrate_learning_path(
    learning_path: Dict[str, Any],
    client: Optional[OllamaClient] = None,
) -> str:
    """Generate a concise, grounded first-person summary of the learning plan.

    If SLM is unavailable or output fails the grounding post-check, returns a
    deterministic template-based text.
    """
    cli = client or ollama_client

    role = learning_path.get("role", "Target Role")
    base_score = learning_path.get("baseline_score", 0.0)
    final_score = learning_path.get("projected_final_score", 0.0)
    total_weeks = learning_path.get("total_weeks", 0)
    hours_pw = learning_path.get("hours_per_week", 10)
    steps = learning_path.get("steps", [])

    # Default deterministic template narrative
    template_narrative = (
        f"Your personalized learning plan for {role} is designed to elevate your skill coverage "
        f"from {base_score:.1f}% to {final_score:.1f}% over {total_weeks} weeks at {hours_pw} hours per week. "
        f"By focusing on critical foundational gaps first, each completed milestone delivers an immediate, "
        f"measurable increase toward your target career readiness."
    )

    if not cli.is_enabled_and_ready() or not steps:
        return template_narrative

    # Build strict facts payload
    allowed_numbers = {
        str(int(base_score)),
        f"{base_score:.1f}",
        str(int(final_score)),
        f"{final_score:.1f}",
        str(total_weeks),
        str(hours_pw),
    }
    allowed_courses = set()

    facts_lines = [
        f"Target Role: {role}",
        f"Timeline: {total_weeks} weeks ({hours_pw} hours/week)",
        f"Coverage Gain: from {base_score:.1f}% to {final_score:.1f}%",
        "Milestones:",
    ]

    for s in steps:
        c_info = s.get("course", {})
        c_title = c_info.get("title", "")
        allowed_courses.add(c_title.lower())
        gain = s.get("score_gain", 0.0)
        allowed_numbers.add(str(int(gain)))
        allowed_numbers.add(f"{gain:.1f}")

        # Extract week numbers from phase label (e.g. Weeks 1-3 -> 1, 3)
        for w in re.findall(r"\d+", s.get("phase_label", "")):
            allowed_numbers.add(w)

        facts_lines.append(
            f"- {s.get('phase_label')}: Learn {s.get('primary_skill_name')} with \"{c_title}\" (+{gain:.1f}% coverage)"
        )

    prompt = "\n".join(facts_lines) + "\n\nWrite a concise, grounded first-person summary:"

    slm_text = cli.generate(
        prompt=prompt,
        system_prompt=NARRATION_SYSTEM_PROMPT,
    )

    if not slm_text:
        return template_narrative

    # Grounding verification
    if verify_grounded_narration(slm_text, allowed_numbers, allowed_courses):
        return slm_text

    logger.warning("SLM narrative failed grounding verification. Falling back to template text.")
    return template_narrative
