"""Property-based tests for serialization.

**Feature: resume-screening-agent, Property 9: Serialization Round-Trip**
**Feature: resume-screening-agent, Property 15: Agent Output Schema Conformance**
"""

from hypothesis import given, settings, strategies as st, HealthCheck

from src.models.resume import ResumeData, ExperienceEntry, EducationEntry
from src.models.job import JobRequirements
from src.models.match import MatchResult
from src.models.candidate import CandidateResult
from src.utils.serialization import Serializer

# Simple alphabet for faster generation
SIMPLE_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "


# Custom strategies for generating test data
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


@st.composite  
def match_result(draw):
    """Generate random MatchResult with valid weighted score."""
    skills_score = draw(st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False))
    experience_score = draw(st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False))
    education_score = draw(st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False))
    overall_score = skills_score * 0.4 + experience_score * 0.4 + education_score * 0.2
    
    return MatchResult(
        resume=draw(resume_data()),
        overall_score=overall_score,
        skills_score=skills_score,
        experience_score=experience_score,
        education_score=education_score,
        matched_skills=draw(st.lists(st.text(min_size=1, max_size=20, alphabet=SIMPLE_CHARS), min_size=0, max_size=5)),
        skill_gaps=draw(st.lists(st.text(min_size=1, max_size=20, alphabet=SIMPLE_CHARS), min_size=0, max_size=5)),
        strengths=draw(st.lists(st.text(min_size=1, max_size=30, alphabet=SIMPLE_CHARS), min_size=0, max_size=3))
    )


@st.composite
def candidate_result(draw):
    """Generate random CandidateResult."""
    skills_score = draw(st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False))
    experience_score = draw(st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False))
    education_score = draw(st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False))
    overall_score = skills_score * 0.4 + experience_score * 0.4 + education_score * 0.2
    
    return CandidateResult(
        rank=draw(st.integers(min_value=1, max_value=100)),
        name=draw(st.text(min_size=1, max_size=50, alphabet=SIMPLE_CHARS)),
        overall_score=overall_score,
        skills_score=skills_score,
        experience_score=experience_score,
        education_score=education_score,
        matched_skills=draw(st.lists(st.text(min_size=1, max_size=20, alphabet=SIMPLE_CHARS), min_size=0, max_size=5)),
        skill_gaps=draw(st.lists(st.text(min_size=1, max_size=20, alphabet=SIMPLE_CHARS), min_size=0, max_size=5)),
        strengths=draw(st.lists(st.text(min_size=1, max_size=30, alphabet=SIMPLE_CHARS), min_size=0, max_size=3)),
        explanation=draw(st.text(min_size=1, max_size=100, alphabet=SIMPLE_CHARS))
    )


class TestSerializationRoundTrip:
    """
    **Feature: resume-screening-agent, Property 9: Serialization Round-Trip**
    **Validates: Requirements 4.5, 4.6, 9.3, 9.4**
    
    For any valid data model object, serializing to JSON and then 
    deserializing should produce an equivalent object.
    """
    
    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(resume_data())
    def test_resume_data_round_trip(self, resume: ResumeData):
        """ResumeData serialization round-trip preserves all data."""
        serializer = Serializer()
        json_str = serializer.serialize(resume)
        restored = serializer.deserialize(json_str, ResumeData)
        
        assert restored.name == resume.name
        assert restored.skills == resume.skills
        assert restored.email == resume.email
        assert restored.phone == resume.phone
        assert restored.raw_text == resume.raw_text
        assert restored.schema_version == resume.schema_version
        assert len(restored.experience) == len(resume.experience)
        assert len(restored.education) == len(resume.education)

    @settings(max_examples=100)
    @given(job_requirements())
    def test_job_requirements_round_trip(self, job: JobRequirements):
        """JobRequirements serialization round-trip preserves all data."""
        serializer = Serializer()
        json_str = serializer.serialize(job)
        restored = serializer.deserialize(json_str, JobRequirements)
        
        assert restored.title == job.title
        assert restored.required_skills == job.required_skills
        assert restored.preferred_skills == job.preferred_skills
        assert restored.min_experience_years == job.min_experience_years
        assert restored.education_requirements == job.education_requirements
        assert restored.responsibilities == job.responsibilities
        assert restored.schema_version == job.schema_version

    @settings(max_examples=100)
    @given(candidate_result())
    def test_candidate_result_round_trip(self, candidate: CandidateResult):
        """CandidateResult serialization round-trip preserves all data."""
        serializer = Serializer()
        json_str = serializer.serialize(candidate)
        restored = serializer.deserialize(json_str, CandidateResult)
        
        assert restored.rank == candidate.rank
        assert restored.name == candidate.name
        assert abs(restored.overall_score - candidate.overall_score) < 0.01
        assert abs(restored.skills_score - candidate.skills_score) < 0.01
        assert abs(restored.experience_score - candidate.experience_score) < 0.01
        assert abs(restored.education_score - candidate.education_score) < 0.01
        assert restored.matched_skills == candidate.matched_skills
        assert restored.skill_gaps == candidate.skill_gaps
        assert restored.strengths == candidate.strengths
        assert restored.explanation == candidate.explanation
        assert restored.schema_version == candidate.schema_version


class TestSchemaConformance:
    """
    **Feature: resume-screening-agent, Property 15: Agent Output Schema Conformance**
    **Validates: Requirements 9.1, 9.2, 9.5**
    
    For any output from Parser_Agent or Analyzer_Agent, the JSON output 
    should validate against the corresponding schema and include schema_version.
    """
    
    @settings(max_examples=100)
    @given(resume_data())
    def test_resume_data_has_schema_version(self, resume: ResumeData):
        """ResumeData serialization includes schema_version field."""
        serializer = Serializer()
        json_str = serializer.serialize(resume)
        
        assert serializer.validate_schema(json_str, ResumeData)
        assert '"schema_version"' in json_str

    @settings(max_examples=100)
    @given(job_requirements())
    def test_job_requirements_has_schema_version(self, job: JobRequirements):
        """JobRequirements serialization includes schema_version field."""
        serializer = Serializer()
        json_str = serializer.serialize(job)
        
        assert serializer.validate_schema(json_str, JobRequirements)
        assert '"schema_version"' in json_str

    @settings(max_examples=100)
    @given(match_result())
    def test_match_result_has_schema_version(self, match: MatchResult):
        """MatchResult serialization includes schema_version field."""
        serializer = Serializer()
        json_str = serializer.serialize(match)
        
        assert serializer.validate_schema(json_str, MatchResult)
        assert '"schema_version"' in json_str

    @settings(max_examples=100)
    @given(candidate_result())
    def test_candidate_result_has_schema_version(self, candidate: CandidateResult):
        """CandidateResult serialization includes schema_version field."""
        serializer = Serializer()
        json_str = serializer.serialize(candidate)
        
        assert serializer.validate_schema(json_str, CandidateResult)
        assert '"schema_version"' in json_str
