"""Role Profiles and Job Description Demand Modeling for SkillGap.

Analyzes job postings to generate empirical skill-demand profiles per canonical role.
Provides title normalization (seniority stripping + regex rules + embedding centroid fallback),
skill frequency weighting, tier assignment (core, common, bonus), and on-the-fly JD parsing.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
from sentence_transformers import SentenceTransformer

from config import settings
from ml.extract import extract_skills

logger = logging.getLogger(__name__)

# Section regexes for parsing single job descriptions
REQ_SECTION_PAT = re.compile(
    r"(?i)\b(?:requirements?|qualifications?|must[\s-]have|what\s+you(?:'ll)?\s+need|what\s+we(?:'re)?\s+looking\s+for|minimum\s+qualifications?|basic\s+qualifications?)\b"
)
PREF_SECTION_PAT = re.compile(
    r"(?i)\b(?:nice[\s-]to[\s-]have|preferred|preferred\s+qualifications?|bonus|good[\s-]to[\s-]have|plus(?:es)?|optional)\b"
)


def strip_seniority(title: str) -> Tuple[str, Optional[str]]:
    """Separate seniority prefix/suffix keywords from the functional job title.

    Examples:
        'Senior Backend Developer' -> ('Backend Developer', 'senior')
        'Junior Data Analyst - Remote' -> ('Data Analyst', 'junior')
        'Lead Site Reliability Engineer' -> ('Site Reliability Engineer', 'lead')
        'Software Engineer' -> ('Software Engineer', None)

    Returns:
        (clean_title, seniority_level)
    """
    if not title:
        return "", None

    # Remove extra non-alphanumeric noise at edges and common location tails like '- Remote', '(Remote)'
    cleaned = re.sub(r"(?i)[\(\[\{]?(?:remote|hybrid|on[\s-]site|full[\s-]time|part[\s-]time|contract)[\)\]\}]?", "", title)
    cleaned = re.sub(r"\s+[-–—/|]\s+.*$", "", cleaned).strip()
    cleaned = re.sub(r"\s*\|\s*.*$", "", cleaned).strip()

    detected_seniority: Optional[str] = None
    lower = cleaned.lower()

    SENIORITY_CANONICAL = {
        "sr": "senior",
        "jr": "junior",
        "internship": "intern",
        "entry level": "entry",
        "mid-level": "mid",
    }

    # Match seniority keywords surrounded by word boundaries
    for kw in sorted(settings.SENIORITY_KEYWORDS, key=len, reverse=True):
        pattern = re.compile(rf"\b{re.escape(kw)}\b", re.IGNORECASE)
        if pattern.search(lower):
            raw_detected = kw.lower()
            detected_seniority = SENIORITY_CANONICAL.get(raw_detected, raw_detected)
            # Strip keyword from title
            cleaned = pattern.sub("", cleaned)
            break

    # Clean up double spaces and residual hyphens/commas
    clean_title = re.sub(r"[\s,]+", " ", cleaned).strip()
    return clean_title, detected_seniority


def load_role_rules() -> Dict[str, List[str]]:
    """Load role mapping keyword rules from config file or defaults."""
    if settings.ROLE_RULES_FILE.is_file():
        with open(settings.ROLE_RULES_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def normalize_job_title(
    raw_title: str,
    rules: Optional[Dict[str, List[str]]] = None,
    model: Optional[SentenceTransformer] = None,
    role_centroids: Optional[Dict[str, np.ndarray]] = None,
) -> Tuple[Optional[str], Optional[str]]:
    """Map a raw job title to a canonical role name and seniority level.

    Priority:
    1. Seniority stripping.
    2. Exact / substring regex rule match from role_rules.json (longest match wins).
    3. Semantic embedding centroid match (if cutoff is met).

    Returns:
        (canonical_role_name, seniority_level) or (None, seniority_level) if unassigned.
    """
    if not raw_title or not raw_title.strip():
        return None, None

    clean_title, seniority = strip_seniority(raw_title)
    if not clean_title:
        return None, seniority

    lower_clean = clean_title.lower()
    rule_dict = rules if rules is not None else load_role_rules()

    # Rule-based matching
    best_role: Optional[str] = None
    best_match_len = 0

    for role_name, patterns in rule_dict.items():
        for pat in patterns:
            pat_lower = pat.lower()
            # Check whole phrase match or word boundary match
            if re.search(rf"\b{re.escape(pat_lower)}\b", lower_clean):
                if len(pat_lower) > best_match_len:
                    best_match_len = len(pat_lower)
                    best_role = role_name

    if best_role is not None:
        return best_role, seniority

    # Fallback to title embedding similarity against role centroids
    if model is not None and role_centroids:
        title_vec = model.encode(clean_title, normalize_embeddings=True)
        best_sim = -1.0
        best_emb_role: Optional[str] = None

        for role_name, centroid in role_centroids.items():
            sim = float(np.dot(title_vec, centroid))
            if sim > best_sim:
                best_sim = sim
                best_emb_role = role_name

        if best_sim >= settings.ROLE_TITLE_SIMILARITY_CUTOFF:
            return best_emb_role, seniority

    return None, seniority


def assign_tier(weight: float) -> str:
    """Classify a skill's empirical weight into a demand tier."""
    if weight >= settings.CORE_SKILL_SHARE_THRESHOLD:
        return "core"
    elif weight >= settings.COMMON_SKILL_SHARE_THRESHOLD:
        return "common"
    else:
        return "bonus"


def profile_from_jd(
    text: str, role_title: str = "Custom Job Description"
) -> Dict[str, Any]:
    """Create a temporary skill-demand profile from a pasted job description.

    Segments the description into sections and weights requirements higher than nice-to-haves:
    - Requirements / Must-have sections: weight 1.0 (core)
    - Preferred / Nice-to-have sections: weight 0.5 (common)
    - General description: weight 0.8 (core)

    Returns:
        Dictionary conforming to role profile schema with extracted skills, weights, and tiers.
    """
    if not text or not text.strip():
        return {"role": role_title, "n_postings": 1, "skills": {}}

    lines = text.split("\n")
    current_weight = 0.8  # default baseline for general text
    skill_weights: Dict[str, float] = {}

    current_chunk: List[str] = []

    def process_chunk(chunk_lines: List[str], weight: float):
        chunk_text = "\n".join(chunk_lines).strip()
        if not chunk_text:
            return
        res = extract_skills(chunk_text, mode="hybrid")
        for sid in res.skills:
            if sid not in skill_weights or weight > skill_weights[sid]:
                skill_weights[sid] = weight

    for line in lines:
        stripped = line.strip()
        if PREF_SECTION_PAT.search(stripped) and len(stripped.split()) <= 8:
            process_chunk(current_chunk, current_weight)
            current_chunk = []
            current_weight = 0.5
        elif REQ_SECTION_PAT.search(stripped) and len(stripped.split()) <= 8:
            process_chunk(current_chunk, current_weight)
            current_chunk = []
            current_weight = 1.0
        else:
            current_chunk.append(line)

    process_chunk(current_chunk, current_weight)

    # Format into profile skill entries
    skills_profile: Dict[str, Dict[str, Any]] = {}
    for sid, w in sorted(skill_weights.items(), key=lambda item: item[1], reverse=True):
        tier = "core" if w >= 0.8 else "common"
        skills_profile[sid] = {
            "weight": round(w, 2),
            "tier": tier,
        }

    return {
        "role": role_title,
        "n_postings": 1,
        "skills": skills_profile,
    }


# Alias for backward and external compatibility
parse_job_description = profile_from_jd


class RoleProfileManager:
    """Manages loaded role profiles and their reference text embeddings."""

    def __init__(
        self,
        profiles_file: Optional[Path] = None,
        embeddings_file: Optional[Path] = None,
    ):
        self.profiles_file = profiles_file or settings.ROLE_PROFILES_FILE
        self.embeddings_file = embeddings_file or settings.ROLE_EMBEDDINGS_FILE
        self._profiles: Dict[str, Dict[str, Any]] = {}
        self._embeddings: Optional[Dict[str, np.ndarray]] = None

    def is_loaded(self) -> bool:
        return len(self._profiles) > 0

    def load(self) -> None:
        """Load role profiles from disk."""
        if not self.profiles_file.is_file():
            raise FileNotFoundError(
                f"Role profiles file not found at {self.profiles_file}. "
                f"Run 'python scripts/build_profiles.py' to generate role profiles."
            )

        with open(self.profiles_file, "r", encoding="utf-8") as f:
            self._profiles = json.load(f)

        # Load role text embeddings if available
        if self.embeddings_file.is_file():
            raw = np.load(self.embeddings_file, allow_pickle=True)
            if hasattr(raw, "item") and raw.ndim == 0:
                self._embeddings = raw.item()
            elif isinstance(raw, dict):
                self._embeddings = raw
            else:
                all_role_names = sorted(self._profiles.keys())
                self._embeddings = {
                    r: raw[i] for i, r in enumerate(all_role_names) if i < len(raw)
                }
        else:
            self._embeddings = None

        logger.info("Loaded profiles for %d roles.", len(self._profiles))

    @property
    def profiles(self) -> Dict[str, Dict[str, Any]]:
        if not self.is_loaded():
            self.load()
        return self._profiles

    def get_role_profile(self, role_name: str) -> Optional[Dict[str, Any]]:
        """Retrieve profile dictionary for a canonical role."""
        return self.profiles.get(role_name)

    def get_profile(self, role_name: str) -> Optional[Dict[str, Any]]:
        """Alias for get_role_profile."""
        return self.get_role_profile(role_name)

    def get_canonical_roles(self) -> List[str]:
        """List all available canonical roles in the profile repository."""
        return sorted(self.profiles.keys())

    def list_roles(self) -> List[str]:
        """Alias for get_canonical_roles."""
        return self.get_canonical_roles()

    def get_core_skills(self, role_name: str) -> List[str]:
        """Get list of core skill IDs for a role."""
        profile = self.get_role_profile(role_name)
        if not profile:
            return []
        return [
            sid
            for sid, data in profile.get("skills", {}).items()
            if data.get("tier") == "core"
        ]

    def get_common_skills(self, role_name: str) -> List[str]:
        """Get list of common skill IDs for a role."""
        profile = self.get_role_profile(role_name)
        if not profile:
            return []
        return [
            sid
            for sid, data in profile.get("skills", {}).items()
            if data.get("tier") == "common"
        ]

    def get_role_embedding(self, role_name: str) -> Optional[np.ndarray]:
        """Retrieve precomputed description embedding for a role."""
        if self._embeddings is None and self.embeddings_file.is_file():
            self.load()
        if self._embeddings and role_name in self._embeddings:
            return self._embeddings[role_name]
        return None


# Global singleton manager
role_manager = RoleProfileManager()
