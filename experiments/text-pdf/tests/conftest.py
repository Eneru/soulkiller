"""Fresh reusable extraction fixtures for evidence scenarios."""

import pytest

from soulkiller_text import ExtractionResult, extract_utf8

from .synthetic_sources import CODEPOINT_TEXT


@pytest.fixture
def successful_extraction() -> ExtractionResult:
    """Provide independently decoded synthetic text for each evidence test."""
    return extract_utf8(CODEPOINT_TEXT.encode("utf-8"))
