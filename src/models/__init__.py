# Data models for resume screening
from .resume import ResumeData, ExperienceEntry, EducationEntry
from .job import JobRequirements
from .match import MatchResult
from .candidate import CandidateResult
from .status import ProcessingStatus

__all__ = [
    "ResumeData",
    "ExperienceEntry", 
    "EducationEntry",
    "JobRequirements",
    "MatchResult",
    "CandidateResult",
    "ProcessingStatus",
]
