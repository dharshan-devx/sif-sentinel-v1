from dataclasses import dataclass
from enum import Enum


class EvidenceType(Enum):
    HAZARD = "HAZARD"
    ENERGY = "ENERGY"
    CONTROL = "CONTROL"
    ACTIVITY = "ACTIVITY"
    CONTEXT = "CONTEXT"


@dataclass(frozen=True)
class EvidenceItem:
    evidence_type: EvidenceType
    normalized_concept: str
    original_span: str
    negated: bool = False
    verification_status: str | None = None  # e.g., verified, not verified, failed, bypassed, missing, unknown
    temporal_status: str | None = None      # e.g., before, during, after, planned, previously
    confidence: float = 1.0
    match_method: str = "EXACT"             # e.g., EXACT, ALIAS, FUZZY


@dataclass(frozen=True)
class StructuredEvidence:
    items: list[EvidenceItem]
    
    def get_by_type(self, evidence_type: EvidenceType) -> list[EvidenceItem]:
        return [item for item in self.items if item.evidence_type == evidence_type]
    
    def get_primary(self, evidence_type: EvidenceType) -> EvidenceItem | None:
        matches = self.get_by_type(evidence_type)
        return matches[0] if matches else None

    def all_concepts(self, evidence_type: EvidenceType) -> list[str]:
        seen = set()
        result = []
        for item in self.get_by_type(evidence_type):
            if item.normalized_concept not in seen:
                seen.add(item.normalized_concept)
                result.append(item.normalized_concept)
        return result

