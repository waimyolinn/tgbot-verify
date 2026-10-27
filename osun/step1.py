"""Step-1-only offline info generation for /verify6.

No SheerID call, no captcha, no document upload, and no
schedule PNG or other document is generated here. The caller
supplies a Gmail address; no school email is generated.
"""
import re
from typing import Dict, Optional

from . import config
from .name_generator import NameGenerator, generate_birth_date


def parse_verification_id(url: str) -> Optional[str]:
    """Extract verificationId from a SheerID link, if present."""
    if not url:
        return None
    match = re.search(r"verificationId=([a-f0-9]+)", url, re.IGNORECASE)
    return match.group(1) if match else None


def prepare_package(gmail: str, sheerid_url: str) -> Dict:
    """
    Return step-1 info only.

    Args:
        gmail: user-supplied Gmail address, used as-is (lowercased).
        sheerid_url: SheerID link supplied by the user, returned
            for reference only; it is not submitted anywhere.

    Returns:
        dict with generated name, generated birth date, the fixed
        Osun State University school, the supplied Gmail address,
        and the SheerID link.
    """
    if not gmail or not isinstance(gmail, str):
        raise ValueError("A Gmail address is required.")
    gmail = gmail.strip().lower()
    if gmail.count("@") != 1 or not gmail.endswith("@gmail.com"):
        raise ValueError("A Gmail address ending in @gmail.com is required.")
    if not sheerid_url or not isinstance(sheerid_url, str):
        raise ValueError("A SheerID link is required.")
    name = NameGenerator.generate()
    return {
        "first_name": name["first_name"],
        "last_name": name["last_name"],
        "full_name": name["full_name"],
        "birth_date": generate_birth_date(),
        "school_name": config.SCHOOL_NAME,
        "school_city": config.SCHOOL_CITY,
        "school_state": config.SCHOOL_STATE,
        "school_id": config.SCHOOL_ID,
        "email": gmail,
        "sheerid_url": sheerid_url.strip(),
    }
