"""Resume Screening Runner - orchestrates the agent pipeline."""

import logging
from datetime import datetime
from typing import List, Callable, Optional

from src.models.resume import ResumeData
from src.models.job import JobRequirements
from src.models.match import MatchResult
from src.models.candidate import CandidateResult
from src.models.status import ProcessingStatus
from src.agents.parser import ParserAgent
from src.agents.analyzer import AnalyzerAgent
from src.agents.matcher import MatcherAgent
from src.agents.ranker import RankerAgent

logger = logging.getLogger(__name__)


class ResumeScreeningRunner:
    """Orchestrates the resume screening agent pipeline."""

    def __init__(self):
        self.parser = ParserAgent()
        self.analyzer = AnalyzerAgent()
        self.matcher = MatcherAgent()
        self.ranker = RankerAgent()
        self._status: Optional[ProcessingStatus] = None

    def get_status(self) -> Optional[ProcessingStatus]:
        """Get current processing status."""
        return self._status

    def _update_status(
        self,
        agent: str,
        processed: int,
        total: int,
        start_time: datetime,
        error: Optional[str] = None,
        is_complete: bool = False
    ) -> ProcessingStatus:
        """Update and return processing status."""
        elapsed = (datetime.now() - start_time).total_seconds()
        self._status = ProcessingStatus(
            current_agent=agent,
            processed_count=processed,
            total_count=total,
            is_complete=is_complete,
            start_time=start_time,
            elapsed_seconds=elapsed,
            error_message=error
        )
        return self._status

    def process(
        self,
        pdf_files: List[bytes],
        job_description: str,
        on_status_update: Optional[Callable[[ProcessingStatus], None]] = None,
        generate_explanations: bool = True
    ) -> tuple[List[CandidateResult], Optional[str]]:
        """Process resumes against job description.
        
        Args:
            pdf_files: List of PDF file contents as bytes
            job_description: Job description text
            on_status_update: Optional callback for status updates
            generate_explanations: Whether to generate AI explanations
            
        Returns:
            Tuple of (results, error_message)
        """
        start_time = datetime.now()
        total_resumes = len(pdf_files)
        
        def notify(status: ProcessingStatus):
            if on_status_update:
                on_status_update(status)

        # Step 1: Analyze job description
        notify(self._update_status("Analyzer", 0, total_resumes, start_time))
        
        job_requirements, error = self.analyzer.analyze_job_description(job_description)
        if error:
            status = self._update_status("Analyzer", 0, total_resumes, start_time, error=error)
            notify(status)
            return [], f"Failed to analyze job description: {error}"

        # Step 2: Parse resumes
        parsed_resumes: List[ResumeData] = []
        errors: List[str] = []
        
        for i, pdf_bytes in enumerate(pdf_files):
            notify(self._update_status("Parser", i, total_resumes, start_time))
            
            resume_data, error = self.parser.parse_resume(pdf_bytes)
            if error:
                logger.warning(f"Failed to parse resume {i+1}: {error}")
                errors.append(f"Resume {i+1}: {error}")
                continue
            
            parsed_resumes.append(resume_data)

        if not parsed_resumes:
            error_msg = "No resumes could be parsed"
            status = self._update_status("Parser", total_resumes, total_resumes, start_time, error=error_msg)
            notify(status)
            return [], error_msg

        # Step 3: Match candidates
        matches: List[MatchResult] = []
        
        for i, resume in enumerate(parsed_resumes):
            notify(self._update_status("Matcher", i, len(parsed_resumes), start_time))
            
            try:
                match_result = self.matcher.match_candidate(resume, job_requirements)
                matches.append(match_result)
            except Exception as e:
                logger.warning(f"Failed to match candidate {resume.name}: {e}")
                errors.append(f"Matching {resume.name}: {str(e)}")
                continue

        if not matches:
            error_msg = "No candidates could be matched"
            status = self._update_status("Matcher", len(parsed_resumes), len(parsed_resumes), start_time, error=error_msg)
            notify(status)
            return [], error_msg

        # Step 4: Rank candidates
        notify(self._update_status("Ranker", 0, len(matches), start_time))
        
        try:
            results = self.ranker.rank_candidates(matches, generate_explanations=generate_explanations)
        except Exception as e:
            logger.error(f"Failed to rank candidates: {e}")
            # Return unranked results as fallback
            results = self.ranker.rank_candidates(matches, generate_explanations=False)

        # Complete
        status = self._update_status("Complete", len(results), len(results), start_time, is_complete=True)
        notify(status)

        error_summary = "; ".join(errors) if errors else None
        return results, error_summary

    def process_from_text(
        self,
        resume_texts: List[str],
        job_description: str,
        on_status_update: Optional[Callable[[ProcessingStatus], None]] = None,
        generate_explanations: bool = False
    ) -> tuple[List[CandidateResult], Optional[str]]:
        """Process resumes from text (for testing without PDFs).
        
        Args:
            resume_texts: List of resume text contents
            job_description: Job description text
            on_status_update: Optional callback for status updates
            generate_explanations: Whether to generate AI explanations
            
        Returns:
            Tuple of (results, error_message)
        """
        start_time = datetime.now()
        total_resumes = len(resume_texts)
        
        def notify(status: ProcessingStatus):
            if on_status_update:
                on_status_update(status)

        # Step 1: Analyze job description
        notify(self._update_status("Analyzer", 0, total_resumes, start_time))
        
        job_requirements, error = self.analyzer.analyze_job_description(job_description)
        if error:
            status = self._update_status("Analyzer", 0, total_resumes, start_time, error=error)
            notify(status)
            return [], f"Failed to analyze job description: {error}"

        # Step 2: Parse resumes from text
        parsed_resumes: List[ResumeData] = []
        errors: List[str] = []
        
        for i, text in enumerate(resume_texts):
            notify(self._update_status("Parser", i, total_resumes, start_time))
            
            resume_data, error = self.parser.parse_resume_from_text(text)
            if error:
                logger.warning(f"Failed to parse resume {i+1}: {error}")
                errors.append(f"Resume {i+1}: {error}")
                continue
            
            parsed_resumes.append(resume_data)

        if not parsed_resumes:
            error_msg = "No resumes could be parsed"
            status = self._update_status("Parser", total_resumes, total_resumes, start_time, error=error_msg)
            notify(status)
            return [], error_msg

        # Step 3: Match candidates
        matches: List[MatchResult] = []
        
        for i, resume in enumerate(parsed_resumes):
            notify(self._update_status("Matcher", i, len(parsed_resumes), start_time))
            
            try:
                match_result = self.matcher.match_candidate(resume, job_requirements)
                matches.append(match_result)
            except Exception as e:
                logger.warning(f"Failed to match candidate {resume.name}: {e}")
                errors.append(f"Matching {resume.name}: {str(e)}")
                continue

        if not matches:
            error_msg = "No candidates could be matched"
            status = self._update_status("Matcher", len(parsed_resumes), len(parsed_resumes), start_time, error=error_msg)
            notify(status)
            return [], error_msg

        # Step 4: Rank candidates
        notify(self._update_status("Ranker", 0, len(matches), start_time))
        
        try:
            results = self.ranker.rank_candidates(matches, generate_explanations=generate_explanations)
        except Exception as e:
            logger.error(f"Failed to rank candidates: {e}")
            results = self.ranker.rank_candidates(matches, generate_explanations=False)

        # Complete
        status = self._update_status("Complete", len(results), len(results), start_time, is_complete=True)
        notify(status)

        error_summary = "; ".join(errors) if errors else None
        return results, error_summary
