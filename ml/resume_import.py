"""Resume Import Engine for SkillGap.

Parses unstructured resumes (PDF, DOCX, TXT) into a schema-compliant partial draft
with a confidence-tracked `needs_review` list. Uses deterministic heuristics and
the skill extractor without storing any data.
"""

from __future__ import annotations

import json
import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from ml.extract import extract_skills
from ml.parse import parse_resume
from ml.resume_schema import (
    Basics,
    CertificationItem,
    EducationItem,
    ExperienceItem,
    ProjectItem,
    Resume,
    SkillItem,
    SocialLink,
    sanitize_string,
)
from ml.socials import extract_value, load_platforms

logger = logging.getLogger(__name__)

CATALOG_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "tech_catalog.json"

EMAIL_REGEX = re.compile(r"\b[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}\b")
PHONE_REGEX = re.compile(r"(?:\+?\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}|\+?\d{10,13}")
DATE_RANGE_REGEX = re.compile(
    r"\b((?:19|20)\d{2}(?:[-/.]\d{1,2})?|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*(?:19|20)\d{2})\s*(?:–|-|—|to)\s*((?:19|20)\d{2}(?:[-/.]\d{1,2})?|(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\.?\s*(?:19|20)\d{2}|Present|Current)\b",
    re.IGNORECASE,
)
YEAR_REGEX = re.compile(r"\b(19\d{2}|20\d{2})\b")

MONTH_MAP = {
    "jan": "01", "feb": "02", "mar": "03", "apr": "04",
    "may": "05", "jun": "06", "jul": "07", "aug": "08",
    "sep": "09", "oct": "10", "nov": "11", "dec": "12",
}

SECTION_HEADERS = [
    ("experience", re.compile(r"^(?:work\s+experience|professional\s+experience|experience|employment(?:\s+history)?|career\s+history)\b", re.IGNORECASE)),
    ("education", re.compile(r"^(?:education|academic\s+background|degrees?|qualifications|academics)\b", re.IGNORECASE)),
    ("projects", re.compile(r"^(?:projects?|key\s+projects?|personal\s+projects?|academic\s+projects?)\b", re.IGNORECASE)),
    ("skills", re.compile(r"^(?:technical\s+skills?|technologies|tech\s+stack|core\s+competencies|skills?\s*(?:&|and)\s*tools?|skills?|tools?\s*(?:&|and)\s*technologies)\b", re.IGNORECASE)),
    ("summary", re.compile(r"^(?:summary|professional\s+summary|about(?:\s+me)?|profile|overview|objective)\b", re.IGNORECASE)),
    ("certifications", re.compile(r"^(?:certifications?|licenses?\s*(?:&|and)\s*certifications?|credentials)\b", re.IGNORECASE)),
    ("achievements", re.compile(r"^(?:achievements?|honors?\s*(?:&|and)\s*awards?|awards?)\b", re.IGNORECASE)),
    ("publications", re.compile(r"^(?:publications?|papers?|research)\b", re.IGNORECASE)),
]


def _normalize_date_str(val: str) -> Optional[str]:
    """Normalize extracted date token to YYYY-MM, YYYY, or Present."""
    if not val:
        return None
    val = val.strip()
    if val.lower() in ("present", "current"):
        return "Present"

    # Match Month Year (e.g., 'Jan 2021', 'September 2020')
    m_mo = re.match(r"^([A-Za-z]+)\.?\s*(\d{4})$", val)
    if m_mo:
        month_prefix = m_mo.group(1)[:3].lower()
        year = m_mo.group(2)
        month_num = MONTH_MAP.get(month_prefix, "01")
        return f"{year}-{month_num}"

    # Match YYYY-MM or YYYY.MM or YYYY/MM
    m_ym = re.match(r"^(\d{4})[-/.](\d{1,2})$", val)
    if m_ym:
        year = m_ym.group(1)
        month = m_ym.group(2).zfill(2)
        return f"{year}-{month}"

    # Match standalone year YYYY
    m_y = re.match(r"^(\d{4})$", val)
    if m_y:
        return m_y.group(1)

    return None


def _load_catalog_lookup() -> Tuple[Dict[str, str], Dict[str, str]]:
    """Return (skill_name_to_category, alias_to_category)."""
    skill_to_cat: Dict[str, str] = {}
    if CATALOG_PATH.exists():
        with open(CATALOG_PATH, "r", encoding="utf-8") as f:
            data = json.load(f)
        for cat in data.get("categories", []):
            cid = cat["id"]
            for sk in cat.get("skills", []):
                skill_to_cat[sk["name"].lower()] = cid
                if sk.get("taxonomy_id"):
                    skill_to_cat[sk["taxonomy_id"].lower()] = cid
                for alias in sk.get("aliases", []):
                    skill_to_cat[alias.lower()] = cid
    return skill_to_cat


def _split_into_sections(text: str) -> Dict[str, List[str]]:
    """Segment document text into labeled section line buckets."""
    sections: Dict[str, List[str]] = {"header": []}
    current_sec = "header"

    for line in text.split("\n"):
        clean_line = line.strip()
        if not clean_line:
            continue

        matched_sec = None
        # Check if line matches a known section header
        if len(clean_line) <= 50 and not clean_line.endswith("."):
            for sec_name, pat in SECTION_HEADERS:
                if pat.match(clean_line):
                    matched_sec = sec_name
                    break

        if matched_sec:
            current_sec = matched_sec
            if current_sec not in sections:
                sections[current_sec] = []
        else:
            sections[current_sec].append(clean_line)

    return sections


def import_resume(file_bytes: bytes, filename: str) -> Dict[str, Any]:
    """Parse resume from bytes into a draft Resume model with review items."""
    needs_review: List[Dict[str, str]] = []

    # 1. Parse text using existing parser
    raw_text = parse_resume(file_bytes, filename)
    sections = _split_into_sections(raw_text)
    header_lines = sections.get("header", [])

    # 2. Extract Candidate Basics
    # Name
    name = "Candidate"
    name_found = False
    for line in header_lines[:3]:
        # Filter out lines that look like contacts or headings
        if not EMAIL_REGEX.search(line) and not PHONE_REGEX.search(line) and "http" not in line and "@" not in line:
            words = line.split()
            if 1 <= len(words) <= 5 and not any(ch.isdigit() for ch in line):
                name = line.title()
                name_found = True
                break

    if not name_found:
        needs_review.append({
            "field": "basics.name",
            "reason": "Candidate name could not be automatically determined from the document header with high confidence.",
        })

    # Email
    email_match = EMAIL_REGEX.search(raw_text)
    if email_match:
        email = email_match.group(0).lower()
    else:
        email = "placeholder@example.com"
        needs_review.append({
            "field": "basics.email",
            "reason": "No email address found in the resume. Please provide a valid email.",
        })

    # Phone
    phone_match = PHONE_REGEX.search(raw_text)
    phone = phone_match.group(0).strip() if phone_match else None

    # Headline
    headline: Optional[str] = None
    if len(header_lines) >= 2:
        for line in header_lines[1:4]:
            if line.title() != name and not EMAIL_REGEX.search(line) and not PHONE_REGEX.search(line) and len(line) < 100:
                headline = line
                break

    # Social links
    links: List[Dict[str, str]] = []
    platforms = load_platforms()
    for pid, pdata in platforms.items():
        if pid in ("email", "phone"):
            continue
        # Search for domain pattern
        if pid == "github":
            gh_m = re.search(r"github\.com/([a-zA-Z0-9_-]+)", raw_text, re.IGNORECASE)
            if gh_m:
                links.append({"platform_id": "github", "value": gh_m.group(1)})
        elif pid == "linkedin":
            li_m = re.search(r"linkedin\.com/in/([a-zA-Z0-9_-]+)", raw_text, re.IGNORECASE)
            if li_m:
                links.append({"platform_id": "linkedin", "value": li_m.group(1)})
        elif pid == "leetcode":
            lc_m = re.search(r"leetcode\.com/(?:u/)?([a-zA-Z0-9_-]+)", raw_text, re.IGNORECASE)
            if lc_m:
                links.append({"platform_id": "leetcode", "value": lc_m.group(1)})

    # Summary
    summary_lines = sections.get("summary", [])
    summary = " ".join(summary_lines).strip() if summary_lines else None

    # 3. Extract Skills
    skill_to_cat = _load_catalog_lookup()
    extracted = extract_skills(raw_text, mode="baseline")
    skills_list: List[Dict[str, Any]] = []
    seen_skills: Set[str] = set()

    for sid in extracted.skills:
        cat_id = skill_to_cat.get(sid.lower(), "other_tools")
        display_name = sid.replace("_", " ").title()
        if sid.lower() not in seen_skills:
            seen_skills.add(sid.lower())
            skills_list.append({
                "category_id": cat_id,
                "name": display_name,
                "taxonomy_id": sid,
                "custom": False,
                "pinned": False,
                "level": "comfortable",
            })

    if not skills_list:
        needs_review.append({
            "field": "skills",
            "reason": "No technical skills were automatically identified. Please select your skills from the catalog.",
        })

    # 4. Extract Experience
    exp_lines = sections.get("experience", [])
    experience_list: List[Dict[str, Any]] = []
    current_entry: Optional[Dict[str, Any]] = None

    for line in exp_lines:
        clean = line.strip()
        if not clean:
            continue

        # Check for date range indicating new entry
        date_match = DATE_RANGE_REGEX.search(clean)
        is_bullet = clean.startswith(("-", "*", "•", "–")) or re.match(r"^\d+\.\s+", clean)

        if date_match and not is_bullet:
            if current_entry:
                experience_list.append(current_entry)
            start_raw, end_raw = date_match.group(1), date_match.group(2)
            # Remove date string from line to isolate title/company
            line_sans_date = clean[:date_match.start()] + clean[date_match.end():]
            tokens = [t.strip() for t in re.split(r"[-–—|,]", line_sans_date) if t.strip()]

            title = tokens[0] if tokens else "Software Engineer"
            company = tokens[1] if len(tokens) > 1 else "Company"

            current_entry = {
                "title": title[:100],
                "company": company[:100],
                "start": _normalize_date_str(start_raw),
                "end": _normalize_date_str(end_raw),
                "current": end_raw.lower() in ("present", "current"),
                "bullets": [],
            }
        elif current_entry is not None:
            # Bullet point or descriptive line
            bullet_text = re.sub(r"^[-*•–\d.]+\s*", "", clean).strip()
            if bullet_text:
                if len(bullet_text) > 300:
                    bullet_text = bullet_text[:297] + "..."
                    needs_review.append({
                        "field": f"experience[{len(experience_list)}].bullets",
                        "reason": f"Bullet point exceeded 300 characters and was truncated.",
                    })
                if len(current_entry["bullets"]) < 8:
                    current_entry["bullets"].append(bullet_text)
        else:
            # If no current entry yet, start a generic one
            tokens = [t.strip() for t in re.split(r"[-–—|,]", clean) if t.strip()]
            if tokens and not is_bullet:
                current_entry = {
                    "title": tokens[0][:100],
                    "company": tokens[1][:100] if len(tokens) > 1 else "Company",
                    "start": None,
                    "end": None,
                    "current": False,
                    "bullets": [],
                }

    if current_entry:
        experience_list.append(current_entry)

    # 5. Extract Education
    edu_lines = sections.get("education", [])
    education_list: List[Dict[str, Any]] = []
    current_edu: Optional[Dict[str, Any]] = None

    for line in edu_lines:
        clean = line.strip()
        if not clean:
            continue

        year_match = YEAR_REGEX.search(clean)
        is_bullet = clean.startswith(("-", "*", "•", "–"))

        if ("university" in clean.lower() or "college" in clean.lower() or "institute" in clean.lower()) and not is_bullet:
            if current_edu:
                education_list.append(current_edu)
            current_edu = {
                "school": clean[:120],
                "degree": "Bachelor of Science",
                "field": "Computer Science",
                "start": None,
                "end": year_match.group(1) if year_match else None,
                "score": None,
                "details": [],
            }
        elif current_edu is not None:
            if any(deg in clean.lower() for deg in ("bachelor", "master", "b.tech", "m.tech", "b.s.", "m.s.", "ph.d")):
                current_edu["degree"] = clean[:100]
            elif is_bullet:
                det = re.sub(r"^[-*•–\d.]+\s*", "", clean).strip()
                if det and len(current_edu["details"]) < 8:
                    current_edu["details"].append(det[:300])

    if current_edu:
        education_list.append(current_edu)

    # 6. Extract Projects
    proj_lines = sections.get("projects", [])
    projects_list: List[Dict[str, Any]] = []
    current_proj: Optional[Dict[str, Any]] = None

    for line in proj_lines:
        clean = line.strip()
        if not clean:
            continue
        is_bullet = clean.startswith(("-", "*", "•", "–"))

        if not is_bullet and len(clean) < 80:
            if current_proj:
                projects_list.append(current_proj)
            current_proj = {
                "name": clean[:100],
                "tech": [],
                "bullets": [],
            }
        elif current_proj is not None:
            b_text = re.sub(r"^[-*•–\d.]+\s*", "", clean).strip()
            if b_text and len(current_proj["bullets"]) < 8:
                current_proj["bullets"].append(b_text[:300])

    if current_proj:
        projects_list.append(current_proj)

    # Assemble and validate partial draft
    draft_dict: Dict[str, Any] = {
        "meta": {"template": "classic"},
        "basics": {
            "name": name,
            "email": email,
            "headline": headline,
            "phone": phone,
            "location": None,
            "links": links,
        },
        "summary": summary,
        "skills": skills_list[:50],
        "experience": experience_list[:10],
        "projects": projects_list[:10],
        "education": education_list[:5],
        "certifications": [],
        "achievements": [],
        "publications": [],
        "custom_sections": [],
    }

    # Validate against Resume schema
    try:
        validated = Resume.model_validate(draft_dict)
        return {
            "resume": validated.model_dump(),
            "needs_review": needs_review,
        }
    except Exception as exc:
        logger.warning(f"Draft validation had issues: {exc}")
        needs_review.append({
            "field": "root",
            "reason": f"Partial draft generated with formatting warnings: {exc}",
        })
        return {
            "resume": draft_dict,
            "needs_review": needs_review,
        }
