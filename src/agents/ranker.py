"""Ranker Agent for ranking candidates by match score."""

import logging
from typing import List, Optional

from src.config import GEMINI_MODEL, get_gemini_api_key
from src.models.match import MatchResult
from src.models.candidate import CandidateResult

logger = logging.getLogger(__name__)


class RankerAgent:
    """Ranks candidates by match score and generates explanations."""

    def __init__(self):
        self._model = None

    def _get_model(self):
        """Lazy initialization of Gemini model."""
        if self._model is None:
            import google.generativeai as genai
            api_key = get_gemini_api_key()
            if not api_key:
                raise ValueError("GEMINI_API_KEY not configured")
            genai.configure(api_key=api_key)
            self._model = genai.GenerativeModel(GEMINI_MODEL)
        return self._model

    def rank_candidates(
        self, 
        matches: List[MatchResult],
        generate_explanations: bool = True
    ) -> List[CandidateResult]:
        """Rank candidates by match score.
        
        Args:
            matches: List of MatchResult objects
            generate_explanations: Whether to generate AI explanations
            
        Returns:
            List of CandidateResult sorted by score descending
        """
        if not matches:
            return []

        # Sort by overall score descending, then by matched_skills count for tiebreaker
        sorted_matches = sorted(
            matches,
            key=lambda m: (m.overall_score, len(m.matched_skills)),
            reverse=True
        )

        results = []
        for rank, match in enumerate(sorted_matches, start=1):
            if generate_explanations:
                explanation = self.generate_explanation(match, rank)
            else:
                explanation = self._generate_simple_explanation(match, rank)
            
            result = CandidateResult(
                rank=rank,
                name=match.resume.name,
                overall_score=match.overall_score,
                skills_score=match.skills_score,
                experience_score=match.experience_score,
                education_score=match.education_score,
                matched_skills=match.matched_skills,
                skill_gaps=match.skill_gaps,
                strengths=match.strengths,
                explanation=explanation
            )
            results.append(result)

        return results

    def _generate_simple_explanation(self, match: MatchResult, rank: int) -> str:
        """Generate a simple explanation without AI.
        
        Args:
            match: MatchResult for the candidate
            rank: Ranking position
            
        Returns:
            Simple explanation string
        """
        parts = [f"Ranked #{rank} with {match.overall_score:.1f}% match."]
        
        if match.matched_skills:
            parts.append(f"Has {len(match.matched_skills)} matching skills.")
        
        if match.skill_gaps:
            parts.append(f"Missing {len(match.skill_gaps)} required skills.")
        
        if match.strengths:
            parts.append(f"Strengths: {', '.join(match.strengths[:2])}.")
        
        return " ".join(parts)

    def generate_explanation(self, match: MatchResult, rank: int) -> str:
        """Generate an AI-powered explanation for the ranking.
        
        Args:
            match: MatchResult for the candidate
            rank: Ranking position
            
        Returns:
            Explanation string
        """
        try:
            model = self._get_model()
            
            prompt = f"""Generate a brief 2-3 sentence explanation for why this candidate is ranked #{rank}.

Candidate: {match.resume.name}
Overall Score: {match.overall_score:.1f}%
Skills Score: {match.skills_score:.1f}%
Experience Score: {match.experience_score:.1f}%
Education Score: {match.education_score:.1f}%
Matched Skills: {', '.join(match.matched_skills) if match.matched_skills else 'None'}
Missing Skills: {', '.join(match.skill_gaps) if match.skill_gaps else 'None'}
Strengths: {', '.join(match.strengths) if match.strengths else 'None'}

Write a professional, concise explanation. Return ONLY the explanation text."""

            response = model.generate_content(prompt)
            return response.text.strip()
            
        except Exception as e:
            logger.warning(f"Failed to generate AI explanation: {e}")
            return self._generate_simple_explanation(match, rank)
