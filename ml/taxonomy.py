"""Canonical Skills Taxonomy module for SkillGap.

Manages loading, normalization, lookup, alias resolution, and similarity search
across canonical skills and their precomputed embeddings.
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

logger = logging.getLogger(__name__)


def normalize_skill_name(name: str) -> str:
    """Normalize a skill name into a clean, lowercased canonical token/string.

    Preserves special programming characters like ++, #, and dots (.net, node.js).
    Strips trailing punctuation and collapses whitespace.
    """
    if not name:
        return ""
    text = name.strip()
    # Strip wrapping quotes or brackets
    text = re.sub(r"^[\"'\(\[\{]+|[\"'\)\]\}]+$", "", text)
    # Strip trailing punctuation (periods, commas, semicolons)
    text = re.sub(r"[\.,;:!\?]+$", "", text)
    # Collapse whitespace
    text = re.sub(r"\s+", " ", text)
    return text.strip().lower()


def is_valid_skill_term(term: str) -> bool:
    """Validate whether a term is suitable as a skill entry.

    Rejects terms longer than 5 words, empty strings, and generic non-skill words.
    """
    if not term:
        return False
    norm = normalize_skill_name(term)
    if not norm:
        return False
    # Check generic non-skill words
    if norm in settings.NON_SKILL_WORDS:
        return False
    # Check word length (max 5 words)
    words = norm.split()
    if len(words) > 5 or len(norm) > 60:
        return False
    return True


def is_ambiguous_skill(name: str, aliases: Optional[List[str]] = None) -> bool:
    """Determine whether a skill name or alias is short or polysemous requiring context.

    Examples: R, C, Go, Swift, Rust, Spark, Word, Excel.
    """
    norm = normalize_skill_name(name)
    if norm in settings.AMBIGUOUS_SKILL_NAMES:
        return True
    if len(norm) <= 2 and norm not in {"ai", "ml", "ui", "ux", "qa", "ci", "cd", "ts", "js"}:
        return True
    if aliases:
        for a in aliases:
            if normalize_skill_name(a) in settings.AMBIGUOUS_SKILL_NAMES:
                return True
    return False


class Taxonomy:
    """In-memory manager for the canonical skills taxonomy and embeddings."""

    def __init__(
        self,
        skills_file: Optional[Path] = None,
        embeddings_file: Optional[Path] = None,
        ids_file: Optional[Path] = None,
    ):
        self.skills_file = skills_file or settings.SKILLS_FILE
        self.embeddings_file = embeddings_file or settings.SKILL_EMBEDDINGS_FILE
        self.ids_file = ids_file or settings.SKILL_IDS_FILE

        self._skills: Dict[str, Dict[str, Any]] = {}
        self._name_to_id: Dict[str, str] = {}
        self._alias_to_id: Dict[str, str] = {}
        self._embeddings: Optional[np.ndarray] = None
        self._skill_ids_list: List[str] = []
        self._id_to_idx: Dict[str, int] = {}
        self._model: Optional[SentenceTransformer] = None

    def is_loaded(self) -> bool:
        """Check if skills have been loaded into memory."""
        return len(self._skills) > 0

    def load(self) -> None:
        """Load skills taxonomy and embeddings from disk."""
        if not self.skills_file.is_file():
            raise FileNotFoundError(
                f"Taxonomy file not found at {self.skills_file}. "
                f"Run 'python scripts/build_taxonomy.py' to generate it."
            )

        with open(self.skills_file, "r", encoding="utf-8") as f:
            self._skills = json.load(f)

        self._name_to_id.clear()
        self._alias_to_id.clear()

        for skill_id, data in self._skills.items():
            name_key = normalize_skill_name(data["name"])
            self._name_to_id[name_key] = skill_id
            for alias in data.get("aliases", []):
                alias_key = normalize_skill_name(alias)
                if alias_key and alias_key not in self._alias_to_id:
                    self._alias_to_id[alias_key] = skill_id

        # Load precomputed embeddings if available
        if self.embeddings_file.is_file() and self.ids_file.is_file():
            self._embeddings = np.load(self.embeddings_file)
            with open(self.ids_file, "r", encoding="utf-8") as f:
                self._skill_ids_list = json.load(f)
            self._id_to_idx = {sid: idx for idx, sid in enumerate(self._skill_ids_list)}
            logger.info(
                "Loaded taxonomy with %d skills and %d embeddings.",
                len(self._skills),
                len(self._embeddings),
            )
        else:
            logger.warning(
                "Taxonomy skills loaded (%d), but embeddings not found at %s. "
                "Run 'python scripts/build_taxonomy.py' to precompute them.",
                len(self._skills),
                self.embeddings_file,
            )

    @property
    def skills(self) -> Dict[str, Dict[str, Any]]:
        if not self.is_loaded():
            self.load()
        return self._skills

    @property
    def embeddings(self) -> Optional[np.ndarray]:
        if self._embeddings is None and self.embeddings_file.is_file():
            self.load()
        return self._embeddings

    @property
    def skill_ids(self) -> List[str]:
        if not self._skill_ids_list and self.ids_file.is_file():
            self.load()
        return self._skill_ids_list

    @property
    def model(self):
        """SentenceTransformer model for on-the-fly phrase embeddings."""
        if self._model is None:
            from sentence_transformers import SentenceTransformer
            self._model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
        return self._model

    def get_skill(self, skill_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve skill dictionary by canonical skill_id."""
        return self.skills.get(skill_id)

    def get_skill_embedding(self, skill_id: str) -> Optional[np.ndarray]:
        """Retrieve precomputed normalized embedding vector for a skill ID."""
        if not self.is_loaded():
            self.load()
        if self._embeddings is None or skill_id not in self._id_to_idx:
            return None
        return self._embeddings[self._id_to_idx[skill_id]]

    def find_skill_id(self, term: str) -> Optional[str]:
        """Resolve a raw or canonical term to its canonical skill_id."""
        if not self.is_loaded():
            self.load()
        norm = normalize_skill_name(term)
        if norm in self._skills:
            return norm
        if norm in self._name_to_id:
            return self._name_to_id[norm]
        if norm in self._alias_to_id:
            return self._alias_to_id[norm]
        return None

    def get_by_category(self, category: str) -> List[Dict[str, Any]]:
        """Return all skills belonging to a specific category."""
        return [
            {"id": sid, **info}
            for sid, info in self.skills.items()
            if info.get("category") == category
        ]

    def get_category_counts(self) -> Dict[str, int]:
        """Compute the distribution of skills across taxonomy categories."""
        counts: Dict[str, int] = {cat: 0 for cat in settings.SKILL_CATEGORIES}
        for info in self.skills.values():
            cat = info.get("category", "tools")
            counts[cat] = counts.get(cat, 0) + 1
        return counts

    def find_nearest_skills(self, query_or_skill_id: str, top_k: int = 20) -> List[Tuple[str, float]]:
        """Find the top-k nearest skills using cosine similarity over precomputed embeddings.

        Args:
            query_or_skill_id: A skill ID (e.g. 'pytorch', 'sql') or an arbitrary query string.
            top_k: Number of nearest neighbors to return.

        Returns:
            List of (skill_name, similarity_score) tuples sorted in descending order.
        """
        if self.embeddings is None:
            raise RuntimeError("Embeddings are not loaded. Run 'python scripts/build_taxonomy.py'.")

        target_id = self.find_skill_id(query_or_skill_id)
        if target_id and target_id in self._id_to_idx:
            # Precomputed vector lookup
            idx = self._id_to_idx[target_id]
            query_vec = self.embeddings[idx]
        else:
            # Encode on-the-fly
            if self._model is None:
                self._model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
            query_vec = self._model.encode(query_or_skill_id, normalize_embeddings=True)

        # Cosine similarity over normalized embeddings is dot product
        scores = np.dot(self.embeddings, query_vec)

        # Get top indices (excluding query self-match if exact match)
        top_indices = np.argsort(scores)[::-1]

        results: List[Tuple[str, float]] = []
        for idx in top_indices:
            sid = self.skill_ids[idx]
            skill_info = self._skills.get(sid, {})
            name = skill_info.get("name", sid)
            score = float(scores[idx])
            results.append((name, score))
            if len(results) >= top_k:
                break

        return results


# Global singleton instance
taxonomy = Taxonomy()
