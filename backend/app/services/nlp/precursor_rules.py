from dataclasses import dataclass

from app.services.nlp.evidence_model import EvidenceType, StructuredEvidence


@dataclass(frozen=True)
class PrecursorCandidateItem:
    category: str
    activity: str | None
    hazard: str | None
    barrier: str | None
    failure_type: str | None
    evidence_text: str | None


def generate_precursor_candidates(evidence: StructuredEvidence) -> list[PrecursorCandidateItem]:
    candidates = []
    
    primary_activity = evidence.get_primary(EvidenceType.ACTIVITY)
    primary_hazard = evidence.get_primary(EvidenceType.HAZARD)
    primary_energy = evidence.get_primary(EvidenceType.ENERGY)
    
    activity_str = primary_activity.normalized_concept if primary_activity else None
    hazard_str = primary_hazard.normalized_concept if primary_hazard else None
    energy_str = primary_energy.normalized_concept if primary_energy else None
    
    hazard_val = energy_str or hazard_str
    
    controls = evidence.get_by_type(EvidenceType.CONTROL)
    
    for control in controls:
        category = None
        failure = control.verification_status
        
        if failure == "not performed" or failure == "missing":
            category = "CONTROL_MISSING"
        elif failure == "not verified":
            category = "CONTROL_UNVERIFIED"
        elif failure == "failed" or failure == "bypassed":
            if energy_str:
                category = "ENERGY_CONTROL_FAILURE"
            else:
                category = "CONTROL_DEGRADATION"
        
        if category:
            candidates.append(PrecursorCandidateItem(
                category=category,
                activity=activity_str,
                hazard=hazard_val,
                barrier=control.normalized_concept,
                failure_type=failure,
                evidence_text=control.original_span
            ))
            
    if not controls and hazard_val:
        candidates.append(PrecursorCandidateItem(
            category="EXPOSURE",
            activity=activity_str,
            hazard=hazard_val,
            barrier=None,
            failure_type="no control present",
            evidence_text=primary_hazard.original_span if primary_hazard else (primary_energy.original_span if primary_energy else None)
        ))
        
    return candidates
