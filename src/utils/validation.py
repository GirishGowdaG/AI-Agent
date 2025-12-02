"""Input validation utilities."""

from dataclasses import dataclass
from typing import List, Optional, Tuple

from src.config import MAX_PDF_FILES, MAX_JOB_DESCRIPTION_LENGTH, MIN_JOB_DESCRIPTION_LENGTH


@dataclass
class ValidationResult:
    """Result of a validation check."""
    is_valid: bool
    error_message: Optional[str] = None


def validate_pdf_files(files: List[bytes]) -> ValidationResult:
    """Validate uploaded PDF files.
    
    Args:
        files: List of file contents as bytes
        
    Returns:
        ValidationResult with is_valid and optional error_message
    """
    if not files:
        return ValidationResult(
            is_valid=False,
            error_message="No files uploaded. Please upload at least one PDF resume."
        )
    
    if len(files) > MAX_PDF_FILES:
        return ValidationResult(
            is_valid=False,
            error_message=f"Too many files. Maximum allowed is {MAX_PDF_FILES}, got {len(files)}."
        )
    
    # Validate each file is a PDF
    invalid_files = []
    for i, file_bytes in enumerate(files):
        if not is_pdf(file_bytes):
            invalid_files.append(i + 1)
    
    if invalid_files:
        return ValidationResult(
            is_valid=False,
            error_message=f"Invalid file format. Files at positions {invalid_files} are not valid PDFs. Only PDF format is supported."
        )
    
    return ValidationResult(is_valid=True)


def validate_file_count(count: int) -> ValidationResult:
    """Validate the number of files.
    
    Args:
        count: Number of files
        
    Returns:
        ValidationResult with is_valid and optional error_message
    """
    if count < 1:
        return ValidationResult(
            is_valid=False,
            error_message="No files uploaded. Please upload at least one PDF resume."
        )
    
    if count > MAX_PDF_FILES:
        return ValidationResult(
            is_valid=False,
            error_message=f"Too many files. Maximum allowed is {MAX_PDF_FILES}, got {count}."
        )
    
    return ValidationResult(is_valid=True)


def is_pdf(file_bytes: bytes) -> bool:
    """Check if file bytes represent a PDF.
    
    Args:
        file_bytes: File content as bytes
        
    Returns:
        True if file is a PDF, False otherwise
    """
    if not file_bytes:
        return False
    
    # Check PDF magic bytes
    return file_bytes.startswith(b'%PDF')


def validate_job_description(description: str) -> ValidationResult:
    """Validate job description input.
    
    Args:
        description: Job description text
        
    Returns:
        ValidationResult with is_valid and optional error_message
    """
    if not description:
        return ValidationResult(
            is_valid=False,
            error_message="Job description is required. Please enter a job description."
        )
    
    stripped = description.strip()
    
    if len(stripped) < MIN_JOB_DESCRIPTION_LENGTH:
        return ValidationResult(
            is_valid=False,
            error_message="Job description is too short. Please provide more details."
        )
    
    if len(stripped) > MAX_JOB_DESCRIPTION_LENGTH:
        return ValidationResult(
            is_valid=False,
            error_message=f"Job description is too long. Maximum allowed is {MAX_JOB_DESCRIPTION_LENGTH} characters, got {len(stripped)}."
        )
    
    return ValidationResult(is_valid=True)


def validate_job_description_length(length: int) -> ValidationResult:
    """Validate job description length.
    
    Args:
        length: Length of job description
        
    Returns:
        ValidationResult with is_valid and optional error_message
    """
    if length < MIN_JOB_DESCRIPTION_LENGTH:
        return ValidationResult(
            is_valid=False,
            error_message="Job description is too short. Please provide more details."
        )
    
    if length > MAX_JOB_DESCRIPTION_LENGTH:
        return ValidationResult(
            is_valid=False,
            error_message=f"Job description is too long. Maximum allowed is {MAX_JOB_DESCRIPTION_LENGTH} characters."
        )
    
    return ValidationResult(is_valid=True)
