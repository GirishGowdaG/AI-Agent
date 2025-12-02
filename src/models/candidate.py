"""Candidate result data model."""

from dataclasses import dataclass, field
from typing import List

from src.config import SCHEMA_VERSION


@dataclass
class CandidateResult:
    """Final ranked candidate result with explanation."""
    rank: int
    name: str
    overall_score: float
    skills_score: float
    experience_score: float
    education_score: float
    matched_skills: List[str]
    skill_gaps: List[str]
    strengths: List[str]
    explanation: str
    schema_version: str = field(default=SCHEMA_VERSION)
