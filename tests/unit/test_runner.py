"""Unit tests for Runner orchestration.

Tests agent execution sequence, error handling, and status updates.
**Validates: Requirements 3.1, 3.2, 3.3**
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from src.runner import ResumeScreeningRunner
from src.models.resume import ResumeData, ExperienceEntry, EducationEntry
from src.models.job import JobRequirements
from src.models.match import MatchResult
from src.models.candidate import CandidateResult
from src.models.status import ProcessingStatus


class TestRunnerOrchestration:
    """Test agent execution sequence."""

    def test_runner_initializes_all_agents(self):
        """Runner initializes all four agents."""
        runner = ResumeScreeningRunner()
        
        assert runner.parser is not None
        assert runner.analyzer is not None
        assert runner.matcher is not None
        assert runner.ranker is not None

    def test_get_status_returns_none_initially(self):
        """get_status returns None before processing starts."""
        runner = ResumeScreeningRunner()
        
        assert runner.get_status() is None

    @patch.object(ResumeScreeningRunner, '_update_status')
    def test_status_updates_called_in_sequence(self, mock_update):
        """Status updates are called for each agent in sequence."""
        runner = ResumeScreeningRunner()
        
        # Mock the agents to avoid actual API calls
        mock_job_req = JobRequirements(
            title="Test",
            required_skills=["Python"],
            preferred_skills=[],
            min_experience_years=2,
            education_requirements=[]
        )
        mock_resume = ResumeData(
            name="Test User",
            skills=["Python"],
            experience=[],
            education=[],
            raw_text="test"
        )
        mock_match = MatchResult(
            resume=mock_resume,
            overall_score=80.0,
            skills_score=100.0,
            experience_score=50.0,
            education_score=100.0,
            matched_skills=["Python"],
            skill_gaps=[],
            strengths=[]
        )
        mock_result = CandidateResult(
            rank=1,
            name="Test User",
            overall_score=80.0,
            skills_score=100.0,
            experience_score=50.0,
            education_score=100.0,
            matched_skills=["Python"],
            skill_gaps=[],
            strengths=[],
            explanation="Test"
        )
        
        runner.analyzer.analyze_job_description = Mock(return_value=(mock_job_req, None))
        runner.parser.parse_resume = Mock(return_value=(mock_resume, None))
        runner.matcher.match_candidate = Mock(return_value=mock_match)
        runner.ranker.rank_candidates = Mock(return_value=[mock_result])
        
        # Create a mock status
        mock_status = ProcessingStatus(
            current_agent="Test",
            processed_count=0,
            total_count=1,
            is_complete=False,
            start_time=datetime.now(),
            elapsed_seconds=0.0
        )
        mock_update.return_value = mock_status
        
        runner.process([b"fake pdf"], "Test job description")
        
        # Verify status updates were called
        assert mock_update.call_count >= 4  # At least Analyzer, Parser, Matcher, Ranker


class TestRunnerErrorHandling:
    """Test error handling and continuation."""

    def test_returns_error_when_job_description_fails(self):
        """Returns error when job description analysis fails."""
        runner = ResumeScreeningRunner()
        runner.analyzer.analyze_job_description = Mock(return_value=(None, "API Error"))
        
        results, error = runner.process([b"fake pdf"], "Test job")
        
        assert results == []
        assert error is not None
        assert "Failed to analyze job description" in error

    def test_continues_when_single_resume_fails(self):
        """Continues processing when one resume fails to parse."""
        runner = ResumeScreeningRunner()
        
        mock_job_req = JobRequirements(
            title="Test",
            required_skills=["Python"],
            preferred_skills=[],
            min_experience_years=0,
            education_requirements=[]
        )
        mock_resume = ResumeData(
            name="Good Resume",
            skills=["Python"],
            experience=[],
            education=[],
            raw_text="test"
        )
        mock_match = MatchResult(
            resume=mock_resume,
            overall_score=80.0,
            skills_score=100.0,
            experience_score=100.0,
            education_score=100.0,
            matched_skills=["Python"],
            skill_gaps=[],
            strengths=[]
        )
        mock_result = CandidateResult(
            rank=1,
            name="Good Resume",
            overall_score=80.0,
            skills_score=100.0,
            experience_score=100.0,
            education_score=100.0,
            matched_skills=["Python"],
            skill_gaps=[],
            strengths=[],
            explanation="Test"
        )
        
        runner.analyzer.analyze_job_description = Mock(return_value=(mock_job_req, None))
        # First resume fails, second succeeds
        runner.parser.parse_resume = Mock(side_effect=[
            (None, "Parse error"),
            (mock_resume, None)
        ])
        runner.matcher.match_candidate = Mock(return_value=mock_match)
        runner.ranker.rank_candidates = Mock(return_value=[mock_result])
        
        results, error = runner.process([b"bad pdf", b"good pdf"], "Test job")
        
        # Should have one result from the successful resume
        assert len(results) == 1
        assert results[0].name == "Good Resume"

    def test_returns_error_when_all_resumes_fail(self):
        """Returns error when all resumes fail to parse."""
        runner = ResumeScreeningRunner()
        
        mock_job_req = JobRequirements(
            title="Test",
            required_skills=["Python"],
            preferred_skills=[],
            min_experience_years=0,
            education_requirements=[]
        )
        
        runner.analyzer.analyze_job_description = Mock(return_value=(mock_job_req, None))
        runner.parser.parse_resume = Mock(return_value=(None, "Parse error"))
        
        results, error = runner.process([b"bad pdf"], "Test job")
        
        assert results == []
        assert error is not None
        assert "No resumes could be parsed" in error


class TestRunnerStatusUpdates:
    """Test status update functionality."""

    def test_status_callback_receives_updates(self):
        """Status callback receives updates during processing."""
        runner = ResumeScreeningRunner()
        
        mock_job_req = JobRequirements(
            title="Test",
            required_skills=["Python"],
            preferred_skills=[],
            min_experience_years=0,
            education_requirements=[]
        )
        mock_resume = ResumeData(
            name="Test",
            skills=["Python"],
            experience=[],
            education=[],
            raw_text="test"
        )
        mock_match = MatchResult(
            resume=mock_resume,
            overall_score=80.0,
            skills_score=100.0,
            experience_score=100.0,
            education_score=100.0,
            matched_skills=["Python"],
            skill_gaps=[],
            strengths=[]
        )
        mock_result = CandidateResult(
            rank=1,
            name="Test",
            overall_score=80.0,
            skills_score=100.0,
            experience_score=100.0,
            education_score=100.0,
            matched_skills=["Python"],
            skill_gaps=[],
            strengths=[],
            explanation="Test"
        )
        
        runner.analyzer.analyze_job_description = Mock(return_value=(mock_job_req, None))
        runner.parser.parse_resume = Mock(return_value=(mock_resume, None))
        runner.matcher.match_candidate = Mock(return_value=mock_match)
        runner.ranker.rank_candidates = Mock(return_value=[mock_result])
        
        status_updates = []
        def callback(status):
            status_updates.append(status.current_agent)
        
        runner.process([b"pdf"], "Test job", on_status_update=callback)
        
        # Should have received multiple status updates
        assert len(status_updates) >= 4
        assert "Analyzer" in status_updates
        assert "Parser" in status_updates
        assert "Matcher" in status_updates

    def test_final_status_is_complete(self):
        """Final status has is_complete=True."""
        runner = ResumeScreeningRunner()
        
        mock_job_req = JobRequirements(
            title="Test",
            required_skills=["Python"],
            preferred_skills=[],
            min_experience_years=0,
            education_requirements=[]
        )
        mock_resume = ResumeData(
            name="Test",
            skills=["Python"],
            experience=[],
            education=[],
            raw_text="test"
        )
        mock_match = MatchResult(
            resume=mock_resume,
            overall_score=80.0,
            skills_score=100.0,
            experience_score=100.0,
            education_score=100.0,
            matched_skills=["Python"],
            skill_gaps=[],
            strengths=[]
        )
        mock_result = CandidateResult(
            rank=1,
            name="Test",
            overall_score=80.0,
            skills_score=100.0,
            experience_score=100.0,
            education_score=100.0,
            matched_skills=["Python"],
            skill_gaps=[],
            strengths=[],
            explanation="Test"
        )
        
        runner.analyzer.analyze_job_description = Mock(return_value=(mock_job_req, None))
        runner.parser.parse_resume = Mock(return_value=(mock_resume, None))
        runner.matcher.match_candidate = Mock(return_value=mock_match)
        runner.ranker.rank_candidates = Mock(return_value=[mock_result])
        
        runner.process([b"pdf"], "Test job")
        
        final_status = runner.get_status()
        assert final_status is not None
        assert final_status.is_complete is True
