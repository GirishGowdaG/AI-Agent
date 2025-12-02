"""Property-based tests for input validation.

**Feature: resume-screening-agent, Property 1: File Upload Limit Validation**
**Feature: resume-screening-agent, Property 2: Non-PDF File Rejection**
**Feature: resume-screening-agent, Property 4: Job Description Length Validation**
**Validates: Requirements 1.1, 1.3, 2.1**
"""

from hypothesis import given, settings, strategies as st, HealthCheck

from src.utils.validation import (
    validate_file_count,
    validate_job_description_length,
    is_pdf,
    validate_pdf_files,
    validate_job_description,
    ValidationResult
)
from src.config import MAX_PDF_FILES, MAX_JOB_DESCRIPTION_LENGTH, MIN_JOB_DESCRIPTION_LENGTH


class TestFileUploadLimitValidation:
    """
    **Feature: resume-screening-agent, Property 1: File Upload Limit Validation**
    **Validates: Requirements 1.1**
    
    For any number of PDF files submitted to the uploader, the system should 
    accept the upload if and only if the count is between 1 and 50 inclusive.
    """

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(st.integers(min_value=1, max_value=MAX_PDF_FILES))
    def test_valid_file_count_accepted(self, count: int):
        """File counts between 1 and 50 are accepted."""
        result = validate_file_count(count)
        assert result.is_valid is True
        assert result.error_message is None

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(st.integers(min_value=MAX_PDF_FILES + 1, max_value=200))
    def test_excessive_file_count_rejected(self, count: int):
        """File counts above 50 are rejected."""
        result = validate_file_count(count)
        assert result.is_valid is False
        assert result.error_message is not None
        assert "Too many files" in result.error_message

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(st.integers(min_value=-100, max_value=0))
    def test_zero_or_negative_file_count_rejected(self, count: int):
        """File counts of 0 or negative are rejected."""
        result = validate_file_count(count)
        assert result.is_valid is False
        assert result.error_message is not None

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(st.integers(min_value=1, max_value=200))
    def test_file_count_boundary(self, count: int):
        """File count validation correctly handles boundary at 50."""
        result = validate_file_count(count)
        
        if 1 <= count <= MAX_PDF_FILES:
            assert result.is_valid is True
        else:
            assert result.is_valid is False


class TestNonPDFFileRejection:
    """
    **Feature: resume-screening-agent, Property 2: Non-PDF File Rejection**
    **Validates: Requirements 1.3**
    
    For any uploaded file with a non-PDF extension or MIME type, the system 
    should reject the file and return an error indicating PDF format is required.
    """

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(st.binary(min_size=10, max_size=100))
    def test_random_bytes_not_pdf(self, data: bytes):
        """Random bytes that don't start with %PDF are not valid PDFs."""
        # Ensure data doesn't accidentally start with PDF magic bytes
        if data.startswith(b'%PDF'):
            data = b'NOTPDF' + data[4:]
        
        assert is_pdf(data) is False

    def test_pdf_magic_bytes_recognized(self):
        """Files starting with %PDF are recognized as PDFs."""
        pdf_bytes = b'%PDF-1.4 fake pdf content'
        assert is_pdf(pdf_bytes) is True

    def test_empty_bytes_not_pdf(self):
        """Empty bytes are not a valid PDF."""
        assert is_pdf(b'') is False

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(st.sampled_from([b'PK', b'GIF89a', b'\x89PNG', b'\xff\xd8\xff', b'RIFF']))
    def test_other_file_formats_rejected(self, magic_bytes: bytes):
        """Other file format magic bytes are rejected."""
        data = magic_bytes + b'some content here'
        assert is_pdf(data) is False

    def test_validate_pdf_files_rejects_non_pdf(self):
        """validate_pdf_files rejects non-PDF files."""
        non_pdf = b'This is not a PDF file'
        result = validate_pdf_files([non_pdf])
        
        assert result.is_valid is False
        assert "not valid PDFs" in result.error_message
        assert "PDF format is supported" in result.error_message

    def test_validate_pdf_files_accepts_pdf(self):
        """validate_pdf_files accepts valid PDF files."""
        pdf = b'%PDF-1.4 fake pdf content'
        result = validate_pdf_files([pdf])
        
        assert result.is_valid is True


class TestJobDescriptionLengthValidation:
    """
    **Feature: resume-screening-agent, Property 4: Job Description Length Validation**
    **Validates: Requirements 2.1**
    
    For any string input to the job description field, the system should 
    accept the input if and only if its length is between 1 and 10,000 characters inclusive.
    """

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(st.integers(min_value=MIN_JOB_DESCRIPTION_LENGTH, max_value=MAX_JOB_DESCRIPTION_LENGTH))
    def test_valid_length_accepted(self, length: int):
        """Lengths between 1 and 10000 are accepted."""
        result = validate_job_description_length(length)
        assert result.is_valid is True
        assert result.error_message is None

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(st.integers(min_value=MAX_JOB_DESCRIPTION_LENGTH + 1, max_value=50000))
    def test_excessive_length_rejected(self, length: int):
        """Lengths above 10000 are rejected."""
        result = validate_job_description_length(length)
        assert result.is_valid is False
        assert result.error_message is not None
        assert "too long" in result.error_message

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(st.integers(min_value=-100, max_value=0))
    def test_zero_or_negative_length_rejected(self, length: int):
        """Lengths of 0 or negative are rejected."""
        result = validate_job_description_length(length)
        assert result.is_valid is False
        assert result.error_message is not None

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(st.text(min_size=1, max_size=100, alphabet="abcdefghijklmnopqrstuvwxyz "))
    def test_valid_job_description_accepted(self, text: str):
        """Valid job descriptions are accepted."""
        result = validate_job_description(text)
        assert result.is_valid is True

    def test_empty_job_description_rejected(self):
        """Empty job description is rejected."""
        result = validate_job_description("")
        assert result.is_valid is False
        assert "required" in result.error_message

    def test_whitespace_only_job_description_rejected(self):
        """Whitespace-only job description is rejected."""
        result = validate_job_description("   \n\t  ")
        assert result.is_valid is False

    @settings(max_examples=100, suppress_health_check=[HealthCheck.too_slow])
    @given(st.integers(min_value=1, max_value=20000))
    def test_length_boundary(self, length: int):
        """Length validation correctly handles boundary at 10000."""
        result = validate_job_description_length(length)
        
        if MIN_JOB_DESCRIPTION_LENGTH <= length <= MAX_JOB_DESCRIPTION_LENGTH:
            assert result.is_valid is True
        else:
            assert result.is_valid is False
