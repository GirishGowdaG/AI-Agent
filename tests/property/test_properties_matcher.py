"""Property-based tests for Matcher Agent.

**Feature: resume-screening-agent, Property 6: Match Score Bounds**
**Feature: resume-screening-agent, Property 7: Weighted Score Calculation**
**Feature: resume-screening-agent, Property 8: Skill Gap Identification**
**Validates: Requirements 4.1, 4.2, 4.3**
"""

from hypothesis import given, settings, strategies as st, HealthCheck

from src.models.resume import ResumeData, ExperienceEntry, EducationEntry
from src.models.job import JobRequirements
from src.agents.matcher import MatcherAgent
from src.config import SKILLS_WEIGHT, EXPERIENCE_WEIGHT, EDUCATION_WEIGHT

# Simple alphabet for faster generation
SIMPLE_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789"


@st.composite
def experience_entry(draw):
    """Generate random ExperienceEntry."""
    return ExperienceEntry(
        title=draw(st.text(min_size=1, max_size=20, alphabet=SIMPLE_CHARS)),
        company=draw(st.text(min_size=1, max_size=20, alphabet=SIMPLE_CHARS)),
        duration_months=draw(st.integers(min_value=1, max_value=120)),
        description=draw(st.text(min_size=1, max_size=30, alphabet=SIMPLE_CHARS))
    )


@st.composite
def education_entry(draw):
    """Generate random EducationEntry."""
    return EducationEntry(
        degree=draw(st.text(min_size=1, max_size=20, alphabet=SIMPLE_CHARS)),
        institution=draw(st.text(min_size=1, max_size=20, alphabet=SIMPLE_CHARS)),
        year=draw(st.one_of(st.none(), st.integers(min_value=1990, max_value=2025))),
        field=draw(st.one_of(st.none(), st.text(min_size=1, max_size=20, alphabet=SIMPLE_CHARS)))
    )


@st.composite
def resume_data(draw):
    """Generate random ResumeData."""
    return ResumeData(
        name=draw(st.text(min_size=1, max_size=30, alphabet=SIMPLE_CHARS)),
        skills=draw(st.lists(st.text(min_size=1, max_size=15, alphabet=SIMPLE_CHARS), min_size=0, max_size=8)),
        experience=draw(st.lists(experience_entry(), min_size=0, max_size=3)),
        education=draw(st.lists(education_entry(), min_size=0, max_size=2)),
        raw_text=draw(st.text(min_size=1, max_size=50, alphabet=SIMPLE_CHARS)),
        email=None,
        phone=None
    )


@st.composite
def job_requirements(draw):
    """Generate random JobRequirements."""
    return JobRequirements(
        title=draw(st.text(min_size=1, max_size=30, alphabet=SIMPLE_CHARS)),
        required_skills=draw(st.lists(st.text(min_size=1, max_size=15, alphabet=SIMPLE_CHARS), min_size=1, max_size=5)),
        preferred_skills=draw(st.lists(st.text(min_size=1, max_size=15, alphabet=SIMPLE_CHARS), min_size=0, max_size=3)),
        min_experience_years=draw(st.integers(min_value=0, max_value=10)),
        education_requirements=draw(st.lists(st.text(min_size=1, max_size=20, alphabet=SIMPLE_CHARS), min_size=0, max_size=2)),
        responsibilities=[]
    )


class TestMatchScoreBounds:
    """
    **Feature: resume-screening-agent, Property 6: Match Score Bounds**
    **Validates: Requirements 4.1**
    
    For any resume and job requirements pair processed by the Matcher_Agent, 
    the overall_score, skills_score, experience_score, and education_score 
    should all be in the range [0, 100].
    """

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(resume_data(), job_requirements())
    def test_overall_score_in_bounds(self, resume: ResumeData, job: JobRequirements):
        """Overall score is always between 0 and 100."""
        matcher = MatcherAgent()
        result = matcher.match_candidate(resume, job)
        
        assert 0 <= result.overall_score <= 100

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(resume_data(), job_requirements())
    def test_skills_score_in_bounds(self, resume: ResumeData, job: JobRequirements):
        """Skills score is always between 0 and 100."""
        matcher = MatcherAgent()
        result = matcher.match_candidate(resume, job)
        
        assert 0 <= result.skills_score <= 100

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(resume_data(), job_requirements())
    def test_experience_score_in_bounds(self, resume: ResumeData, job: JobRequirements):
        """Experience score is always between 0 and 100."""
        matcher = MatcherAgent()
        result = matcher.match_candidate(resume, job)
        
        assert 0 <= result.experience_score <= 100

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(resume_data(), job_requirements())
    def test_education_score_in_bounds(self, resume: ResumeData, job: JobRequirements):
        """Education score is always between 0 and 100."""
        matcher = MatcherAgent()
        result = matcher.match_candidate(resume, job)
        
        assert 0 <= result.education_score <= 100


class TestWeightedScoreCalculation:
    """
    **Feature: resume-screening-agent, Property 7: Weighted Score Calculation**
    **Validates: Requirements 4.2**
    
    For any MatchResult, the overall_score should equal 
    (skills_score * 0.4) + (experience_score * 0.4) + (education_score * 0.2),
    within a tolerance of 0.01.
    """

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(resume_data(), job_requirements())
    def test_weighted_score_formula(self, resume: ResumeData, job: JobRequirements):
        """Overall score equals weighted sum of component scores."""
        matcher = MatcherAgent()
        result = matcher.match_candidate(resume, job)
        
        expected = (
            result.skills_score * SKILLS_WEIGHT +
            result.experience_score * EXPERIENCE_WEIGHT +
            result.education_score * EDUCATION_WEIGHT
        )
        
        assert abs(result.overall_score - expected) < 0.01

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(
        st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False),
        st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False),
        st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False)
    )
    def test_compute_score_formula(self, skills: float, experience: float, education: float):
        """compute_score method correctly applies weights."""
        matcher = MatcherAgent()
        result = matcher.compute_score(skills, experience, education)
        
        expected = skills * 0.4 + experience * 0.4 + education * 0.2
        
        assert abs(result - expected) < 0.01


class TestSkillGapIdentification:
    """
    **Feature: resume-screening-agent, Property 8: Skill Gap Identification**
    **Validates: Requirements 4.3**
    
    For any resume skills list and required skills list, the skill_gaps 
    should equal the set difference of required_skills minus matched_skills.
    """

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(
        st.lists(st.text(min_size=1, max_size=15, alphabet=SIMPLE_CHARS), min_size=0, max_size=8),
        st.lists(st.text(min_size=1, max_size=15, alphabet=SIMPLE_CHARS), min_size=1, max_size=5)
    )
    def test_skill_gaps_are_missing_required_skills(self, resume_skills: list, required_skills: list):
        """Skill gaps contain only required skills not in resume."""
        matcher = MatcherAgent()
        gaps = matcher.identify_gaps(resume_skills, required_skills)
        
        resume_skills_lower = {s.lower().strip() for s in resume_skills}
        
        # Every gap should be a required skill not in resume
        for gap in gaps:
            assert gap.lower().strip() not in resume_skills_lower

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(
        st.lists(st.text(min_size=1, max_size=15, alphabet=SIMPLE_CHARS), min_size=0, max_size=8),
        st.lists(st.text(min_size=1, max_size=15, alphabet=SIMPLE_CHARS), min_size=1, max_size=5)
    )
    def test_skill_gaps_plus_matched_equals_required(self, resume_skills: list, required_skills: list):
        """Gaps plus matched skills should cover all required skills."""
        matcher = MatcherAgent()
        gaps = matcher.identify_gaps(resume_skills, required_skills)
        matched = matcher._find_matched_skills(resume_skills, required_skills)
        
        # Gaps + matched should equal required (by count, accounting for case)
        gaps_lower = {g.lower().strip() for g in gaps}
        matched_lower = {m.lower().strip() for m in matched}
        required_lower = {r.lower().strip() for r in required_skills}
        
        assert gaps_lower | matched_lower == required_lower

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(resume_data(), job_requirements())
    def test_match_result_gaps_are_correct(self, resume: ResumeData, job: JobRequirements):
        """MatchResult skill_gaps are correctly identified."""
        matcher = MatcherAgent()
        result = matcher.match_candidate(resume, job)
        
        resume_skills_lower = {s.lower().strip() for s in resume.skills}
        
        # Every gap should be a required skill not in resume
        for gap in result.skill_gaps:
            assert gap.lower().strip() not in resume_skills_lower
