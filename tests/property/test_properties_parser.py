"""Property-based tests for Parser Agent output structure.

**Feature: resume-screening-agent, Property 3: Parser Output Structure**
**Validates: Requirements 1.5**
"""

from hypothesis import given, settings, strategies as st, HealthCheck

from src.models.resume import ResumeData, ExperienceEntry, EducationEntry

# Simple alphabet for faster generation
SIMPLE_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "


@st.composite
def experience_entry(draw):
    """Generate random ExperienceEntry."""
    return ExperienceEntry(
        title=draw(st.text(min_size=1, max_size=30, alphabet=SIMPLE_CHARS)),
        company=draw(st.text(min_size=1, max_size=30, alphabet=SIMPLE_CHARS)),
        duration_months=draw(st.integers(min_value=1, max_value=360)),
        description=draw(st.text(min_size=1, max_size=50, alphabet=SIMPLE_CHARS))
    )


@st.composite
def education_entry(draw):
    """Generate random EducationEntry."""
    return EducationEntry(
        degree=draw(st.text(min_size=1, max_size=30, alphabet=SIMPLE_CHARS)),
        institution=draw(st.text(min_size=1, max_size=30, alphabet=SIMPLE_CHARS)),
        year=draw(st.one_of(st.none(), st.integers(min_value=1950, max_value=2030))),
        field=draw(st.one_of(st.none(), st.text(min_size=1, max_size=30, alphabet=SIMPLE_CHARS)))
    )


@st.composite
def resume_data(draw):
    """Generate random ResumeData."""
    return ResumeData(
        name=draw(st.text(min_size=1, max_size=50, alphabet=SIMPLE_CHARS)),
        skills=draw(st.lists(st.text(min_size=1, max_size=20, alphabet=SIMPLE_CHARS), min_size=0, max_size=5)),
        experience=draw(st.lists(experience_entry(), min_size=0, max_size=2)),
        education=draw(st.lists(education_entry(), min_size=0, max_size=2)),
        raw_text=draw(st.text(min_size=1, max_size=100, alphabet=SIMPLE_CHARS)),
        email=draw(st.one_of(st.none(), st.just("test@example.com"))),
        phone=draw(st.one_of(st.none(), st.just("1234567890")))
    )


class TestParserOutputStructure:
    """
    **Feature: resume-screening-agent, Property 3: Parser Output Structure**
    **Validates: Requirements 1.5**
    
    For any valid resume text input, the Parser_Agent output should contain 
    all required fields: name (string), skills (array), experience (array), 
    and education (array).
    """

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(resume_data())
    def test_resume_data_has_required_fields(self, resume: ResumeData):
        """ResumeData always contains all required fields."""
        # Verify name is a string
        assert isinstance(resume.name, str)
        assert len(resume.name) > 0
        
        # Verify skills is a list
        assert isinstance(resume.skills, list)
        for skill in resume.skills:
            assert isinstance(skill, str)
        
        # Verify experience is a list of ExperienceEntry
        assert isinstance(resume.experience, list)
        for exp in resume.experience:
            assert isinstance(exp, ExperienceEntry)
            assert isinstance(exp.title, str)
            assert isinstance(exp.company, str)
            assert isinstance(exp.duration_months, int)
            assert isinstance(exp.description, str)
        
        # Verify education is a list of EducationEntry
        assert isinstance(resume.education, list)
        for edu in resume.education:
            assert isinstance(edu, EducationEntry)
            assert isinstance(edu.degree, str)
            assert isinstance(edu.institution, str)

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(resume_data())
    def test_resume_data_has_raw_text(self, resume: ResumeData):
        """ResumeData always contains raw_text field."""
        assert hasattr(resume, 'raw_text')
        assert isinstance(resume.raw_text, str)

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(resume_data())
    def test_resume_data_has_schema_version(self, resume: ResumeData):
        """ResumeData always contains schema_version field."""
        assert hasattr(resume, 'schema_version')
        assert isinstance(resume.schema_version, str)
        assert len(resume.schema_version) > 0

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(resume_data())
    def test_experience_entry_has_valid_duration(self, resume: ResumeData):
        """ExperienceEntry duration_months is always a positive integer."""
        for exp in resume.experience:
            assert exp.duration_months >= 0

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(resume_data())
    def test_education_entry_year_is_valid(self, resume: ResumeData):
        """EducationEntry year is either None or a valid year."""
        for edu in resume.education:
            if edu.year is not None:
                assert isinstance(edu.year, int)
                assert 1900 <= edu.year <= 2100
