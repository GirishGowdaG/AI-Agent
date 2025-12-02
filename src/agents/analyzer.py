"""Analyzer Agent for extracting requirements from job descriptions."""

import json
import logging
from typing import Optional

from src.config import GEMINI_MODEL, get_gemini_api_key
from src.models.job import JobRequirements

logger = logging.getLogger(__name__)


class AnalyzerAgent:
    """Extracts structured requirements from job descriptions using Gemini API."""

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

    def _build_prompt(self, description: str) -> str:
        """Build the prompt for Gemini to extract job requirements."""
        return f"""Extract structured requirements from this job description. Return ONLY valid JSON with this exact structure:
{{
    "title": "Job Title",
    "required_skills": ["skill1", "skill2"],
    "preferred_skills": ["skill3", "skill4"],
    "min_experience_years": 3,
    "education_requirements": ["Bachelor's degree", "Master's preferred"],
    "responsibilities": ["responsibility1", "responsibility2"]
}}

Job Description:
{description}

Return ONLY the JSON, no other text."""

    def analyze_job_description(self, description: str) -> tuple[Optional[JobRequirements], Optional[str]]:
        """Analyze a job description and extract structured requirements.
        
        Args:
            description: Job description text
            
        Returns:
            Tuple of (JobRequirements, error_message)
            If successful, error_message is None
            If failed, JobRequirements is None
        """
        if not description or not description.strip():
            return None, "Empty job description"

        try:
            model = self._get_model()
            prompt = self._build_prompt(description)
            response = model.generate_content(prompt)
            
            response_text = response.text.strip()
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])
            
            data = json.loads(response_text)
            
            job_requirements = JobRequirements(
                title=data.get("title", "Unknown Position"),
                required_skills=data.get("required_skills", []),
                preferred_skills=data.get("preferred_skills", []),
                min_experience_years=data.get("min_experience_years") or 0,
                education_requirements=data.get("education_requirements", []),
                responsibilities=data.get("responsibilities", [])
            )
            
            return job_requirements, None
            
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse Gemini response as JSON: {e}"
            logger.error(error_msg)
            return None, error_msg
        except Exception as e:
            error_msg = f"Failed to analyze job description: {e}"
            logger.error(error_msg)
            return None, error_msg
