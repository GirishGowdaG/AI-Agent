"""Match result data model."""

from dataclasses import dataclass, field
from typing import List

from src.config import SCHEMA_VERSION
from src.models.resume import ResumeData


@dataclass
class MatchResult:
    """Result of matching a resume against job requirements."""
    resume: ResumeData
    overall_score: float  # 0-100
    skills_score: float   # 0-100, weight: 40%
    experience_score: float  # 0-100, weight: 40%
    education_score: float   # 0-100, weight: 20%
    matched_skills: List[str]
    skill_gaps: List[str]
    strengths: List[str]
    schema_version: str = field(default=SCHEMA_VERSION)
