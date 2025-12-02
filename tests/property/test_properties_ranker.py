"""Property-based tests for Ranker Agent.

**Feature: resume-screening-agent, Property 10: Ranking Sort Order**
**Feature: resume-screening-agent, Property 11: Tiebreaker Consistency**
**Feature: resume-screening-agent, Property 12: Result Completeness**
**Validates: Requirements 5.1, 5.3, 5.4**
"""

from hypothesis import given, settings, strategies as st, HealthCheck

from src.models.resume import ResumeData, ExperienceEntry, EducationEntry
from src.models.match import MatchResult
from src.agents.ranker import RankerAgent

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
        field=None
    )


@st.composite
def resume_data(draw):
    """Generate random ResumeData."""
    return ResumeData(
        name=draw(st.text(min_size=1, max_size=30, alphabet=SIMPLE_CHARS)),
        skills=draw(st.lists(st.text(min_size=1, max_size=15, alphabet=SIMPLE_CHARS), min_size=0, max_size=5)),
        experience=draw(st.lists(experience_entry(), min_size=0, max_size=2)),
        education=draw(st.lists(education_entry(), min_size=0, max_size=2)),
        raw_text=draw(st.text(min_size=1, max_size=30, alphabet=SIMPLE_CHARS)),
        email=None,
        phone=None
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
        matched_skills=draw(st.lists(st.text(min_size=1, max_size=15, alphabet=SIMPLE_CHARS), min_size=0, max_size=5)),
        skill_gaps=draw(st.lists(st.text(min_size=1, max_size=15, alphabet=SIMPLE_CHARS), min_size=0, max_size=5)),
        strengths=draw(st.lists(st.text(min_size=1, max_size=30, alphabet=SIMPLE_CHARS), min_size=0, max_size=3))
    )


class TestRankingSortOrder:
    """
    **Feature: resume-screening-agent, Property 10: Ranking Sort Order**
    **Validates: Requirements 5.1**
    
    For any list of MatchResults processed by the Ranker_Agent, the output 
    CandidateResults should be sorted in descending order by overall_score.
    """

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(st.lists(match_result(), min_size=1, max_size=5))
    def test_results_sorted_by_score_descending(self, matches: list):
        """Results are sorted by overall_score in descending order."""
        ranker = RankerAgent()
        results = ranker.rank_candidates(matches, generate_explanations=False)
        
        # Check that scores are in descending order
        for i in range(len(results) - 1):
            assert results[i].overall_score >= results[i + 1].overall_score

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(st.lists(match_result(), min_size=1, max_size=5))
    def test_ranks_are_sequential(self, matches: list):
        """Ranks are sequential starting from 1."""
        ranker = RankerAgent()
        results = ranker.rank_candidates(matches, generate_explanations=False)
        
        for i, result in enumerate(results):
            assert result.rank == i + 1

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(st.lists(match_result(), min_size=1, max_size=5))
    def test_all_candidates_ranked(self, matches: list):
        """All input candidates appear in output."""
        ranker = RankerAgent()
        results = ranker.rank_candidates(matches, generate_explanations=False)
        
        assert len(results) == len(matches)


class TestTiebreakerConsistency:
    """
    **Feature: resume-screening-agent, Property 11: Tiebreaker Consistency**
    **Validates: Requirements 5.3**
    
    For any two candidates with identical overall_scores, the candidate 
    with more matched_skills should have a lower (better) rank.
    """

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(st.floats(min_value=0, max_value=100, allow_nan=False, allow_infinity=False))
    def test_tiebreaker_uses_matched_skills(self, score: float):
        """When scores are equal, more matched skills = better rank."""
        # Create two matches with same score but different matched_skills count
        resume1 = ResumeData(
            name="Candidate A",
            skills=["Python", "Java", "SQL"],
            experience=[],
            education=[],
            raw_text="test"
        )
        resume2 = ResumeData(
            name="Candidate B",
            skills=["Python"],
            experience=[],
            education=[],
            raw_text="test"
        )
        
        match1 = MatchResult(
            resume=resume1,
            overall_score=score,
            skills_score=score,
            experience_score=score,
            education_score=score,
            matched_skills=["Python", "Java", "SQL"],  # 3 skills
            skill_gaps=[],
            strengths=[]
        )
        match2 = MatchResult(
            resume=resume2,
            overall_score=score,
            skills_score=score,
            experience_score=score,
            education_score=score,
            matched_skills=["Python"],  # 1 skill
            skill_gaps=[],
            strengths=[]
        )
        
        ranker = RankerAgent()
        results = ranker.rank_candidates([match1, match2], generate_explanations=False)
        
        # Candidate with more matched skills should rank higher (lower rank number)
        candidate_a = next(r for r in results if r.name == "Candidate A")
        candidate_b = next(r for r in results if r.name == "Candidate B")
        
        assert candidate_a.rank < candidate_b.rank


class TestResultCompleteness:
    """
    **Feature: resume-screening-agent, Property 12: Result Completeness**
    **Validates: Requirements 5.4**
    
    For any CandidateResult in the ranking output, the object should contain 
    non-null values for: rank, name, overall_score, matched_skills, skill_gaps, 
    strengths, and explanation.
    """

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(st.lists(match_result(), min_size=1, max_size=5))
    def test_results_have_rank(self, matches: list):
        """All results have a valid rank."""
        ranker = RankerAgent()
        results = ranker.rank_candidates(matches, generate_explanations=False)
        
        for result in results:
            assert result.rank is not None
            assert isinstance(result.rank, int)
            assert result.rank > 0

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(st.lists(match_result(), min_size=1, max_size=5))
    def test_results_have_name(self, matches: list):
        """All results have a name."""
        ranker = RankerAgent()
        results = ranker.rank_candidates(matches, generate_explanations=False)
        
        for result in results:
            assert result.name is not None
            assert isinstance(result.name, str)

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(st.lists(match_result(), min_size=1, max_size=5))
    def test_results_have_overall_score(self, matches: list):
        """All results have an overall_score."""
        ranker = RankerAgent()
        results = ranker.rank_candidates(matches, generate_explanations=False)
        
        for result in results:
            assert result.overall_score is not None
            assert isinstance(result.overall_score, float)

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(st.lists(match_result(), min_size=1, max_size=5))
    def test_results_have_matched_skills(self, matches: list):
        """All results have matched_skills list."""
        ranker = RankerAgent()
        results = ranker.rank_candidates(matches, generate_explanations=False)
        
        for result in results:
            assert result.matched_skills is not None
            assert isinstance(result.matched_skills, list)

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(st.lists(match_result(), min_size=1, max_size=5))
    def test_results_have_skill_gaps(self, matches: list):
        """All results have skill_gaps list."""
        ranker = RankerAgent()
        results = ranker.rank_candidates(matches, generate_explanations=False)
        
        for result in results:
            assert result.skill_gaps is not None
            assert isinstance(result.skill_gaps, list)

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(st.lists(match_result(), min_size=1, max_size=5))
    def test_results_have_strengths(self, matches: list):
        """All results have strengths list."""
        ranker = RankerAgent()
        results = ranker.rank_candidates(matches, generate_explanations=False)
        
        for result in results:
            assert result.strengths is not None
            assert isinstance(result.strengths, list)

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(st.lists(match_result(), min_size=1, max_size=5))
    def test_results_have_explanation(self, matches: list):
        """All results have an explanation."""
        ranker = RankerAgent()
        results = ranker.rank_candidates(matches, generate_explanations=False)
        
        for result in results:
            assert result.explanation is not None
            assert isinstance(result.explanation, str)
            assert len(result.explanation) > 0
