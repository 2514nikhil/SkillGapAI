"""In-memory, time-limited cache for SkillGap analysis sessions.

Holds ONLY extracted canonical skill IDs and target role identifiers.
Strictly NEVER persists resume files, raw text, or candidate personal data.
"""

from __future__ import annotations

import logging
import time
import uuid
from typing import Any, Dict, List, Optional, Set

from config import settings

logger = logging.getLogger(__name__)


class AnalysisCache:
    """Time-limited in-memory store for candidate skill profiles."""

    def __init__(self, ttl_seconds: Optional[int] = None):
        self.ttl = ttl_seconds or settings.ANALYSIS_CACHE_TTL_SECONDS
        self._cache: Dict[str, Dict[str, Any]] = {}

    def set(
        self,
        skills: List[str] | Set[str],
        role: Optional[str] = None,
        jd_profile: Optional[Dict[str, Any]] = None,
    ) -> str:
        """Store extracted skill IDs and return a unique random analysis_id.

        Args:
            skills: Canonical skill IDs.
            role: Optional target role name.
            jd_profile: Optional transient JD profile dict (skills and weights only, no raw text).
        """
        self.cleanup()
        analysis_id = str(uuid.uuid4())
        self._cache[analysis_id] = {
            "skills": sorted(list(set(skills))),
            "role": role,
            "jd_profile": jd_profile,
            "created_at": time.time(),
        }
        return analysis_id

    def get(self, analysis_id: str) -> Optional[Dict[str, Any]]:
        """Retrieve cached analysis skills by ID if not expired."""
        self.cleanup()
        entry = self._cache.get(analysis_id)
        if not entry:
            return None
        if time.time() - entry["created_at"] > self.ttl:
            self._cache.pop(analysis_id, None)
            return None
        return entry

    def cleanup(self) -> None:
        """Remove expired entries."""
        now = time.time()
        expired = [k for k, v in self._cache.items() if now - v["created_at"] > self.ttl]
        for k in expired:
            self._cache.pop(k, None)

    def clear(self) -> None:
        """Clear all cached entries."""
        self._cache.clear()

    def __len__(self) -> int:
        self.cleanup()
        return len(self._cache)


# Global singleton cache instance
analysis_cache = AnalysisCache()
