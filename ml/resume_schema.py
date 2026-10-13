"""Standard Resume Schema (Pydantic v2) for SkillGap Resume Builder.

Enforces:
- Statelessness & Zero-PII collection rules:
  strictly prohibits photo, date of birth, gender, marital status,
  religion, nationality, full home address, or government IDs.
- Name and Email are the only mandatory fields; all others are optional.
- Automatic HTML tag stripping and control character sanitization.
- Strict date validation: "YYYY-MM", "YYYY", or "Present".
- Exact section and bullet length constraints.
"""

from __future__ import annotations

import html
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional, Set

from pydantic import (
    BaseModel,
    ConfigDict,
    EmailStr,
    Field,
    field_validator,
    model_validator,
)

DATE_PATTERN = re.compile(r"^(?:Present|\d{4}-\d{2}|\d{4})$")

FORBIDDEN_PII_FIELDS: Set[str] = {
    "photo",
    "avatar",
    "image",
    "picture",
    "dob",
    "date_of_birth",
    "birth_date",
    "gender",
    "sex",
    "marital_status",
    "marital",
    "religion",
    "religious",
    "nationality",
    "citizenship",
    "address",
    "home_address",
    "street_address",
    "postal_code",
    "zip_code",
    "ssn",
    "aadhaar",
    "passport",
    "id_number",
    "national_id",
}


def sanitize_string(val: str) -> str:
    """Strip HTML tags, control characters, and unescape entities."""
    if not isinstance(val, str):
        return val
    # Strip HTML tags
    text = re.sub(r"<[^>]+>", "", val)
    # Strip ASCII control characters (keep newline and tab)
    text = re.sub(r"[\x00-\x08\x0b\x0c\x0e-\x1f\x7f]", "", text)
    # Unescape HTML entities
    text = html.unescape(text)
    return text.strip()


def validate_date_string(val: Optional[str]) -> Optional[str]:
    """Validate date format to 'YYYY-MM', 'YYYY', or 'Present'."""
    if val is None:
        return None
    val = sanitize_string(val)
    if not val:
        return None
    if not DATE_PATTERN.match(val):
        raise ValueError(f"Invalid date '{val}'. Dates must match 'YYYY-MM', 'YYYY', or 'Present'.")
    return val


def validate_bullet_string(val: str) -> str:
    """Sanitize and ensure bullet point is <= 300 characters."""
    clean = sanitize_string(val)
    if len(clean) > 300:
        raise ValueError(f"Bullet point exceeds 300 character limit ({len(clean)} chars): '{clean[:40]}...'")
    return clean


class BaseCleanModel(BaseModel):
    """Base model enforcing forbidden fields check, extra forbidden, and string sanitization."""

    model_config = ConfigDict(
        extra="forbid",
        str_strip_whitespace=True,
        validate_assignment=True,
    )

    @model_validator(mode="before")
    @classmethod
    def check_forbidden_fields_and_sanitize(cls, data: Any) -> Any:
        if not isinstance(data, dict):
            return data

        # Check for forbidden fields
        for key in data.keys():
            lower_key = str(key).lower()
            if lower_key in FORBIDDEN_PII_FIELDS:
                raise ValueError(
                    f"Forbidden field '{key}' detected. SkillGap strictly prohibits collecting "
                    f"photos, dates of birth, gender, nationality, religion, home address, or government IDs."
                )

        # Sanitize strings recursively
        sanitized: Dict[str, Any] = {}
        for k, v in data.items():
            if isinstance(v, str):
                sanitized[k] = sanitize_string(v)
            elif isinstance(v, list):
                sanitized[k] = [
                    sanitize_string(item) if isinstance(item, str) else item
                    for item in v
                ]
            else:
                sanitized[k] = v
        return sanitized


class Meta(BaseCleanModel):
    template: str = Field(default="modern", max_length=50)
    target_role: Optional[str] = Field(default=None, max_length=100)


class Location(BaseCleanModel):
    city: Optional[str] = Field(default=None, max_length=100)
    region_country: Optional[str] = Field(default=None, max_length=100)


class SocialLink(BaseCleanModel):
    platform_id: str = Field(..., max_length=50)
    value: str = Field(..., max_length=200)

    @field_validator("platform_id", mode="before")
    @classmethod
    def normalize_pid(cls, v: str) -> str:
        return str(v).strip().lower()


class Basics(BaseCleanModel):
    name: str = Field(..., min_length=1, max_length=120, description="Full name of candidate")
    email: str = Field(..., description="Contact email address")
    headline: Optional[str] = Field(default=None, max_length=150)
    phone: Optional[str] = Field(default=None, max_length=50)
    location: Optional[Location] = None
    links: List[SocialLink] = Field(default_factory=list, max_length=15)

    @field_validator("email", mode="before")
    @classmethod
    def validate_email_format(cls, v: str) -> str:
        clean = sanitize_string(v)
        if not re.match(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$", clean):
            raise ValueError(f"Invalid email address: '{clean}'")
        return clean


class SkillItem(BaseCleanModel):
    category_id: str = Field(..., max_length=50)
    name: str = Field(..., min_length=1, max_length=100)
    taxonomy_id: Optional[str] = Field(default=None, max_length=100)
    custom: bool = False
    pinned: bool = False
    level: Optional[
        Literal[
            "familiar",
            "comfortable",
            "strong",
            "beginner",
            "intermediate",
            "advanced",
            "expert",
        ]
    ] = None


class ExperienceItem(BaseCleanModel):
    company: str = Field(..., min_length=1, max_length=120)
    title: str = Field(..., min_length=1, max_length=120)
    location: Optional[str] = Field(default=None, max_length=100)
    start: Optional[str] = None
    end: Optional[str] = None
    current: bool = False
    bullets: List[str] = Field(default_factory=list, max_length=8)

    @field_validator("start", "end", mode="before")
    @classmethod
    def validate_dates(cls, v: Optional[str]) -> Optional[str]:
        return validate_date_string(v)

    @field_validator("bullets", mode="before")
    @classmethod
    def validate_bullets(cls, v: List[str]) -> List[str]:
        if not v:
            return []
        return [validate_bullet_string(b) for b in v]


class ProjectItem(BaseCleanModel):
    name: str = Field(..., min_length=1, max_length=120)
    link: Optional[str] = Field(default=None, max_length=250)
    tech: List[str] = Field(default_factory=list, max_length=30)
    bullets: List[str] = Field(default_factory=list, max_length=8)

    @field_validator("bullets", mode="before")
    @classmethod
    def validate_bullets(cls, v: List[str]) -> List[str]:
        if not v:
            return []
        return [validate_bullet_string(b) for b in v]


class EducationItem(BaseCleanModel):
    school: str = Field(..., min_length=1, max_length=150)
    degree: Optional[str] = Field(default=None, max_length=100)
    field: Optional[str] = Field(default=None, max_length=100)
    start: Optional[str] = None
    end: Optional[str] = None
    score: Optional[str] = Field(default=None, max_length=50)
    details: List[str] = Field(default_factory=list, max_length=8)

    @field_validator("start", "end", mode="before")
    @classmethod
    def validate_dates(cls, v: Optional[str]) -> Optional[str]:
        return validate_date_string(v)

    @field_validator("details", mode="before")
    @classmethod
    def validate_details(cls, v: List[str]) -> List[str]:
        if not v:
            return []
        return [validate_bullet_string(d) for d in v]


class CertificationItem(BaseCleanModel):
    name: str = Field(..., min_length=1, max_length=150)
    issuer: Optional[str] = Field(default=None, max_length=120)
    date: Optional[str] = None

    @field_validator("date", mode="before")
    @classmethod
    def validate_dates(cls, v: Optional[str]) -> Optional[str]:
        return validate_date_string(v)


class PublicationItem(BaseCleanModel):
    title: str = Field(..., min_length=1, max_length=250)
    venue: Optional[str] = Field(default=None, max_length=150)
    year: Optional[str] = None
    link: Optional[str] = Field(default=None, max_length=250)

    @field_validator("year", mode="before")
    @classmethod
    def validate_year(cls, v: Optional[Any]) -> Optional[str]:
        if v is None:
            return None
        return validate_date_string(str(v))


class CustomSectionItem(BaseCleanModel):
    title: str = Field(..., min_length=1, max_length=100)
    bullets: List[str] = Field(default_factory=list, max_length=8)

    @field_validator("bullets", mode="before")
    @classmethod
    def validate_bullets(cls, v: List[str]) -> List[str]:
        if not v:
            return []
        return [validate_bullet_string(b) for b in v]


class Resume(BaseCleanModel):
    """Complete Resume representation."""

    meta: Meta = Field(default_factory=Meta)
    basics: Basics
    summary: Optional[str] = Field(default=None, max_length=2000)
    skills: List[SkillItem] = Field(default_factory=list, max_length=150)
    experience: List[ExperienceItem] = Field(default_factory=list, max_length=15)
    projects: List[ProjectItem] = Field(default_factory=list, max_length=15)
    education: List[EducationItem] = Field(default_factory=list, max_length=15)
    certifications: List[CertificationItem] = Field(default_factory=list, max_length=15)
    achievements: List[str] = Field(default_factory=list, max_length=15)
    publications: List[PublicationItem] = Field(default_factory=list, max_length=15)
    custom_sections: List[CustomSectionItem] = Field(default_factory=list, max_length=15)

    @field_validator("achievements", mode="before")
    @classmethod
    def validate_achievements(cls, v: List[str]) -> List[str]:
        if not v:
            return []
        return [validate_bullet_string(a) for a in v]


def export_json_schema(target_file: Optional[Path] = None) -> Dict[str, Any]:
    """Export standard JSON Schema for the Resume model."""
    schema = Resume.model_json_schema()
    if target_file is not None:
        target_file.parent.mkdir(parents=True, exist_ok=True)
        with open(target_file, "w", encoding="utf-8") as f:
            json.dump(schema, f, indent=2)
    return schema
