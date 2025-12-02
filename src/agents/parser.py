"""Parser Agent for extracting structured data from resumes."""

import json
import logging
from typing import Optional

from src.config import GEMINI_MODEL, get_gemini_api_key
from src.models.resume import ResumeData, ExperienceEntry, EducationEntry
from src.utils.pdf_extractor import PDFExtractor

logger = logging.getLogger(__name__)


class ParserAgent:
    """Extracts structured data from resume PDFs using Gemini API."""

    def __init__(self):
        self.pdf_extractor = PDFExtractor()
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

    def extract_text(self, pdf_bytes: bytes) -> tuple[str, Optional[str]]:
        """Extract text from PDF bytes.
        
        Args:
            pdf_bytes: Raw PDF file content
            
        Returns:
            Tuple of (text, error_message)
        """
        return self.pdf_extractor.extract_text(pdf_bytes)

    def _build_prompt(self, text: str) -> str:
        """Build the prompt for Gemini to extract resume data."""
        return f"""Extract structured information from this resume text. Return ONLY valid JSON with this exact structure:
{{
    "name": "Full Name",
    "email": "email@example.com or null",
    "phone": "phone number or null",
    "skills": ["skill1", "skill2"],
    "experience": [
        {{
            "title": "Job Title",
            "company": "Company Name",
            "duration_months": 24,
            "description": "Brief description"
        }}
    ],
    "education": [
        {{
            "degree": "Degree Name",
            "institution": "University Name",
            "year": 2020,
            "field": "Field of Study or null"
        }}
    ]
}}

Resume text:
{text}

Return ONLY the JSON, no other text."""

    def parse_resume(self, pdf_bytes: bytes) -> tuple[Optional[ResumeData], Optional[str]]:
        """Parse a resume PDF and extract structured data.
        
        Args:
            pdf_bytes: Raw PDF file content
            
        Returns:
            Tuple of (ResumeData, error_message)
            If successful, error_message is None
            If failed, ResumeData is None
        """
        # Extract text from PDF
        text, error = self.extract_text(pdf_bytes)
        if error:
            return None, error

        try:
            # Call Gemini API
            model = self._get_model()
            prompt = self._build_prompt(text)
            response = model.generate_content(prompt)
            
            # Parse JSON response
            response_text = response.text.strip()
            # Remove markdown code blocks if present
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])
            
            data = json.loads(response_text)
            
            # Build ResumeData
            experience = [
                ExperienceEntry(
                    title=exp.get("title", ""),
                    company=exp.get("company", ""),
                    duration_months=exp.get("duration_months") or 0,
                    description=exp.get("description", "")
                )
                for exp in data.get("experience", [])
            ]
            
            education = [
                EducationEntry(
                    degree=edu.get("degree", ""),
                    institution=edu.get("institution", ""),
                    year=edu.get("year"),
                    field=edu.get("field")
                )
                for edu in data.get("education", [])
            ]
            
            resume_data = ResumeData(
                name=data.get("name", "Unknown"),
                email=data.get("email"),
                phone=data.get("phone"),
                skills=data.get("skills", []),
                experience=experience,
                education=education,
                raw_text=text
            )
            
            return resume_data, None
            
        except json.JSONDecodeError as e:
            error_msg = f"Failed to parse Gemini response as JSON: {e}"
            logger.error(error_msg)
            return None, error_msg
        except Exception as e:
            error_msg = f"Failed to parse resume: {e}"
            logger.error(error_msg)
            return None, error_msg

    def parse_resume_from_text(self, text: str) -> tuple[Optional[ResumeData], Optional[str]]:
        """Parse resume from raw text (for testing without PDF).
        
        Args:
            text: Resume text content
            
        Returns:
            Tuple of (ResumeData, error_message)
        """
        if not text or not text.strip():
            return None, "Empty resume text"

        try:
            model = self._get_model()
            prompt = self._build_prompt(text)
            response = model.generate_content(prompt)
            
            response_text = response.text.strip()
            if response_text.startswith("```"):
                lines = response_text.split("\n")
                response_text = "\n".join(lines[1:-1])
            
            data = json.loads(response_text)
            
            experience = [
                ExperienceEntry(
                    title=exp.get("title", ""),
                    company=exp.get("company", ""),
                    duration_months=exp.get("duration_months") or 0,
                    description=exp.get("description", "")
                )
                for exp in data.get("experience", [])
            ]
            
            education = [
                EducationEntry(
                    degree=edu.get("degree", ""),
                    institution=edu.get("institution", ""),
                    year=edu.get("year"),
                    field=edu.get("field")
                )
                for edu in data.get("education", [])
            ]
            
            resume_data = ResumeData(
                name=data.get("name", "Unknown"),
                email=data.get("email"),
                phone=data.get("phone"),
                skills=data.get("skills", []),
                experience=experience,
                education=education,
                raw_text=text
            )
            
            return resume_data, None
            
        except Exception as e:
            error_msg = f"Failed to parse resume text: {e}"
            logger.error(error_msg)
            return None, error_msg
