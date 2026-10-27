"""Step-1-only configuration for Osun State University.

This module is offline only. It does not contain a SheerID
programId, and it does not invent a SheerID organization id.
"""

SCHOOL_NAME = "Osun State University"
SCHOOL_CITY = "Osogbo"
SCHOOL_STATE = "Osun"
# SheerID organization id for this school: unknown.
# It is intentionally None and must not be guessed.
SCHOOL_ID = None
SCHOOL = {
    "id": None,
    "idExtended": None,
    "name": SCHOOL_NAME,
    "city": SCHOOL_CITY,
    "state": SCHOOL_STATE,
    "type": "UNIVERSITY",
}
