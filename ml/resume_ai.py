"""Resume AI Writing Assistant and Optimization Engine for SkillGap.

Provides faithful, grounded writing assistance with zero hallucination leakage:
- improve_bullet: Rewrites bullets with strong action verbs and zero invented facts.
- draft_summary: Generates 2-3 sentence summaries strictly from verified resume data.
- polish_project: Converts project notes into impact bullets without new tools.
- suggest_skills_from_text: Deterministically extracts skills from text not yet selected.
- tailor: Reuses gap analyzer to evaluate role fit without mutates the candidate's resume.

Operates with local SLM (Ollama) when enabled/healthy, with full rule-based fallback.
All results cached in-memory only (zero disk persistence, zero logging of content).
"""

from __future__ import annotations

import hashlib
import json
import logging
import re
import time
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from config import settings
from ml.explain import rank_gaps_by_impact
from ml.extract import extract_skills
from ml.match import GapResult, gap_analysis
from ml.profiles import parse_job_description, role_manager
from ml.resume_ai_rules import (
    draft_summary_rules,
    improve_bullet_rules,
    polish_project_rules,
)
from ml.resume_ai_validate import validate_bullet, validate_summary
from ml.resume_schema import Resume
from ml.slm import ollama_client
from ml.taxonomy import taxonomy

logger = logging.getLogger(__name__)

# Strictly in-memory cache with size limit (max 500) and expiry (1 hour TTL)
_IN_MEMORY_AI_CACHE: Dict[str, Tuple[float, Any]] = {}
MAX_CACHE_SIZE = 500
CACHE_TTL_SECONDS = 3600.0


def _cache_get(key: str) -> Optional[Any]:
    """Retrieve value from cache if not expired."""
    now = time.time()
    if key in _IN_MEMORY_AI_CACHE:
        ts, val = _IN_MEMORY_AI_CACHE[key]
        if now - ts < CACHE_TTL_SECONDS:
            return val
        del _IN_MEMORY_AI_CACHE[key]
    return None


def _cache_set(key: str, val: Any) -> None:
    """Store value in cache with eviction when size exceeds limit."""
    now = time.time()
    if len(_IN_MEMORY_AI_CACHE) >= MAX_CACHE_SIZE:
        oldest_k = min(_IN_MEMORY_AI_CACHE.keys(), key=lambda k: _IN_MEMORY_AI_CACHE[k][0])
        del _IN_MEMORY_AI_CACHE[oldest_k]
    _IN_MEMORY_AI_CACHE[key] = (now, val)


def _cache_key(prefix: str, data: Any) -> str:
    """Generate SHA256 content hash key."""
    serialized = json.dumps(data, sort_keys=True, default=str)
    h = hashlib.sha256(serialized.encode("utf-8")).hexdigest()
    return f"{prefix}:{h}"


def _clean_slm_text(text: str) -> str:
    """Strip surrounding quotes, markdown fences, and bullet markers."""
    clean = text.strip()
    clean = re.sub(r"^```[a-zA-Z]*\n?", "", clean)
    clean = re.sub(r"\n?```$", "", clean)
    clean = clean.strip()
    clean = re.sub(r"^[\"']|[\"']$", "", clean)
    clean = re.sub(r"^[-*•–\d.]+\s*", "", clean)
    return clean.strip()


def improve_bullet(
    text: str,
    context: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    """Improve bullet point into strong ATS variants.

    Tries SLM if available and strictly validates; falls back to rules.
    """
    context = context or {}
    key = _cache_key("bullet", {"text": text, "context": context, "use_slm": settings.USE_SLM})
    cached = _cache_get(key)
    if cached is not None:
        return cached

    clean_orig = text.strip()
    is_current = context.get("current", False)
    role = context.get("role") or context.get("title") or "Software Engineer"
    org = context.get("company") or context.get("project") or ""
    skills = context.get("selected_skills") or []
    skills_str = ", ".join(skills[:5]) if skills else ""

    # Check if SLM is enabled and responding
    if settings.USE_SLM and ollama_client.is_enabled_and_ready():
        tense_guide = "present-tense" if is_current else "past-tense"
        system_prompt = (
            "You are a professional ATS resume assistant. "
            "Your task is to rewrite a resume bullet to maximize clarity and impact. "
            "STRICT RULES: "
            f"1. Start with a strong {tense_guide} action verb. "
            "2. Keep EVERY fact, number, and tool from the source text. "
            "3. Add NO new facts, numbers, tools, technologies, or outcomes. "
            "4. Do NOT use first-person pronouns (I, me, my, we, our). "
            "5. Exactly ONE sentence, 12 to 30 words, plain professional language. "
            "6. Output ONLY the rewritten bullet point with no conversational filler."
        )

        user_prompt = (
            f"Rewrite this bullet:\n'{clean_orig}'\n"
            f"Context: Role: {role}, Organization: {org}, Allowed Tools: {skills_str}"
        )

        # Attempt 1: Standard generation (zero disk cache)
        raw_resp = ollama_client.generate(
            prompt=user_prompt, system_prompt=system_prompt, cache_on_disk=False
        )
        candidate = _clean_slm_text(raw_resp or "")
        is_valid, checks, failures = validate_bullet(candidate, clean_orig, context)

        # Attempt 2: Stricter retry if validation failed
        if not is_valid:
            stricter_prompt = (
                f"PREVIOUS ATTEMPT FAILED VALIDATION: {'; '.join(failures)}.\n"
                f"Rewrite this bullet strictly using ONLY words and facts from the source:\n'{clean_orig}'\n"
                f"Do NOT invent any numbers or tools. Start with an action verb."
            )
            retry_resp = ollama_client.generate(
                prompt=stricter_prompt, system_prompt=system_prompt, cache_on_disk=False
            )
            retry_candidate = _clean_slm_text(retry_resp or "")
            retry_valid, retry_checks, _ = validate_bullet(retry_candidate, clean_orig, context)

            if retry_valid:
                candidate = retry_candidate
                checks = retry_checks
                is_valid = True

        if is_valid:
            result = {
                "source": "slm",
                "status": "Enhanced using local SLM with faithfulness verification.",
                "variants": [
                    {
                        "text": candidate.rstrip(".") + ".",
                        "changes": ["Synthesized into concise action-driven statement."],
                        "checks": checks,
                    }
                ],
            }
            _cache_set(key, result)
            return result

    # Rule-based fallback if SLM disabled, offline, or failed validation
    result = improve_bullet_rules(clean_orig, context)
    _cache_set(key, result)
    return result


def draft_summary(
    resume: Union[Resume, Dict[str, Any]],
) -> Dict[str, Any]:
    """Draft professional summary variants strictly grounded in resume facts."""
    data = resume.model_dump() if isinstance(resume, Resume) else resume
    key = _cache_key("summary", {"data": data, "use_slm": settings.USE_SLM})
    cached = _cache_get(key)
    if cached is not None:
        return cached

    if settings.USE_SLM and ollama_client.is_enabled_and_ready():
        # Build concise facts summary
        role = data.get("meta", {}).get("target_role") or data.get("basics", {}).get("headline") or "Software Professional"
        skills = [s.get("name") for s in data.get("skills", []) if isinstance(s, dict)]
        exp_titles = [e.get("title") for e in data.get("experience", []) if e.get("title")]

        system_prompt = (
            "You are a resume writing assistant. Write a 2-3 sentence executive professional summary. "
            "STRICT RULES: Use ONLY the provided role, skills, and background. "
            "Never invent facts, metrics, or technologies. No first-person pronouns. Plain English."
        )
        prompt = (
            f"Candidate Role: {role}\n"
            f"Verified Skills: {', '.join(skills[:8])}\n"
            f"Experience Titles: {', '.join(exp_titles[:3])}\n"
            "Generate a 2-3 sentence professional summary."
        )
        raw_resp = ollama_client.generate(
            prompt=prompt, system_prompt=system_prompt, cache_on_disk=False
        )
        candidate = _clean_slm_text(raw_resp or "")
        is_valid, checks, _ = validate_summary(candidate, data)

        if is_valid:
            result = {
                "source": "slm",
                "status": "Generated summary via verified SLM synthesis.",
                "variants": [{"text": candidate, "checks": checks}],
            }
            _cache_set(key, result)
            return result

    # Fallback to rules
    result = draft_summary_rules(data)
    _cache_set(key, result)
    return result


def polish_project(
    name: str,
    tech: List[str],
    notes: str,
) -> Dict[str, Any]:
    """Polish raw project notes into up to 2 concise impact bullets."""
    key = _cache_key("project", {"name": name, "tech": tech, "notes": notes, "use_slm": settings.USE_SLM})
    cached = _cache_get(key)
    if cached is not None:
        return cached

    if settings.USE_SLM and ollama_client.is_enabled_and_ready():
        system_prompt = (
            "You are an engineering resume editor. Convert rough project notes into 1 or 2 bullet points. "
            "STRICT RULES: Use ONLY the technologies and actions explicitly mentioned. "
            "Start with an action verb. Do not invent numbers or tools. No first person. Max 30 words per bullet."
        )
        prompt = f"Project Name: {name}\nTechnologies: {', '.join(tech)}\nUser Notes:\n{notes}"
        raw_resp = ollama_client.generate(
            prompt=prompt, system_prompt=system_prompt, cache_on_disk=False
        )
        lines = [_clean_slm_text(l) for l in (raw_resp or "").split("\n") if _clean_slm_text(l)]
        valid_bullets = []
        for line in lines[:2]:
            ok, _, _ = validate_bullet(line, notes, {"tech": tech, "project": name})
            if ok:
                valid_bullets.append(line.rstrip(".") + ".")

        if valid_bullets:
            result = {
                "source": "slm",
                "status": "Polished project notes using verified SLM synthesis.",
                "bullets": valid_bullets,
            }
            _cache_set(key, result)
            return result

    result = polish_project_rules(name, tech, notes)
    _cache_set(key, result)
    return result


def suggest_skills_from_text(
    resume: Union[Resume, Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """Deterministically discover skills mentioned in text but not selected in skills list."""
    data = resume.model_dump() if isinstance(resume, Resume) else resume

    # Collect already selected skills
    selected_skills_set: Set[str] = set()
    for item in data.get("skills", []):
        if isinstance(item, dict):
            if item.get("taxonomy_id"):
                selected_skills_set.add(item["taxonomy_id"].lower())
            if item.get("name"):
                selected_skills_set.add(item["name"].lower())
        else:
            selected_skills_set.add(str(item).lower())

    # Build corpus from bullets and descriptions
    text_chunks: List[str] = []
    if data.get("summary"):
        text_chunks.append(data["summary"])
    for exp in data.get("experience", []):
        text_chunks.extend(exp.get("bullets", []))
    for proj in data.get("projects", []):
        text_chunks.extend(proj.get("bullets", []))
        text_chunks.extend(proj.get("tech", []))
    for cs in data.get("custom_sections", []):
        text_chunks.extend(cs.get("bullets", []))

    full_corpus = "\n".join(text_chunks)
    if not full_corpus.strip():
        return []

    # Extract skills using hybrid mode
    extracted = extract_skills(full_corpus, mode="hybrid")
    suggestions: List[Dict[str, Any]] = []

    for sid in extracted.skills:
        skill_info = taxonomy.get_skill(sid) or {}
        skill_name = skill_info.get("name", sid.replace("_", " ").title())
        canonical_id = sid.lower()

        # Check if already present in selected skills
        if canonical_id in selected_skills_set or skill_name.lower() in selected_skills_set:
            continue

        sentence = extracted.best_sentences.get(sid, "")
        cat_id = skill_info.get("category", "other_tools")

        suggestions.append({
            "skill_id": sid,
            "name": skill_name,
            "category_id": cat_id,
            "sentence": sentence,
        })

    return suggestions


def tailor(
    resume: Union[Resume, Dict[str, Any]],
    target: str,
) -> Dict[str, Any]:
    """Tailor resume against a target role or job description.

    Evaluates skill gap, computes what-if impact, and returns actionable gaps.
    NEVER mutates the input resume.
    """
    data = resume.model_dump() if isinstance(resume, Resume) else resume

    # 1. Combine selected skills and skills extracted from text
    candidate_skills: Set[str] = set()
    for s in data.get("skills", []):
        if isinstance(s, dict):
            tid = s.get("taxonomy_id")
            if tid:
                candidate_skills.add(tid.lower())
            else:
                candidate_skills.add(s.get("name", "").lower())
        else:
            candidate_skills.add(str(s).lower())

    text_parts: List[str] = []
    if data.get("summary"):
        text_parts.append(data["summary"])
    for exp in data.get("experience", []):
        text_parts.extend(exp.get("bullets", []))
    for proj in data.get("projects", []):
        text_parts.extend(proj.get("bullets", []))

    if text_parts:
        extracted = extract_skills("\n".join(text_parts), mode="baseline")
        for sid in extracted.skills:
            candidate_skills.add(sid.lower())

    # 2. Resolve Role Profile
    clean_target = target.strip()
    profile = role_manager.get_role_profile(clean_target)
    if profile is None:
        # Custom Job Description text
        profile = parse_job_description(clean_target)
        role_title = profile.get("role", "Target Role")
    else:
        role_title = clean_target

    # 3. Gap Analysis
    gap: GapResult = gap_analysis(candidate_skills, profile, skill_emb=taxonomy)

    # 4. What-if Ranking of Missing Skills
    ranked_gaps = rank_gaps_by_impact(gap, profile, skill_emb=taxonomy)

    covered_list = [
        {
            "skill": cs.name,
            "skill_id": cs.skill_id,
            "tier": cs.tier,
            "match_type": cs.match_type,
            "similarity": cs.similarity,
        }
        for cs in gap.exact_matches + gap.partial_matches
    ]

    missing_list = [
        {
            "skill": g.skill_name,
            "skill_id": g.skill_id,
            "tier": g.tier,
            "weight": g.weight,
            "potential_gain": g.score_gain,
            "suggestion_prompt": f"If you have experience with {g.skill_name}, consider highlighting it in your resume.",
        }
        for g in ranked_gaps
    ]

    return {
        "target_role": role_title,
        "score": gap.final_score,
        "coverage_score": gap.coverage_score,
        "semantic_score": gap.semantic_score,
        "covered_skills": covered_list,
        "missing_skills": missing_list,
        "keyword_coverage": gap.coverage_score,
        "suggest_only": True,
    }
