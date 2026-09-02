import re
import unicodedata
from dataclasses import dataclass


@dataclass(frozen=True)
class PreprocessedText:
    original_text: str
    normalized_text: str
    sentences: list[str]
    tokens: list[str]


def preprocess_text(text: str) -> PreprocessedText:
    """Normalize analysis text while retaining exact source text for evidence."""
    unicode_text = unicodedata.normalize("NFKC", text)
    normalized = re.sub(r"[\u2018\u2019]", "'", unicode_text)
    normalized = re.sub(r"[\u201c\u201d]", '"', normalized)
    normalized = re.sub(r"\s+", " ", normalized).strip()
    sentences = [part.strip() for part in re.split(r"(?<=[.!?])\s+", normalized) if part.strip()]
    return PreprocessedText(text, normalized.lower(), sentences or [normalized], re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)?", normalized.lower()))
