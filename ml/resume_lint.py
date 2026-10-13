"""Deterministic Resume Linter for SkillGap Resume Builder.

Validates resumes against professional ATS best practices and structural integrity.
Produces categorized findings:
- error: Critical defects preventing a valid ATS submission
- warning: Issues that weaken the resume or violate hiring guidelines
- tip: Stylistic or strategic enhancements to improve impact
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Union

from ml.resume_schema import Resume, sanitize_string

RULES_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "resume_rules.json"
PLATFORMS_PATH = Path(__file__).resolve().parent.parent / "data" / "processed" / "social_platforms.json"

# Load rules and platform metadata
def _load_rules() -> Dict[str, Any]:
    if RULES_PATH.exists():
        with open(RULES_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "weak_phrases": ["responsible for", "duties included", "worked on", "helped with", "assisted with", "tasked with", "handled"],
        "first_person_pronouns": ["i", "me", "my", "myself", "we", "us", "our", "ours", "ourselves"],
        "non_resume_platforms": ["discord", "reddit", "quora", "instagram", "facebook", "tiktok", "twitch", "pinterest"],
        "action_verbs": ["built", "designed", "developed", "led", "managed", "optimized", "spearheaded"],
    }


def _load_non_resume_platforms() -> Set[str]:
    platforms_set = set(_load_rules().get("non_resume_platforms", []))
    if PLATFORMS_PATH.exists():
        try:
            with open(PLATFORMS_PATH, "r", encoding="utf-8") as f:
                data = json.load(f)
                for item in data:
                    if not item.get("resume_friendly", True):
                        platforms_set.add(item["id"].lower())
        except Exception:
            pass
    return platforms_set


METRIC_REGEX = re.compile(r"(\d+(?:\.\d+)?%?|\$|€|£|₹|\b\d+x\b|\b\d+\b)")
PHONE_REGEX = re.compile(r"^\+?[0-9\s().-]{7,25}$")
EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")
SENTENCE_SPLIT_REGEX = re.compile(r"(?<=[.!?])\s+")
PRONOUN_REGEX = re.compile(r"\b(i|me|my|myself|we|us|our|ours|ourselves)\b", re.IGNORECASE)


def _to_dict(resume: Union[Resume, Dict[str, Any]]) -> Dict[str, Any]:
    if isinstance(resume, Resume):
        return resume.model_dump()
    elif isinstance(resume, dict):
        return resume
    else:
        raise ValueError(f"Expected Resume model or dict, got {type(resume).__name__}")


def lint(resume: Union[Resume, Dict[str, Any]]) -> List[Dict[str, str]]:
    """Lint resume and return list of {level, section, message, path}."""
    issues: List[Dict[str, str]] = []
    rules = _load_rules()
    non_resume_platforms = _load_non_resume_platforms()
    weak_phrases = [wp.lower() for wp in rules.get("weak_phrases", [])]

    # Normalize data
    try:
        data = _to_dict(resume)
    except Exception as exc:
        return [{
            "level": "error",
            "section": "meta",
            "message": f"Malformed resume payload: {exc}",
            "path": "root",
        }]

    basics = data.get("basics") or {}
    skills = data.get("skills") or []
    experience = data.get("experience") or []
    projects = data.get("projects") or []
    education = data.get("education") or []
    certifications = data.get("certifications") or []
    achievements = data.get("achievements") or []
    publications = data.get("publications") or []
    custom_sections = data.get("custom_sections") or []
    summary = data.get("summary") or basics.get("summary") or ""

    # ==========================================
    # 1. ERRORS
    # ==========================================

    # Name check
    name = (basics.get("name") or "").strip()
    if not name:
        issues.append({
            "level": "error",
            "section": "basics",
            "message": "Candidate name is missing. A full name is mandatory for an ATS resume.",
            "path": "basics.name",
        })

    # Email check
    email = (basics.get("email") or "").strip()
    if not email:
        issues.append({
            "level": "error",
            "section": "basics",
            "message": "Contact email is missing. A valid email address is mandatory for recruiters to reach you.",
            "path": "basics.email",
        })
    elif not EMAIL_REGEX.match(email):
        issues.append({
            "level": "error",
            "section": "basics",
            "message": f"Email '{email}' is not in a valid format (e.g., user@example.com).",
            "path": "basics.email",
        })

    # Phone check (if provided)
    phone = (basics.get("phone") or "").strip()
    if phone and not PHONE_REGEX.match(phone):
        issues.append({
            "level": "error",
            "section": "basics",
            "message": f"Phone number '{phone}' appears invalid. Please include standard country/area code and digits.",
            "path": "basics.phone",
        })

    # Empty required fields & End before start in Experience
    for idx, exp in enumerate(experience):
        c_name = (exp.get("company") or "").strip()
        title = (exp.get("title") or "").strip()
        if not c_name:
            issues.append({
                "level": "error",
                "section": "experience",
                "message": f"Work experience entry #{idx+1} is missing a company name.",
                "path": f"experience[{idx}].company",
            })
        if not title:
            issues.append({
                "level": "error",
                "section": "experience",
                "message": f"Work experience entry #{idx+1} at '{c_name or 'Unknown'}' is missing a job title.",
                "path": f"experience[{idx}].title",
            })

        start = (exp.get("start") or "").strip()
        end = (exp.get("end") or "").strip()
        if start and end and end != "Present":
            # Compare dates (both YYYY or YYYY-MM)
            if start > end:
                issues.append({
                    "level": "error",
                    "section": "experience",
                    "message": f"End date ({end}) cannot be earlier than start date ({start}) for {title or c_name}.",
                    "path": f"experience[{idx}].end",
                })

    # Empty required fields & End before start in Education
    for idx, edu in enumerate(education):
        school = (edu.get("school") or "").strip()
        if not school:
            issues.append({
                "level": "error",
                "section": "education",
                "message": f"Education entry #{idx+1} is missing the institution/school name.",
                "path": f"education[{idx}].school",
            })
        start = (edu.get("start") or "").strip()
        end = (edu.get("end") or "").strip()
        if start and end and end != "Present":
            if start > end:
                issues.append({
                    "level": "error",
                    "section": "education",
                    "message": f"End date ({end}) cannot be earlier than start date ({start}) for {school}.",
                    "path": f"education[{idx}].end",
                })

    # Empty required fields in Projects
    for idx, proj in enumerate(projects):
        p_name = (proj.get("name") or "").strip()
        if not p_name:
            issues.append({
                "level": "error",
                "section": "projects",
                "message": f"Project entry #{idx+1} is missing a project name.",
                "path": f"projects[{idx}].name",
            })

    # Empty required fields in Skills
    for idx, sk in enumerate(skills):
        sk_name = (sk.get("name") if isinstance(sk, dict) else str(sk)).strip()
        if not sk_name:
            issues.append({
                "level": "error",
                "section": "skills",
                "message": f"Skill item #{idx+1} has an empty name.",
                "path": f"skills[{idx}].name",
            })

    # Bullet length check (> 300 chars is an error)
    def _check_bullet_lengths(bullets: List[str], path_prefix: str, sec: str):
        for b_idx, bullet in enumerate(bullets):
            clean_b = sanitize_string(bullet)
            if len(clean_b) > 300:
                issues.append({
                    "level": "error",
                    "section": sec,
                    "message": f"Bullet exceeds 300 character limit ({len(clean_b)} characters): '{clean_b[:50]}...'",
                    "path": f"{path_prefix}.bullets[{b_idx}]",
                })

    for idx, exp in enumerate(experience):
        _check_bullet_lengths(exp.get("bullets", []), f"experience[{idx}]", "experience")
    for idx, proj in enumerate(projects):
        _check_bullet_lengths(proj.get("bullets", []), f"projects[{idx}]", "projects")
    for idx, edu in enumerate(education):
        _check_bullet_lengths(edu.get("details", []), f"education[{idx}]", "education")
    for b_idx, ach in enumerate(achievements):
        if len(sanitize_string(ach)) > 300:
            issues.append({
                "level": "error",
                "section": "achievements",
                "message": f"Achievement bullet exceeds 300 character limit ({len(ach)} chars).",
                "path": f"achievements[{b_idx}]",
            })
    for idx, cust in enumerate(custom_sections):
        _check_bullet_lengths(cust.get("bullets", []), f"custom_sections[{idx}]", "custom_sections")

    # ==========================================
    # 2. WARNINGS
    # ==========================================

    # Page estimate: more than 2 pages worth of content
    total_bullets = (
        sum(len(e.get("bullets", [])) for e in experience)
        + sum(len(p.get("bullets", [])) for p in projects)
        + sum(len(e.get("details", [])) for e in education)
        + len(achievements)
        + sum(len(c.get("bullets", [])) for c in custom_sections)
    )
    raw_text_parts = [
        name,
        summary,
        " ".join((s.get("name", "") if isinstance(s, dict) else str(s)) for s in skills),
        " ".join(" ".join(e.get("bullets", [])) for e in experience),
        " ".join(" ".join(p.get("bullets", [])) for p in projects),
        " ".join(" ".join(e.get("details", [])) for e in education),
        " ".join(achievements),
    ]
    total_words = len(" ".join(raw_text_parts).split())
    if total_words > 850 or total_bullets > 25:
        issues.append({
            "level": "warning",
            "section": "meta",
            "message": f"Resume content ({total_words} words, {total_bullets} bullets) is likely to exceed 2 pages. Consider condensing bullets to keep within 1-2 pages.",
            "path": "root",
        })

    # Entry with no bullets & more than 8 bullets in one entry
    for idx, exp in enumerate(experience):
        b_count = len(exp.get("bullets", []))
        if b_count == 0:
            issues.append({
                "level": "warning",
                "section": "experience",
                "message": f"Experience at '{exp.get('company', f'#{idx+1}')}' has no bullet points describing your achievements.",
                "path": f"experience[{idx}].bullets",
            })
        elif b_count > 8:
            issues.append({
                "level": "warning",
                "section": "experience",
                "message": f"Experience at '{exp.get('company', f'#{idx+1}')}' has {b_count} bullets. ATS best practice recommends 3 to 8 focused bullets per role.",
                "path": f"experience[{idx}].bullets",
            })

    for idx, proj in enumerate(projects):
        b_count = len(proj.get("bullets", []))
        if b_count == 0:
            issues.append({
                "level": "warning",
                "section": "projects",
                "message": f"Project '{proj.get('name', f'#{idx+1}')}' has no bullet points describing work done.",
                "path": f"projects[{idx}].bullets",
            })
        elif b_count > 8:
            issues.append({
                "level": "warning",
                "section": "projects",
                "message": f"Project '{proj.get('name', f'#{idx+1}')}' has {b_count} bullets. Keep to under 8 concise bullets.",
                "path": f"projects[{idx}].bullets",
            })

    # Bullets starting with a weak phrase & First-person pronouns in bullets
    def _inspect_bullets_for_style(bullets: List[str], path_prefix: str, sec: str):
        for b_idx, bullet in enumerate(bullets):
            clean = sanitize_string(bullet).strip()
            if not clean:
                continue

            # Weak phrase start check
            lower = clean.lower()
            for wp in weak_phrases:
                if lower.startswith(wp):
                    issues.append({
                        "level": "warning",
                        "section": sec,
                        "message": f"Bullet starts with weak phrase '{wp}'. Replace with a strong action verb (e.g., Architected, Spearheaded, Accelerated).",
                        "path": f"{path_prefix}.bullets[{b_idx}]",
                    })
                    break

            # First-person pronoun check
            found_pronouns = PRONOUN_REGEX.findall(clean)
            if found_pronouns:
                unique_p = sorted(set(p.lower() for p in found_pronouns))
                issues.append({
                    "level": "warning",
                    "section": sec,
                    "message": f"Avoid first-person pronouns ({', '.join(unique_p)}) in resume bullets. Use direct action verb phrasing.",
                    "path": f"{path_prefix}.bullets[{b_idx}]",
                })

    for idx, exp in enumerate(experience):
        _inspect_bullets_for_style(exp.get("bullets", []), f"experience[{idx}]", "experience")
    for idx, proj in enumerate(projects):
        _inspect_bullets_for_style(proj.get("bullets", []), f"projects[{idx}]", "projects")
    for idx, edu in enumerate(education):
        _inspect_bullets_for_style(edu.get("details", []), f"education[{idx}]", "education")
    for idx, cust in enumerate(custom_sections):
        _inspect_bullets_for_style(cust.get("bullets", []), f"custom_sections[{idx}]", "custom_sections")

    # Inconsistent date formats
    all_dates: List[str] = []
    for exp in experience:
        if exp.get("start"): all_dates.append(exp["start"])
        if exp.get("end") and exp["end"] != "Present": all_dates.append(exp["end"])
    for edu in education:
        if edu.get("start"): all_dates.append(edu["start"])
        if edu.get("end") and edu["end"] != "Present": all_dates.append(edu["end"])
    for cert in certifications:
        if cert.get("date"): all_dates.append(cert["date"])
    for pub in publications:
        if pub.get("year"): all_dates.append(pub["year"])

    date_formats: Set[str] = set()
    for d in all_dates:
        if re.match(r"^\d{4}-\d{2}$", d):
            date_formats.add("YYYY-MM")
        elif re.match(r"^\d{4}$", d):
            date_formats.add("YYYY")
    if len(date_formats) > 1:
        issues.append({
            "level": "warning",
            "section": "meta",
            "message": "Inconsistent date formats detected across entries (both 'YYYY-MM' and 'YYYY' used). Choose one consistent style.",
            "path": "root",
        })

    # Duplicate skills
    seen_skill_names: Set[str] = set()
    seen_tax_ids: Set[str] = set()
    for idx, sk in enumerate(skills):
        name_val = (sk.get("name", "") if isinstance(sk, dict) else str(sk)).strip().lower()
        tax_val = sk.get("taxonomy_id", "").strip().lower() if isinstance(sk, dict) and sk.get("taxonomy_id") else None

        if name_val in seen_skill_names:
            issues.append({
                "level": "warning",
                "section": "skills",
                "message": f"Duplicate skill '{sk.get('name')}' found in skills list.",
                "path": f"skills[{idx}]",
            })
        seen_skill_names.add(name_val)

        if tax_val:
            if tax_val in seen_tax_ids:
                issues.append({
                    "level": "warning",
                    "section": "skills",
                    "message": f"Duplicate skill taxonomy ID '{tax_val}' found.",
                    "path": f"skills[{idx}].taxonomy_id",
                })
            seen_tax_ids.add(tax_val)

    # Link from non-resume-friendly platform
    links = basics.get("links") or []
    for idx, lk in enumerate(links):
        pid = (lk.get("platform_id") or "").strip().lower()
        if pid in non_resume_platforms:
            issues.append({
                "level": "warning",
                "section": "basics",
                "message": f"Link '{pid}' is from a non-resume-friendly or casual social platform. Keep links professional (e.g., GitHub, LinkedIn, Portfolio).",
                "path": f"basics.links[{idx}].platform_id",
            })

    # ==========================================
    # 3. TIPS
    # ==========================================

    # Bullets with no number or outcome
    def _inspect_bullets_for_metrics(bullets: List[str], path_prefix: str, sec: str):
        for b_idx, bullet in enumerate(bullets):
            clean = sanitize_string(bullet).strip()
            if not clean:
                continue
            if not METRIC_REGEX.search(clean):
                issues.append({
                    "level": "tip",
                    "section": sec,
                    "message": "Add a number or quantifiable outcome if you have one (e.g., 'reduced latency by 35%').",
                    "path": f"{path_prefix}.bullets[{b_idx}]",
                })

    for idx, exp in enumerate(experience):
        _inspect_bullets_for_metrics(exp.get("bullets", []), f"experience[{idx}]", "experience")
    for idx, proj in enumerate(projects):
        _inspect_bullets_for_metrics(proj.get("bullets", []), f"projects[{idx}]", "projects")

    # Summary longer than 4 sentences
    if summary:
        sentences = [s.strip() for s in SENTENCE_SPLIT_REGEX.split(summary) if s.strip()]
        if len(sentences) > 4:
            issues.append({
                "level": "tip",
                "section": "summary",
                "message": f"Summary is {len(sentences)} sentences long. Professional summaries should ideally be 2 to 4 concise sentences.",
                "path": "summary",
            })

    # Fewer than 5 skills
    if len(skills) < 5:
        issues.append({
            "level": "tip",
            "section": "skills",
            "message": f"You have listed {len(skills)} skills. Adding at least 5 relevant technical skills improves ATS search matching.",
            "path": "skills",
        })

    # Skills not used anywhere in experience or projects
    combined_body = (
        " ".join(" ".join(e.get("bullets", [])) + " " + e.get("title", "") for e in experience)
        + " "
        + " ".join(" ".join(p.get("bullets", [])) + " " + " ".join(p.get("tech", [])) + " " + p.get("name", "") for p in projects)
    ).lower()

    for idx, sk in enumerate(skills):
        sk_raw = (sk.get("name", "") if isinstance(sk, dict) else str(sk)).strip()
        sk_norm = sk_raw.lower()
        if sk_norm and sk_norm not in combined_body:
            issues.append({
                "level": "tip",
                "section": "skills",
                "message": f"Skill '{sk_raw}' is listed but not mentioned in your experience or project bullets. Consider demonstrating how you used it.",
                "path": f"skills[{idx}]",
            })

    # Same starting verb used 3+ times
    starting_verbs: Dict[str, int] = {}
    all_experience_and_proj_bullets: List[str] = []
    for exp in experience:
        all_experience_and_proj_bullets.extend(exp.get("bullets", []))
    for proj in projects:
        all_experience_and_proj_bullets.extend(proj.get("bullets", []))

    for b in all_experience_and_proj_bullets:
        clean_words = sanitize_string(b).strip().split()
        if clean_words:
            first_word = re.sub(r"[^a-zA-Z]", "", clean_words[0]).lower()
            if len(first_word) >= 3:
                starting_verbs[first_word] = starting_verbs.get(first_word, 0) + 1

    for verb, count in starting_verbs.items():
        if count >= 3:
            issues.append({
                "level": "tip",
                "section": "experience",
                "message": f"The starting verb '{verb.capitalize()}' is used {count} times across your bullets. Vary your verbs to make your resume dynamic.",
                "path": "experience.bullets",
            })

    return issues
