import re
import unicodedata
from dataclasses import dataclass

CONTRACTIONS = [
    (re.compile(r"\bwasn['’]t\b", re.IGNORECASE), "was not"),
    (re.compile(r"\bweren['’]t\b", re.IGNORECASE), "were not"),
    (re.compile(r"\bdidn['’]t\b", re.IGNORECASE), "did not"),
    (re.compile(r"\bhaven['’]t\b", re.IGNORECASE), "have not"),
    (re.compile(r"\bhasn['’]t\b", re.IGNORECASE), "has not"),
    (re.compile(r"\bcouldn['’]t\b", re.IGNORECASE), "could not"),
    (re.compile(r"\bcan['’]t\b", re.IGNORECASE), "can not"),
    (re.compile(r"\bcannot\b", re.IGNORECASE), "can not"),
    (re.compile(r"\bwon['’]t\b", re.IGNORECASE), "will not"),
    (re.compile(r"\bshouldn['’]t\b", re.IGNORECASE), "should not"),
    (re.compile(r"\bisn['’]t\b", re.IGNORECASE), "is not"),
    (re.compile(r"\baren['’]t\b", re.IGNORECASE), "are not"),
    (re.compile(r"\bdon['’]t\b", re.IGNORECASE), "do not"),
    (re.compile(r"\bdoesn['’]t\b", re.IGNORECASE), "does not"),
]

# Known abbreviations that should not trigger sentence boundaries
PROTECTED_ABBREVIATIONS = (
    "e.g.", "i.e.", "approx.", "dr.", "p.s.i.", "psi.", "no.", "vs.",
    "dept.", "spec.", "vol.", "temp.", "fig.", "rev.", "min.", "max.",
    "sec.", "hr.", "hrs.", "est.", "mfg.", "tel.", "ref."
)


@dataclass(frozen=True)
class PreprocessedText:
    original_text: str
    normalized_text: str
    sentences: list[str]
    tokens: list[str]


def _expand_contractions(text: str) -> str:
    for pattern, replacement in CONTRACTIONS:
        text = pattern.sub(replacement, text)
    return text


def split_sentences(text: str) -> list[str]:
    """Split text into sentences while protecting decimals, abbreviations, and bullets."""
    if not text or not text.strip():
        return []

    # Protect known abbreviations by replacing periods with a placeholder
    protected = text
    placeholder = "\u0000"

    # Protect numbered list markers at start of lines (e.g., "1. Supervisor notified")
    protected = re.sub(r"(?m)^\s*(\d+)\.\s+", rf"\1{placeholder} ", protected)

    for abbr in PROTECTED_ABBREVIATIONS:
        pattern = re.compile(re.escape(abbr), re.IGNORECASE)
        protected = pattern.sub(lambda m: m.group(0).replace(".", placeholder), protected)

    # Protect decimal numbers (e.g., 10.5, 3.14)
    protected = re.sub(r"(\d+)\.(\d+)", rf"\1{placeholder}\2", protected)

    # Protect equipment codes like P-101.A
    protected = re.sub(r"([A-Za-z0-9]+)\.([A-Za-z0-9]+)", rf"\1{placeholder}\2", protected)

    # Split on sentence boundaries:
    # 1. Newlines
    # 2. Lookbehind for punctuation (.!?) followed by whitespace or end-of-string
    # 3. Semicolons followed by whitespace
    raw_segments = re.split(r"(?:[\r\n]+|;\s+|(?<=[.!?])\s+)", protected)

    sentences = []
    for segment in raw_segments:
        # Restore placeholder periods
        restored = segment.replace(placeholder, ".").strip()
        # Clean bullet markers at start (e.g. "- ", "* ", "1. ", "• ")
        cleaned = re.sub(r"^(?:[\-\*•\u2022]\s*|\d+\.\s*)", "", restored).strip()
        if cleaned:
            sentences.append(cleaned)



    return sentences or [text.strip()]


def preprocess_text(text: str) -> PreprocessedText:
    """
    Normalize analysis text while preserving original text and safety-critical terms.
    
    Guarantees:
    - Original text is retained verbatim for evidence extraction and auditing.
    - Contractions are expanded (e.g. wasn't -> was not) so negation is explicit.
    - Decimals, abbreviations, and line breaks are handled cleanly in sentence segmentation.
    - Safety-critical terms (not, no, without, before, failed, etc.) are strictly preserved.
    """
    unicode_text = unicodedata.normalize("NFKC", text)
    normalized = re.sub(r"[\u2018\u2019]", "'", unicode_text)
    normalized = re.sub(r"[\u201c\u201d]", '"', normalized)
    normalized = re.sub(r"[\u2013\u2014]", "-", normalized)

    # Expand contractions before sentence splitting to preserve negation semantics
    expanded = _expand_contractions(normalized)

    # Robust sentence splitting on the expanded text
    sentences = split_sentences(expanded)

    # Collapse whitespace for the canonical normalized text
    collapsed = re.sub(r"\s+", " ", expanded).strip()
    normalized_lower = collapsed.lower()

    tokens = re.findall(r"[a-z0-9]+(?:-[a-z0-9]+)?", normalized_lower)

    return PreprocessedText(
        original_text=text,
        normalized_text=normalized_lower,
        sentences=sentences or [collapsed],
        tokens=tokens
    )
