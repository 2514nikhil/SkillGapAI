"""Skill Extraction Engine for SkillGap.

Implements a two-stage extraction architecture:
- Stage A: High-precision dictionary matching using spaCy PhraseMatcher with
  longest-match resolution, alias resolution, and context rules for ambiguous skills.
- Stage B: High-recall semantic fallback using noun chunk embeddings against
  precomputed taxonomy embeddings.
"""

from __future__ import annotations

import logging
import re
from dataclasses import asdict, dataclass, field
from typing import Any, Dict, List, Optional, Set, Tuple

import numpy as np
import spacy
from spacy.matcher import PhraseMatcher
from spacy.tokens import Doc, Span

from config import settings
from ml.taxonomy import Taxonomy, is_ambiguous_skill, normalize_skill_name, taxonomy

logger = logging.getLogger(__name__)

# Section heading patterns
SECTION_PATTERNS = [
    (
        "skills",
        re.compile(
            r"^(?:technical\s+skills?|technologies|tech\s+stack|core\s+competencies|skills?\s*(?:&|and)\s*tools?|skills?|tools?\s*(?:&|and)\s*technologies)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "experience",
        re.compile(
            r"^(?:work\s+experience|professional\s+experience|employment\s+history|experience|career\s+history)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "projects",
        re.compile(
            r"^(?:projects?|key\s+projects?|personal\s+projects?|academic\s+projects?)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "education",
        re.compile(
            r"^(?:education|academic\s+background|degrees?|qualifications)\b",
            re.IGNORECASE,
        ),
    ),
    (
        "certifications",
        re.compile(
            r"^(?:certifications?|licenses?\s*(?:&|and)\s*certifications?|credentials)\b",
            re.IGNORECASE,
        ),
    ),
]


@dataclass
class SkillHit:
    """Represents a single occurrence of an extracted skill in the text."""

    skill_id: str
    surface_text: str
    start: int
    end: int
    sentence: str
    section: str
    source: str = "dict"  # "dict" or "semantic"
    confidence: float = 1.0

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


@dataclass
class ExtractionResult:
    """Consolidated result of skill extraction across a document."""

    skills: List[str]  # Sorted list of unique canonical skill_ids
    hits: List[SkillHit]
    skill_hits_by_id: Dict[str, List[SkillHit]]
    best_sentences: Dict[str, str]
    confidence_by_skill: Dict[str, float]
    mode: str

    def to_dict(self) -> Dict[str, Any]:
        return {
            "skills": self.skills,
            "hits": [h.to_dict() for h in self.hits],
            "skill_hits_by_id": {
                sid: [h.to_dict() for h in hits] for sid, hits in self.skill_hits_by_id.items()
            },
            "best_sentences": self.best_sentences,
            "confidence_by_skill": self.confidence_by_skill,
            "mode": self.mode,
        }


def detect_sections(text: str) -> List[Tuple[int, int, str]]:
    """Detect resume/document section boundaries using heading heuristics.

    Returns:
        List of (start_char, end_char, section_name) intervals.
    """
    if not text:
        return []

    lines = text.split("\n")
    headers: List[Tuple[int, str]] = []

    current_offset = 0
    for line in lines:
        stripped = line.strip().strip(":").strip()
        for sec_name, pat in SECTION_PATTERNS:
            if pat.match(stripped) and len(stripped.split()) <= 5:
                headers.append((current_offset, sec_name))
                break
        current_offset += len(line) + 1  # +1 for newline

    if not headers:
        return [(0, len(text), "other")]

    # Build spans from header offsets
    sections: List[Tuple[int, int, str]] = []
    if headers[0][0] > 0:
        sections.append((0, headers[0][0], "other"))

    for i in range(len(headers)):
        start = headers[i][0]
        end = headers[i + 1][0] if i + 1 < len(headers) else len(text)
        sections.append((start, end, headers[i][1]))

    return sections


def get_section_for_offset(offset: int, sections: List[Tuple[int, int, str]]) -> str:
    """Find the section name encompassing a given character offset."""
    for start, end, name in sections:
        if start <= offset < end:
            return name
    return "other"


def has_ambiguous_context(
    doc: Doc,
    token_start: int,
    token_end: int,
    section: str,
    window_size: int = 4,
) -> bool:
    """Check whether a short or polysemous skill match has surrounding context evidence.

    Accepts match if:
    1. It appears inside a dedicated skills section ('skills'), OR
    2. Any token within window_size before or after is a recognized cue word.

    Args:
        doc: Processed spaCy Doc.
        token_start: Token index where match starts.
        token_end: Token index where match ends.
        section: Detected section name.
        window_size: Number of tokens before and after to inspect for cue words.
    """
    if section.lower() == "skills":
        return True

    # Look in the token context window
    start_ctx = max(0, token_start - window_size)
    end_ctx = min(len(doc), token_end + window_size)

    cue_words = settings.AMBIGUOUS_CUE_WORDS

    # Inspect preceding window
    for t in doc[start_ctx:token_start]:
        if t.text.lower() in cue_words or t.lemma_.lower() in cue_words:
            return True

    # Inspect succeeding window
    for t in doc[token_end:end_ctx]:
        if t.text.lower() in cue_words or t.lemma_.lower() in cue_words:
            return True

    return False


class SkillExtractor:
    """Orchestrates Stage A (PhraseMatcher) and Stage B (Semantic) extraction."""

    def __init__(self, tax: Optional[Taxonomy] = None):
        self.tax = tax or taxonomy
        self._nlp: Optional[spacy.language.Language] = None
        self._matcher: Optional[PhraseMatcher] = None
        self._pattern_to_id: Dict[str, str] = {}

    @property
    def nlp(self) -> spacy.language.Language:
        if self._nlp is None:
            self._nlp = spacy.load(settings.SPACY_MODEL_NAME)
        return self._nlp

    @property
    def matcher(self) -> PhraseMatcher:
        if self._matcher is None:
            self._init_matcher()
        return self._matcher

    def _init_matcher(self) -> None:
        """Initialize spaCy PhraseMatcher with canonical skill names and aliases."""
        if not self.tax.is_loaded():
            self.tax.load()

        self._matcher = PhraseMatcher(self.nlp.vocab, attr="LOWER")
        self._pattern_to_id.clear()

        for skill_id, info in self.tax.skills.items():
            patterns = [info["name"]] + info.get("aliases", [])
            for pattern_str in patterns:
                norm_pat = pattern_str.strip()
                if norm_pat:
                    doc = self.nlp.make_doc(norm_pat)
                    # Add pattern with label = skill_id
                    self._matcher.add(skill_id, [doc])
                    self._pattern_to_id[norm_pat.lower()] = skill_id

        logger.info("Initialized PhraseMatcher with skills taxonomy.")

    def extract_baseline(self, text: str) -> List[SkillHit]:
        """Stage A: High-precision dictionary matching with longest match resolution."""
        if not text or not text.strip():
            return []

        doc = self.nlp(text)
        sections = detect_sections(text)
        raw_matches = self.matcher(doc)

        # Build candidate Spans with metadata
        candidates: List[Tuple[Span, str]] = []
        for match_id, start_tok, end_tok in raw_matches:
            span = doc[start_tok:end_tok]
            skill_id = self.nlp.vocab.strings[match_id]
            candidates.append((span, skill_id))

        # Longest match wins: sort by length (descending), then start token (ascending)
        candidates.sort(key=lambda item: (len(item[0]), -(item[0].start)), reverse=True)

        accepted_spans: List[Tuple[int, int]] = []  # (start_char, end_char)
        hits: List[SkillHit] = []

        for span, skill_id in candidates:
            start_char = span.start_char
            end_char = span.end_char

            # Check overlap with already accepted spans
            overlaps = any(
                max(start_char, a_start) < min(end_char, a_end)
                for a_start, a_end in accepted_spans
            )
            if overlaps:
                continue

            section = get_section_for_offset(start_char, sections)
            skill_info = self.tax.get_skill(skill_id)
            is_amb = skill_info.get("ambiguous", False) if skill_info else False

            # If ambiguous, require context evidence
            if is_amb and not has_ambiguous_context(doc, span.start, span.end, section):
                continue

            accepted_spans.append((start_char, end_char))
            sentence_text = span.sent.text.strip() if span.sent else span.text

            confidence = 1.0 if section == "skills" else 0.90
            hit = SkillHit(
                skill_id=skill_id,
                surface_text=span.text,
                start=start_char,
                end=end_char,
                sentence=sentence_text,
                section=section,
                source="dict",
                confidence=confidence,
            )
            hits.append(hit)

        # Sort hits chronologically by start offset
        hits.sort(key=lambda h: h.start)
        return hits

    def extract_semantic(
        self,
        text: str,
        existing_hits: Optional[List[SkillHit]] = None,
    ) -> List[SkillHit]:
        """Stage B: Semantic fallback for uncaptured noun phrases in skills sections."""
        if not text or not text.strip():
            return []

        doc = self.nlp(text)
        sections = detect_sections(text)
        existing_hits = existing_hits or []
        occupied_intervals = [(h.start, h.end) for h in existing_hits]
        existing_skill_ids = {h.skill_id for h in existing_hits}

        candidates: List[Tuple[Span, str, str]] = []  # (span, cleaned_text, section)

        # 1. Inspect noun chunks and bullet items
        for chunk in doc.noun_chunks:
            # Check overlap with existing dict hits
            if any(
                max(chunk.start_char, o_start) < min(chunk.end_char, o_end)
                for o_start, o_end in occupied_intervals
            ):
                continue

            cleaned = normalize_skill_name(chunk.text)
            words = cleaned.split()
            if not (1 <= len(words) <= 5 and 2 <= len(cleaned) <= 40):
                continue

            # Reject purely numeric or punctuation
            if not re.search(r"[a-zA-Z]", cleaned):
                continue

            # Skip common stopwords
            if chunk.root.is_stop and len(words) == 1:
                continue

            sec = get_section_for_offset(chunk.start_char, sections)
            candidates.append((chunk, cleaned, sec))

        if not candidates or self.tax.embeddings is None:
            return []

        candidate_texts = [c[1] for c in candidates]
        # Embed candidate phrases
        model = self.tax._model
        if model is None:
            from sentence_transformers import SentenceTransformer
            model = SentenceTransformer(settings.EMBEDDING_MODEL_NAME)
            self.tax._model = model

        chunk_embeddings = model.encode(candidate_texts, normalize_embeddings=True)
        # Cosine similarities: (num_candidates, num_skills)
        sim_matrix = np.dot(chunk_embeddings, self.tax.embeddings.T)

        semantic_hits: List[SkillHit] = []
        threshold = settings.SEM_MATCH_THRESHOLD

        for idx, (span, cleaned, sec) in enumerate(candidates):
            best_skill_idx = int(np.argmax(sim_matrix[idx]))
            best_score = float(sim_matrix[idx, best_skill_idx])

            if best_score >= threshold:
                best_skill_id = self.tax.skill_ids[best_skill_idx]
                if best_skill_id in existing_skill_ids:
                    continue

                sentence_text = span.sent.text.strip() if span.sent else span.text
                hit = SkillHit(
                    skill_id=best_skill_id,
                    surface_text=span.text,
                    start=span.start_char,
                    end=span.end_char,
                    sentence=sentence_text,
                    section=sec,
                    source="semantic",
                    confidence=round(best_score, 4),
                )
                semantic_hits.append(hit)
                existing_skill_ids.add(best_skill_id)
                occupied_intervals.append((span.start_char, span.end_char))

        semantic_hits.sort(key=lambda h: h.start)
        return semantic_hits

    def extract_skills(self, text: str, mode: str = "hybrid") -> ExtractionResult:
        """Extract canonical skills from text in 'baseline', 'hybrid', or 'hybrid+slm' mode."""
        if mode not in {"baseline", "hybrid", "hybrid+slm"}:
            raise ValueError(f"Unknown extraction mode '{mode}'. Choose 'baseline', 'hybrid', or 'hybrid+slm'.")

        baseline_hits = self.extract_baseline(text)

        if mode == "baseline":
            all_hits = baseline_hits
        else:
            semantic_hits = self.extract_semantic(text, existing_hits=baseline_hits)
            all_hits = baseline_hits + semantic_hits
            all_hits.sort(key=lambda h: h.start)

            if mode == "hybrid+slm":
                from ml.slm import extract_skills_slm

                slm_hits: List[SkillHit] = []
                existing_skill_ids = {h.skill_id for h in all_hits}

                doc = self.nlp(text)
                sections = detect_sections(text)

                def get_sec(char_offset: int) -> str:
                    for s_start, s_end, s_name in sections:
                        if s_start <= char_offset < s_end:
                            return s_name
                    return "other"

                for sent in doc.sents:
                    sent_text = sent.text.strip()
                    if len(sent_text.split()) < 4:
                        continue

                    # Check if this sentence contains any existing hit
                    has_hit = any(
                        sent.start_char <= h.start < sent.end_char
                        for h in all_hits
                    )
                    if not has_hit:
                        # Low-yield sentence: request SLM extraction recovery
                        slm_extracted = extract_skills_slm(sent_text)
                        for can_id, surface in slm_extracted:
                            if can_id in existing_skill_ids:
                                continue

                            # Find character offsets in text
                            surf_lower = surface.lower()
                            s_idx = sent_text.lower().find(surf_lower)
                            if s_idx != -1:
                                start_char = sent.start_char + s_idx
                                end_char = start_char + len(surface)
                            else:
                                start_char = sent.start_char
                                end_char = sent.end_char

                            sec = get_sec(start_char)
                            hit = SkillHit(
                                skill_id=can_id,
                                surface_text=surface,
                                start=start_char,
                                end=end_char,
                                sentence=sent_text,
                                section=sec,
                                source="slm",
                                confidence=0.70,
                            )
                            slm_hits.append(hit)
                            existing_skill_ids.add(can_id)

                all_hits.extend(slm_hits)
                all_hits.sort(key=lambda h: h.start)

        # Consolidate per skill_id
        skill_hits_by_id: Dict[str, List[SkillHit]] = {}
        for h in all_hits:
            skill_hits_by_id.setdefault(h.skill_id, []).append(h)

        unique_skills = sorted(skill_hits_by_id.keys())

        # Select best evidence sentence per skill
        best_sentences: Dict[str, str] = {}
        confidence_by_skill: Dict[str, float] = {}

        for sid, hits in skill_hits_by_id.items():
            # Preference: hits with sentences in experience > projects > skills > other
            def sentence_priority(h: SkillHit) -> Tuple[int, int]:
                sec_order = {"experience": 3, "projects": 2, "skills": 1, "other": 0}
                return (sec_order.get(h.section, 0), len(h.sentence))

            best_hit = max(hits, key=sentence_priority)
            best_sentences[sid] = best_hit.sentence
            # Max confidence across hits for this skill
            confidence_by_skill[sid] = max(h.confidence for h in hits)

        return ExtractionResult(
            skills=unique_skills,
            hits=all_hits,
            skill_hits_by_id=skill_hits_by_id,
            best_sentences=best_sentences,
            confidence_by_skill=confidence_by_skill,
            mode=mode,
        )


# Singleton extractor
extractor = SkillExtractor()


def extract_baseline(text: str) -> List[SkillHit]:
    """Convenience function for Stage A baseline extraction."""
    return extractor.extract_baseline(text)


def extract_semantic(text: str, existing_hits: Optional[List[SkillHit]] = None) -> List[SkillHit]:
    """Convenience function for Stage B semantic fallback."""
    return extractor.extract_semantic(text, existing_hits=existing_hits)


def extract_skills(text: str, mode: str = "hybrid") -> ExtractionResult:
    """Convenience function for full extraction."""
    return extractor.extract_skills(text, mode=mode)
