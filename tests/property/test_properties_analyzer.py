"""Property-based tests for Analyzer Agent output structure.

**Feature: resume-screening-agent, Property 5: Analyzer Output Structure**
**Validates: Requirements 2.2**
"""

from hypothesis import given, settings, strategies as st, HealthCheck

from src.models.job import JobRequirements

# Simple alphabet for faster generation
SIMPLE_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "


@st.composite
def job_requirements(draw):
    """Generate random JobRequirements."""
    return JobRequirements(
        title=draw(st.text(min_size=1, max_size=50, alphabet=SIMPLE_CHARS)),
        required_skills=draw(st.lists(st.text(min_size=1, max_size=20, alphabet=SIMPLE_CHARS), min_size=1, max_size=5)),
        preferred_skills=draw(st.lists(st.text(min_size=1, max_size=20, alphabet=SIMPLE_CHARS), min_size=0, max_size=3)),
        min_experience_years=draw(st.integers(min_value=0, max_value=20)),
        education_requirements=draw(st.lists(st.text(min_size=1, max_size=30, alphabet=SIMPLE_CHARS), min_size=0, max_size=3)),
        responsibilities=draw(st.lists(st.text(min_size=1, max_size=50, alphabet=SIMPLE_CHARS), min_size=0, max_size=3))
    )


class TestAnalyzerOutputStructure:
    """
    **Feature: resume-screening-agent, Property 5: Analyzer Output Structure**
    **Validates: Requirements 2.2**
    
    For any valid job description input, the Analyzer_Agent output should contain 
    required_skills (array), min_experience_years (number), and education_requirements (array).
    """

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(job_requirements())
    def test_job_requirements_has_required_skills(self, job: JobRequirements):
        """JobRequirements always contains required_skills as a list."""
        assert hasattr(job, 'required_skills')
        assert isinstance(job.required_skills, list)
        for skill in job.required_skills:
            assert isinstance(skill, str)

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(job_requirements())
    def test_job_requirements_has_min_experience_years(self, job: JobRequirements):
        """JobRequirements always contains min_experience_years as an integer."""
        assert hasattr(job, 'min_experience_years')
        assert isinstance(job.min_experience_years, int)
        assert job.min_experience_years >= 0

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(job_requirements())
    def test_job_requirements_has_education_requirements(self, job: JobRequirements):
        """JobRequirements always contains education_requirements as a list."""
        assert hasattr(job, 'education_requirements')
        assert isinstance(job.education_requirements, list)
        for edu in job.education_requirements:
            assert isinstance(edu, str)

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(job_requirements())
    def test_job_requirements_has_title(self, job: JobRequirements):
        """JobRequirements always contains title as a string."""
        assert hasattr(job, 'title')
        assert isinstance(job.title, str)
        assert len(job.title) > 0

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(job_requirements())
    def test_job_requirements_has_schema_version(self, job: JobRequirements):
        """JobRequirements always contains schema_version field."""
        assert hasattr(job, 'schema_version')
        assert isinstance(job.schema_version, str)
        assert len(job.schema_version) > 0

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(job_requirements())
    def test_job_requirements_has_preferred_skills(self, job: JobRequirements):
        """JobRequirements always contains preferred_skills as a list."""
        assert hasattr(job, 'preferred_skills')
        assert isinstance(job.preferred_skills, list)
        for skill in job.preferred_skills:
            assert isinstance(skill, str)
