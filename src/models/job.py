"""Job requirements data model."""

from dataclasses import dataclass, field
from typing import List

from src.config import SCHEMA_VERSION


@dataclass
class JobRequirements:
    """Structured job requirements extracted from description."""
    title: str
    required_skills: List[str]
    preferred_skills: List[str]
    min_experience_years: int
    education_requirements: List[str]
    responsibilities: List[str] = field(default_factory=list)
    schema_version: str = field(default=SCHEMA_VERSION)
