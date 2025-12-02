"""Matcher Agent for computing match scores between resumes and job requirements."""

import logging
from typing import List

from src.config import SKILLS_WEIGHT, EXPERIENCE_WEIGHT, EDUCATION_WEIGHT
from src.models.resume import ResumeData
from src.models.job import JobRequirements
from src.models.match import MatchResult

logger = logging.getLogger(__name__)


class MatcherAgent:
    """Computes semantic similarity scores between resumes and job requirements."""

    def __init__(self):
        self.skills_weight = SKILLS_WEIGHT
        self.experience_weight = EXPERIENCE_WEIGHT
        self.education_weight = EDUCATION_WEIGHT

    def match_candidate(
        self, 
        resume: ResumeData, 
        requirements: JobRequirements
    ) -> MatchResult:
        """Match a resume against job requirements.
        
        Args:
            resume: Parsed resume data
            requirements: Job requirements
            
        Returns:
            MatchResult with scores and analysis
        """
        # Compute individual scores
        skills_score = self._compute_skills_score(resume.skills, requirements.required_skills)
        experience_score = self._compute_experience_score(resume.experience, requirements.min_experience_years)
        education_score = self._compute_education_score(resume.education, requirements.education_requirements)
        
        # Compute weighted overall score
        overall_score = self.compute_score(skills_score, experience_score, education_score)
        
        # Identify matched skills and gaps
        matched_skills = self._find_matched_skills(resume.skills, requirements.required_skills)
        skill_gaps = self.identify_gaps(resume.skills, requirements.required_skills)
        
        # Identify strengths
        strengths = self.identify_strengths(resume, requirements)
        
        return MatchResult(
            resume=resume,
            overall_score=overall_score,
            skills_score=skills_score,
            experience_score=experience_score,
            education_score=education_score,
            matched_skills=matched_skills,
            skill_gaps=skill_gaps,
            strengths=strengths
        )

    def compute_score(
        self,
        skills_score: float,
        experience_score: float,
        education_score: float
    ) -> float:
        """Compute weighted overall score.
        
        Args:
            skills_score: Skills match score (0-100)
            experience_score: Experience match score (0-100)
            education_score: Education match score (0-100)
            
        Returns:
            Weighted overall score (0-100)
        """
        return (
            skills_score * self.skills_weight +
            experience_score * self.experience_weight +
            education_score * self.education_weight
        )

    def _compute_skills_score(
        self, 
        resume_skills: List[str], 
        required_skills: List[str]
    ) -> float:
        """Compute skills match score.
        
        Args:
            resume_skills: Skills from resume
            required_skills: Required skills from job
            
        Returns:
            Score from 0-100
        """
        if not required_skills:
            return 100.0
        
        # Normalize skills for comparison (lowercase)
        resume_skills_lower = {s.lower().strip() for s in resume_skills}
        required_skills_lower = {s.lower().strip() for s in required_skills}
        
        # Count matches
        matches = len(resume_skills_lower & required_skills_lower)
        
        # Calculate percentage
        return min(100.0, (matches / len(required_skills_lower)) * 100)

    def _compute_experience_score(
        self, 
        experience: List, 
        min_years: int
    ) -> float:
        """Compute experience match score.
        
        Args:
            experience: Experience entries from resume
            min_years: Minimum years required
            
        Returns:
            Score from 0-100
        """
        min_years = min_years or 0
        if min_years <= 0:
            return 100.0
        
        # Calculate total months of experience (handle None values)
        total_months = sum((exp.duration_months or 0) for exp in experience)
        total_years = total_months / 12
        
        # Score based on how well experience meets requirement
        if total_years >= min_years:
            return 100.0
        else:
            return min(100.0, (total_years / min_years) * 100)

    def _compute_education_score(
        self, 
        education: List, 
        requirements: List[str]
    ) -> float:
        """Compute education match score.
        
        Args:
            education: Education entries from resume
            requirements: Education requirements from job
            
        Returns:
            Score from 0-100
        """
        if not requirements:
            return 100.0
        
        if not education:
            return 0.0
        
        # Simple matching based on degree keywords
        education_text = " ".join(
            f"{edu.degree} {edu.field or ''} {edu.institution}".lower()
            for edu in education
        )
        
        matches = 0
        for req in requirements:
            req_lower = req.lower()
            if any(word in education_text for word in req_lower.split()):
                matches += 1
        
        return min(100.0, (matches / len(requirements)) * 100)

    def _find_matched_skills(
        self, 
        resume_skills: List[str], 
        required_skills: List[str]
    ) -> List[str]:
        """Find skills that match between resume and requirements.
        
        Args:
            resume_skills: Skills from resume
            required_skills: Required skills from job
            
        Returns:
            List of matched skills
        """
        resume_skills_lower = {s.lower().strip(): s for s in resume_skills}
        matched = []
        
        for req_skill in required_skills:
            req_lower = req_skill.lower().strip()
            if req_lower in resume_skills_lower:
                matched.append(resume_skills_lower[req_lower])
        
        return matched

    def identify_gaps(
        self,
        resume_skills: List[str],
        required_skills: List[str]
    ) -> List[str]:
        """Identify skill gaps between resume and requirements.
        
        Args:
            resume_skills: Skills from resume
            required_skills: Required skills from job
            
        Returns:
            List of missing skills (required but not in resume)
        """
        resume_skills_lower = {s.lower().strip() for s in resume_skills}
        gaps = []
        
        for req_skill in required_skills:
            if req_skill.lower().strip() not in resume_skills_lower:
                gaps.append(req_skill)
        
        return gaps

    def identify_strengths(
        self,
        resume: ResumeData,
        requirements: JobRequirements
    ) -> List[str]:
        """Identify candidate strengths that align with job requirements.
        
        Args:
            resume: Parsed resume data
            requirements: Job requirements
            
        Returns:
            List of strength descriptions
        """
        strengths = []
        
        # Check for skill matches
        matched_skills = self._find_matched_skills(resume.skills, requirements.required_skills)
        if matched_skills:
            strengths.append(f"Has {len(matched_skills)} of {len(requirements.required_skills)} required skills")
        
        # Check for experience (handle None values)
        total_months = sum((exp.duration_months or 0) for exp in resume.experience)
        total_years = total_months / 12
        min_exp_years = requirements.min_experience_years or 0
        if min_exp_years > 0 and total_years >= min_exp_years:
            strengths.append(f"Exceeds experience requirement ({total_years:.1f} years)")
        
        # Check for preferred skills
        preferred_matches = self._find_matched_skills(resume.skills, requirements.preferred_skills)
        if preferred_matches:
            strengths.append(f"Has {len(preferred_matches)} preferred skills")
        
        return strengths
