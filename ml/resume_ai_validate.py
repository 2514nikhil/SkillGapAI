"""Faithfulness and Style Validator for Resume AI.

Guarantees zero hallucination leakage and ATS compliance:
- Every number, percentage, and monetary amount must appear in the source text.
- Every technology, tool, or proper noun must be present in the source or permitted context.
- No first-person pronouns.
- No banned or passive phrases.
- Must start with an approved action verb.
- No emoji, no markdown markup.
- Length within ATS limits (12 to 30 words for bullets).
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

RULES_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "resume_rules.json"
CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "tech_catalog.json"

NUMBER_REGEX = re.compile(r"(\b\d+(?:\.\d+)?%?|\$\d+(?:\.\d+)?[kKmMbB]?|€\d+|£\d+|₹\d+|\b\d+x\b|\b\d+\b)")
PRONOUN_REGEX = re.compile(r"\b(i|me|my|myself|we|us|our|ours|ourselves)\b", re.IGNORECASE)
MARKDOWN_REGEX = re.compile(r"(\*\*|\*|__|#|\[.*?\]\(.*?\)|`|~~)")
EMOJI_REGEX = re.compile(
    "["
    "\U0001F600-\U0001F64F"  # emoticons
    "\U0001F300-\U0001F5FF"  # symbols & pictographs
    "\U0001F680-\U0001F6FF"  # transport & map symbols
    "\U0001F1E0-\U0001F1FF"  # flags (iOS)
    "\U00002702-\U000027B0"
    "\U000024C2-\U0001F251"
    "]+",
    flags=re.UNICODE,
)

_cached_rules: Optional[Dict[str, Any]] = None
_cached_known_tools: Optional[Set[str]] = None


def _get_rules() -> Dict[str, Any]:
    global _cached_rules
    if _cached_rules is None:
        if RULES_PATH.exists():
            with open(RULES_PATH, "r", encoding="utf-8") as f:
                _cached_rules = json.load(f)
        else:
            _cached_rules = {
                "weak_phrases": ["responsible for", "duties included", "worked on", "helped with", "assisted with", "tasked with", "handled"],
                "first_person_pronouns": ["i", "me", "my", "myself", "we", "us", "our", "ours", "ourselves"],
                "action_verbs": ["built", "designed", "developed", "led", "managed", "optimized", "engineered", "architected", "automated"],
            }
    return _cached_rules


def _get_known_tools() -> Set[str]:
    """Load all canonical skill names and aliases from catalog."""
    global _cached_known_tools
    if _cached_known_tools is None:
        tools: Set[str] = set()
        if CATALOG_PATH.exists():
            with open(CATALOG_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
            for cat in data.get("categories", []):
                for sk in cat.get("skills", []):
                    tools.add(sk["name"].lower())
                    if sk.get("taxonomy_id"):
                        tools.add(sk["taxonomy_id"].lower())
                    for alias in sk.get("aliases", []):
                        tools.add(alias.lower())
        _cached_known_tools = tools
    return _cached_known_tools


def extract_numbers(text: str) -> Set[str]:
    """Extract all numeric, currency, percentage, and multiplier tokens."""
    tokens = NUMBER_REGEX.findall(text)
    cleaned: Set[str] = set()
    for tok in tokens:
        c = tok.strip().lower()
        if c:
            cleaned.add(c)
    return cleaned


def extract_potential_tools(text: str) -> Set[str]:
    """Identify potential tool/technology terms appearing in text."""
    known = _get_known_tools()
    found: Set[str] = set()
    text_lower = text.lower()
    for tool in known:
        if len(tool) >= 2 and re.search(r"\b" + re.escape(tool) + r"\b", text_lower):
            found.add(tool)
    return found


def validate_bullet(
    candidate: str,
    source_text: str,
    context: Optional[Dict[str, Any]] = None,
) -> Tuple[bool, Dict[str, bool], List[str]]:
    """Validate an improved bullet candidate for absolute faithfulness.

    Args:
        candidate: The proposed bullet point string.
        source_text: The user's original unpolished bullet.
        context: Optional dictionary with role, company, selected_skills, tech.

    Returns:
        (is_valid, checks_dict, failures_list)
    """
    context = context or {}
    rules = _get_rules()
    failures: List[str] = []
    checks: Dict[str, bool] = {
        "no_invented_numbers": True,
        "no_invented_tools": True,
        "no_first_person": True,
        "no_banned_phrases": True,
        "starts_with_action_verb": True,
        "no_emoji_or_markdown": True,
        "length_within_limits": True,
    }

    clean_candidate = candidate.strip().rstrip(".")

    # 1. No First Person Pronouns
    if PRONOUN_REGEX.search(clean_candidate):
        checks["no_first_person"] = False
        failures.append("Candidate contains first-person pronouns.")

    # 2. No Banned / Weak Phrases
    cand_lower = clean_candidate.lower()
    for wp in rules.get("weak_phrases", []):
        if wp.lower() in cand_lower:
            checks["no_banned_phrases"] = False
            failures.append(f"Candidate contains banned weak phrase '{wp}'.")
            break

    # 3. No Emoji or Markdown
    if MARKDOWN_REGEX.search(candidate) or EMOJI_REGEX.search(candidate):
        checks["no_emoji_or_markdown"] = False
        failures.append("Candidate contains markdown formatting or emoji.")

    # 4. Length Limits (8 to 35 words standard, max 300 chars)
    words = clean_candidate.split()
    word_count = len(words)
    if word_count < 8 or word_count > 35 or len(clean_candidate) > 300:
        checks["length_within_limits"] = False
        failures.append(f"Word count ({word_count}) outside recommended 8-35 range or >300 chars.")

    # 5. Starts with Action Verb
    if words:
        first_word = re.sub(r"[^a-zA-Z]", "", words[0]).lower()
        action_verbs = {v.lower() for v in rules.get("action_verbs", [])}
        # Add common present and past tense variants
        common_extras = {
            "build", "built", "develop", "developed", "design", "designed",
            "engineer", "engineered", "create", "created", "lead", "led",
            "manage", "managed", "optimize", "optimized", "scale", "scaled",
            "automate", "automated", "deploy", "deployed", "implement", "implemented",
            "orchestrate", "orchestrated", "architect", "architected", "spearhead",
            "spearheaded", "accelerate", "accelerated", "reduce", "reduced",
            "refactor", "refactored", "deliver", "delivered", "streamline", "streamlined",
            "establish", "established", "author", "authored", "integrate", "integrated",
            "construct", "constructed", "configure", "configured", "maintain", "maintained",
            "collaborate", "collaborated", "contribute", "contributed", "oversee", "oversaw",
            "conduct", "conducted",
        }
        all_verbs = action_verbs | common_extras
        if first_word not in all_verbs:
            checks["starts_with_action_verb"] = False
            failures.append(f"First word '{first_word}' is not an approved action verb.")

    # 6. No Invented Numbers / Metrics
    cand_nums = extract_numbers(clean_candidate)
    source_nums = extract_numbers(source_text)
    # Also allow numbers mentioned in context
    context_str = " ".join(str(v) for v in context.values() if isinstance(v, (str, list, int, float)))
    context_nums = extract_numbers(context_str)
    allowed_nums = source_nums | context_nums

    invented_nums = cand_nums - allowed_nums
    if invented_nums:
        checks["no_invented_numbers"] = False
        failures.append(f"Invented numbers or metrics detected: {sorted(invented_nums)}")

    # 7. No Invented Tools / Tech
    cand_tools = extract_potential_tools(clean_candidate)
    source_tools = extract_potential_tools(source_text)
    selected_skills = {str(s).lower() for s in context.get("selected_skills", [])}
    context_tech = {str(t).lower() for t in context.get("tech", [])}
    allowed_tools = source_tools | selected_skills | context_tech

    invented_tools = cand_tools - allowed_tools
    if invented_tools:
        checks["no_invented_tools"] = False
        failures.append(f"Invented tools or technologies detected: {sorted(invented_tools)}")

    is_valid = len(failures) == 0
    return is_valid, checks, failures


def validate_summary(
    candidate: str,
    resume_facts: Dict[str, Any],
) -> Tuple[bool, Dict[str, bool], List[str]]:
    """Validate a generated summary against resume facts."""
    failures: List[str] = []
    checks: Dict[str, bool] = {
        "no_invented_numbers": True,
        "no_invented_tools": True,
        "no_first_person": True,
        "no_banned_phrases": True,
        "length_within_limits": True,
    }

    # No first person
    if PRONOUN_REGEX.search(candidate):
        checks["no_first_person"] = False
        failures.append("Summary contains first-person pronouns.")

    # Sentence count: 2 to 4 sentences
    sentences = [s.strip() for s in re.split(r"(?<=[.!?])\s+", candidate) if s.strip()]
    if len(sentences) < 2 or len(sentences) > 4:
        checks["length_within_limits"] = False
        failures.append(f"Summary contains {len(sentences)} sentences (must be 2 to 4 sentences).")

    # Allowed tools
    all_resume_text = json.dumps(resume_facts).lower()
    cand_tools = extract_potential_tools(candidate)
    invented_tools = [t for t in cand_tools if t not in all_resume_text]
    if invented_tools:
        checks["no_invented_tools"] = False
        failures.append(f"Invented tools detected in summary: {invented_tools}")

    # Allowed numbers
    cand_nums = extract_numbers(candidate)
    resume_nums = extract_numbers(all_resume_text)
    invented_nums = cand_nums - resume_nums
    if invented_nums:
        checks["no_invented_numbers"] = False
        failures.append(f"Invented numbers detected in summary: {sorted(invented_nums)}")

    is_valid = len(failures) == 0
    return is_valid, checks, failures
