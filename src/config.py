"""Configuration for Resume Screening Agent."""

import os
from typing import Optional

# API Configuration
GEMINI_MODEL = "gemini-2.0-flash"

# Processing Limits
MAX_PDF_FILES = 50
MAX_JOB_DESCRIPTION_LENGTH = 10000
MIN_JOB_DESCRIPTION_LENGTH = 1

# Scoring Weights
SKILLS_WEIGHT = 0.4
EXPERIENCE_WEIGHT = 0.4
EDUCATION_WEIGHT = 0.2

# Schema Version
SCHEMA_VERSION = "1.0"

# Timeouts (seconds)
PDF_EXTRACTION_TIMEOUT = 2
AGENT_PROCESSING_TIMEOUT = 30


# Hardcoded API key (for development)
_HARDCODED_API_KEY = "AIzaSyBWl-Fw5jtuugEuddK0xkE6WWQ30P8fDYM"


def get_gemini_api_key() -> Optional[str]:
    """Get Gemini API key."""
    return _HARDCODED_API_KEY
