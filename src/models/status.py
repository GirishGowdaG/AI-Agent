"""Processing status data model."""

from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional

from src.config import SCHEMA_VERSION


@dataclass
class ProcessingStatus:
    """Status of the resume screening process."""
    current_agent: str
    processed_count: int
    total_count: int
    is_complete: bool
    start_time: datetime
    elapsed_seconds: float = 0.0
    error_message: Optional[str] = None
    schema_version: str = field(default=SCHEMA_VERSION)
