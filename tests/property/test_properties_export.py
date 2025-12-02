"""Property-based tests for export functionality.

**Feature: resume-screening-agent, Property 13: CSV Export Completeness**
**Feature: resume-screening-agent, Property 14: Export Metadata Presence**
**Validates: Requirements 7.1, 7.3**
"""

from hypothesis import given, settings, strategies as st, HealthCheck

from src.models.candidate import CandidateResult
from src.utils.export import ExportService

# Simple alphabet for faster generation
SIMPLE_CHARS = "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 "


@st.composite
def candidate_result(draw):
    """Generate random CandidateResult."""
    skills_score = draw(st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False))
    experience_score = draw(st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False))
    education_score = draw(st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False))
    overall_score = skills_score * 0.4 + experience_score * 0.4 + education_score * 0.2
    
    return CandidateResult(
        rank=draw(st.integers(min_value=1, max_value=100)),
        name=draw(st.text(min_size=1, max_size=30, alphabet=SIMPLE_CHARS)),
        overall_score=overall_score,
        skills_score=skills_score,
        experience_score=experience_score,
        education_score=education_score,
        matched_skills=draw(st.lists(st.text(min_size=1, max_size=15, alphabet=SIMPLE_CHARS), min_size=0, max_size=5)),
        skill_gaps=draw(st.lists(st.text(min_size=1, max_size=15, alphabet=SIMPLE_CHARS), min_size=0, max_size=5)),
        strengths=draw(st.lists(st.text(min_size=1, max_size=20, alphabet=SIMPLE_CHARS), min_size=0, max_size=3)),
        explanation=draw(st.text(min_size=1, max_size=50, alphabet=SIMPLE_CHARS))
    )


class TestCSVExportCompleteness:
    """
    **Feature: resume-screening-agent, Property 13: CSV Export Completeness**
    **Validates: Requirements 7.1**
    
    For any list of CandidateResults exported to CSV, the CSV should contain 
    one row per candidate with columns for all score fields and analysis data.
    """

    def test_csv_contains_all_candidates_simple(self):
        """CSV contains data for all candidates."""
        results = [
            CandidateResult(
                rank=1, name="Alice", overall_score=80.0, skills_score=90.0,
                experience_score=70.0, education_score=80.0,
                matched_skills=["Python"], skill_gaps=["Java"],
                strengths=["Strong coder"], explanation="Good candidate"
            ),
            CandidateResult(
                rank=2, name="Bob", overall_score=70.0, skills_score=80.0,
                experience_score=60.0, education_score=70.0,
                matched_skills=["SQL"], skill_gaps=["Python"],
                strengths=["Database expert"], explanation="Decent candidate"
            )
        ]
        export_service = ExportService()
        csv_bytes = export_service.to_csv(results, "Test job description")
        csv_text = csv_bytes.decode('utf-8')
        
        # CSV should contain both candidate names
        assert "Alice" in csv_text
        assert "Bob" in csv_text
        assert "Total Candidates: 2" in csv_text

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(st.lists(candidate_result(), min_size=1, max_size=5))
    def test_csv_contains_required_columns(self, results: list):
        """CSV contains all required columns."""
        export_service = ExportService()
        csv_bytes = export_service.to_csv(results, "Test job description")
        csv_text = csv_bytes.decode('utf-8')
        
        # Check for required column headers
        assert 'Rank' in csv_text
        assert 'Name' in csv_text
        assert 'Overall Score' in csv_text
        assert 'Skills Score' in csv_text
        assert 'Experience Score' in csv_text
        assert 'Education Score' in csv_text
        assert 'Matched Skills' in csv_text
        assert 'Skill Gaps' in csv_text

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(candidate_result())
    def test_csv_contains_candidate_name(self, result: CandidateResult):
        """CSV contains each candidate's name."""
        export_service = ExportService()
        csv_bytes = export_service.to_csv([result], "Test job description")
        csv_text = csv_bytes.decode('utf-8')
        
        assert result.name in csv_text

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(st.lists(candidate_result(), min_size=1, max_size=5))
    def test_csv_is_valid_utf8(self, results: list):
        """CSV output is valid UTF-8."""
        export_service = ExportService()
        csv_bytes = export_service.to_csv(results, "Test job description")
        
        # Should not raise an exception
        csv_text = csv_bytes.decode('utf-8')
        assert len(csv_text) > 0


class TestExportMetadataPresence:
    """
    **Feature: resume-screening-agent, Property 14: Export Metadata Presence**
    **Validates: Requirements 7.3**
    
    For any export (CSV or PDF), the output should contain a timestamp 
    and job description summary.
    """

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(
        st.lists(candidate_result(), min_size=1, max_size=3),
        st.text(min_size=10, max_size=100, alphabet=SIMPLE_CHARS)
    )
    def test_csv_contains_timestamp(self, results: list, job_summary: str):
        """CSV export contains timestamp."""
        export_service = ExportService()
        csv_bytes = export_service.to_csv(results, job_summary)
        csv_text = csv_bytes.decode('utf-8')
        
        # Check for timestamp marker
        assert 'Generated:' in csv_text

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(
        st.lists(candidate_result(), min_size=1, max_size=3),
        st.text(min_size=10, max_size=100, alphabet=SIMPLE_CHARS)
    )
    def test_csv_contains_job_summary(self, results: list, job_summary: str):
        """CSV export contains job summary."""
        export_service = ExportService()
        csv_bytes = export_service.to_csv(results, job_summary)
        csv_text = csv_bytes.decode('utf-8')
        
        # Check for job summary marker
        assert 'Job Summary:' in csv_text

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(
        st.lists(candidate_result(), min_size=1, max_size=3),
        st.text(min_size=10, max_size=100, alphabet=SIMPLE_CHARS)
    )
    def test_metadata_contains_timestamp(self, results: list, job_summary: str):
        """Export metadata contains timestamp."""
        export_service = ExportService()
        metadata = export_service.get_export_metadata(results, job_summary)
        
        assert 'timestamp' in metadata
        assert metadata['timestamp'] is not None

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(
        st.lists(candidate_result(), min_size=1, max_size=3),
        st.text(min_size=10, max_size=100, alphabet=SIMPLE_CHARS)
    )
    def test_metadata_contains_job_summary(self, results: list, job_summary: str):
        """Export metadata contains job summary."""
        export_service = ExportService()
        metadata = export_service.get_export_metadata(results, job_summary)
        
        assert 'job_summary' in metadata
        assert metadata['job_summary'] == job_summary

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(
        st.lists(candidate_result(), min_size=1, max_size=3),
        st.text(min_size=10, max_size=100, alphabet=SIMPLE_CHARS)
    )
    def test_metadata_contains_candidate_count(self, results: list, job_summary: str):
        """Export metadata contains total candidate count."""
        export_service = ExportService()
        metadata = export_service.get_export_metadata(results, job_summary)
        
        assert 'total_candidates' in metadata
        assert metadata['total_candidates'] == len(results)
