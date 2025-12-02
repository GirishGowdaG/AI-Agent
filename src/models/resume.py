"""Resume data models."""

from dataclasses import dataclass, field
from typing import List, Optional

from src.config import SCHEMA_VERSION


@dataclass
class ExperienceEntry:
    """Represents a single work experience entry."""
    title: str
    company: str
    duration_months: int
    description: str


@dataclass
class EducationEntry:
    """Represents a single education entry."""
    degree: str
    institution: str
    year: Optional[int] = None
    field: Optional[str] = None


@dataclass
class ResumeData:
    """Structured resume data extracted from PDF."""
    name: str
    skills: List[str]
    experience: List[ExperienceEntry]
    education: List[EducationEntry]
    raw_text: str
    email: Optional[str] = None
    phone: Optional[str] = None
    schema_version: str = field(default=SCHEMA_VERSION)
