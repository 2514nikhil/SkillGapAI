"""Social media and professional platform URL parsing, extraction, and validation.

Supports normalization, stripping prefixes/query parameters, building valid URLs,
and validating platform identifiers. Never fetches URLs.
"""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional
from urllib.parse import parse_qs, urlparse, urlunparse

PLATFORMS_FILE = Path(__file__).resolve().parent.parent / "data" / "processed" / "social_platforms.json"

_PLATFORMS_CACHE: Optional[Dict[str, Dict[str, Any]]] = None


def load_platforms() -> Dict[str, Dict[str, Any]]:
    """Load social platform definitions from JSON cache."""
    global _PLATFORMS_CACHE
    if _PLATFORMS_CACHE is not None:
        return _PLATFORMS_CACHE

    if not PLATFORMS_FILE.exists():
        raise FileNotFoundError(f"Social platforms file not found at {PLATFORMS_FILE}")

    with open(PLATFORMS_FILE, "r", encoding="utf-8") as f:
        data: List[Dict[str, Any]] = json.load(f)

    _PLATFORMS_CACHE = {p["id"]: p for p in data}
    return _PLATFORMS_CACHE


def get_platform(platform_id: str) -> Dict[str, Any]:
    """Retrieve platform definition by id."""
    platforms = load_platforms()
    if platform_id not in platforms:
        raise ValueError(f"Unknown social platform ID: '{platform_id}'")
    return platforms[platform_id]


def extract_value(platform_id: str, text_or_url: str) -> str:
    """Extract normalized platform value/handle from raw user input or full URL.

    Strips '@', protocol, tracking query parameters, and trailing slashes.
    """
    if not text_or_url:
        return ""

    raw = text_or_url.strip()
    platform = get_platform(platform_id)

    # 1. Email handling
    if platform_id == "email":
        if raw.lower().startswith("mailto:"):
            raw = raw[7:]
        # Strip query parameters like ?subject=...
        if "?" in raw:
            raw = raw.split("?")[0]
        return raw.strip()

    # 2. Phone handling
    if platform_id == "phone":
        if raw.lower().startswith("tel:"):
            raw = raw[4:]
        if "?" in raw:
            raw = raw.split("?")[0]
        return raw.strip()

    # 3. Portfolio handling (keep full URL, normalize protocol)
    if platform_id == "portfolio":
        # Strip query parameters if they are common tracking params
        # But preserve paths e.g. /projects
        if not re.match(r"^https?://", raw, re.IGNORECASE):
            raw = "https://" + raw
        parsed = urlparse(raw)
        # Strip tracking query params
        clean_path = parsed.path.rstrip("/")
        clean_url = urlunparse((parsed.scheme, parsed.netloc, clean_path, "", "", ""))
        return clean_url

    # 4. Mastodon handling (user@instance or https://instance/@user)
    if platform_id == "mastodon":
        raw = raw.strip()
        if raw.startswith("http://") or raw.startswith("https://"):
            parsed = urlparse(raw)
            instance = parsed.netloc
            path = parsed.path.strip("/")
            # path is typically @username
            username = path.lstrip("@")
            if username and instance:
                return f"{username}@{instance}"
        # user@instance format
        raw = raw.lstrip("@")
        return raw

    # 5. Google Scholar handling
    if platform_id == "google_scholar":
        if "scholar.google." in raw:
            parsed = urlparse(raw)
            qs = parse_qs(parsed.query)
            if "user" in qs and qs["user"]:
                return qs["user"][0]
        return raw.strip()

    # 6. Stack Overflow handling (numeric user ID)
    if platform_id == "stackoverflow":
        # Can be https://stackoverflow.com/users/12345/user-name or just 12345
        m = re.search(r"/users/(\d+)", raw)
        if m:
            return m.group(1)
        m_num = re.search(r"^\d+$", raw.strip())
        if m_num:
            return m_num.group(0)
        return raw.strip()

    # 7. YouTube handling
    if platform_id == "youtube":
        if "youtube.com" in raw or "youtu.be" in raw:
            parsed = urlparse(raw)
            path = parsed.path.strip("/")
            if path.startswith("channel/"):
                return path.split("channel/")[1].split("/")[0]
            if path.startswith("@"):
                return path.split("/")[0]
            if path.startswith("c/") or path.startswith("user/"):
                return path.split("/")[1]
            if path:
                return path.split("/")[0]
        raw = raw.strip()
        return raw

    # General URL stripping for other platforms
    if raw.startswith("http://") or raw.startswith("https://"):
        parsed = urlparse(raw)
        path = parsed.path.strip("/")
        # Platform-specific path parsing
        if platform_id == "linkedin":
            # https://linkedin.com/in/username
            if path.startswith("in/"):
                path = path[3:]
        elif platform_id == "leetcode":
            # https://leetcode.com/u/username or https://leetcode.com/username
            if path.startswith("u/"):
                path = path[2:]
        elif platform_id == "reddit":
            # https://reddit.com/user/username or /u/username
            if path.startswith("user/"):
                path = path[5:]
            elif path.startswith("u/"):
                path = path[2:]
        elif platform_id == "quora":
            # https://quora.com/profile/username
            if path.startswith("profile/"):
                path = path[8:]
        elif platform_id == "discord":
            # https://discord.gg/inviteCode or /invite/inviteCode
            if path.startswith("invite/"):
                path = path[7:]
        elif platform_id == "bluesky":
            # https://bsky.app/profile/username.bsky.social
            if path.startswith("profile/"):
                path = path[8:]

        # Take first path segment
        parts = [p for p in path.split("/") if p]
        if parts:
            raw = parts[0]
        else:
            raw = ""

    # Strip leading @ or trailing slash
    raw = raw.strip().rstrip("/")
    if platform_id not in ("youtube",):  # YouTube channels can start with @
        raw = raw.lstrip("@")

    return raw


def validate_value(platform_id: str, value: str) -> bool:
    """Validate normalized value against the platform's regex."""
    if not value:
        return False
    platform = get_platform(platform_id)
    validator_pattern = platform.get("validator")
    if not validator_pattern:
        return True
    return bool(re.match(validator_pattern, value))


def build_url(platform_id: str, value: str) -> str:
    """Build a complete, normalized public URL for a given platform and value."""
    extracted = extract_value(platform_id, value)
    if not extracted:
        return ""

    platform = get_platform(platform_id)
    template = platform["url_template"]

    if platform_id == "mastodon":
        # Format user@instance
        if "@" in extracted:
            user, instance = extracted.split("@", 1)
            return f"https://{instance}/@{user}"
        return f"https://mastodon.social/@{extracted}"

    if platform_id == "portfolio":
        if not re.match(r"^https?://", extracted, re.IGNORECASE):
            return f"https://{extracted}"
        return extracted

    return template.format(value=extracted)
