"""Shared validation helpers for report text.

Design intent:
- ONE authoritative rule set for every path that accepts report text.
- Called from Pydantic @field_validators so validation fires at the HTTP
  boundary, before any service or NLP code is reached.
- Returns the *original* text unchanged — normalization for NLP is a
  separate concern handled inside the analysis pipeline.
- Raises ValueError so Pydantic converts it to a structured 422 response
  via the existing RequestValidationError handler.

Boundaries are configuration-driven via Settings so they can be changed
without hunting through schema files.
"""

from app.core.config import get_settings


def validate_report_text(text: str) -> str:
    """Validate report text content.

    Raises ``ValueError`` (captured by Pydantic as a field validation error)
    when the input is:
    - empty or whitespace-only
    - shorter than ``settings.report_text_min_length`` (meaningful chars)
    - longer than ``settings.report_text_max_length`` (raw bytes guard)

    Returns the *original, unmodified* text so the stored audit record
    preserves the submitter's exact wording.
    """
    settings = get_settings()

    stripped = text.strip()

    if not stripped:
        raise ValueError(
            "Report text must contain meaningful content, not only whitespace."
        )

    if len(stripped) < settings.report_text_min_length:
        raise ValueError(
            f"Report text must contain at least {settings.report_text_min_length} "
            "characters of meaningful content."
        )

    if len(text) > settings.report_text_max_length:
        raise ValueError(
            f"Report text must not exceed {settings.report_text_max_length} characters."
        )

    return text
