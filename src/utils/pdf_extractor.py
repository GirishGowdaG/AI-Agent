"""PDF text extraction utility using PyMuPDF."""

import logging
from typing import Optional, Tuple

logger = logging.getLogger(__name__)


class PDFExtractionError(Exception):
    """Raised when PDF extraction fails."""
    pass


class PDFExtractor:
    """Extracts text content from PDF files using PyMuPDF."""

    def extract_text(self, pdf_bytes: bytes) -> Tuple[str, Optional[str]]:
        """Extract text from PDF bytes.
        
        Args:
            pdf_bytes: Raw PDF file content as bytes
            
        Returns:
            Tuple of (extracted_text, error_message)
            If successful, error_message is None
            If failed, extracted_text is empty string
        """
        try:
            import fitz  # PyMuPDF
        except ImportError:
            return "", "PyMuPDF not installed. Run: pip install PyMuPDF"

        if not pdf_bytes:
            return "", "Empty PDF file"

        try:
            # Open PDF from bytes
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            
            if doc.page_count == 0:
                doc.close()
                return "", "PDF has no pages"
            
            # Extract text from all pages
            text_parts = []
            for page_num in range(doc.page_count):
                page = doc[page_num]
                text = page.get_text()
                if text:
                    text_parts.append(text)
            
            doc.close()
            
            full_text = "\n".join(text_parts).strip()
            
            if not full_text:
                return "", "PDF contains no extractable text"
            
            return full_text, None
            
        except Exception as e:
            error_msg = f"Failed to extract PDF text: {str(e)}"
            logger.error(error_msg)
            return "", error_msg

    def is_valid_pdf(self, pdf_bytes: bytes) -> bool:
        """Check if bytes represent a valid PDF file.
        
        Args:
            pdf_bytes: Raw file content as bytes
            
        Returns:
            True if valid PDF, False otherwise
        """
        if not pdf_bytes:
            return False
        
        # Check PDF magic bytes
        if not pdf_bytes.startswith(b'%PDF'):
            return False
        
        try:
            import fitz
            doc = fitz.open(stream=pdf_bytes, filetype="pdf")
            is_valid = doc.page_count >= 0
            doc.close()
            return is_valid
        except Exception:
            return False
