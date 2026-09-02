from dataclasses import dataclass

from app.services.nlp.entity_extractor import ExtractedEntities
from app.services.nlp.preprocessing import PreprocessedText


@dataclass(frozen=True)
class Evidence:
    evidence_span: str | None
    evidence_sentences: list[str]
    evidence_terms: list[str]
    confidence: float


def extract_evidence(document: PreprocessedText, entities: ExtractedEntities) -> Evidence:
    terms = [term.lower() for term in entities.matched_terms]
    hits = [sentence for sentence in document.sentences if any(term in sentence.lower() for term in terms)]
    span = " ".join(hits) if hits else None
    return Evidence(span, hits, entities.matched_terms, 1.0 if span and terms else 0.0)
