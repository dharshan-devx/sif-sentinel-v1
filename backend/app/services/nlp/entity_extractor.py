import re
from dataclasses import dataclass

from app.core.constants import BarrierStatus
from app.services.nlp.evidence_model import EvidenceItem, EvidenceType, StructuredEvidence
from app.services.nlp.preprocessing import PreprocessedText


# Backward compatibility for typing in analysis_pipeline until fully migrated
@dataclass(frozen=True)
class ExtractedEntities:
    activity: str | None
    hazard: str | None
    barrier: str | None
    barrier_status: BarrierStatus
    barrier_failure: str | None
    confidence: float
    matched_terms: list[str]


MATCHERS = {
    "activity": [("Confined Space Work", ("confined space", "entered tank", "vessel entry")), ("Maintenance", ("maintenance", "repair", "service")), ("Inspection", ("inspection", "inspect")), ("Construction", ("construction",)), ("Excavation", ("excavat", "trench")), ("Lifting", ("lifting", "crane", "hoist", "suspended load")), ("Driving", ("driving", "vehicle", "truck", "reversing")), ("Hot Work", ("hot work", "welding", "cutting", "grinding")), ("Electrical Work", ("electrical", "energized", "cable")), ("Material Handling", ("material handling", "manual handling")), ("Work at Height", ("work at height", "ladder", "scaffold", "roof")), ("Pipeline/Line Work", ("pipeline", "line break")), ("Loading/Unloading", ("loading", "unloading")), ("Operations", ("operator", "operations"))],
    "hazard": [("Stored Energy", ("energy isolation", "stored energy", "isolation", "lockout", "pressure release")), ("Electrical Energy", ("electrical", "energized", "live wire")), ("Pressure", ("pressure", "pressurized", "pneumatic", "hydraulic")), ("Toxic Atmosphere", ("toxic", "gas testing", "gas test", "flammable atmosphere")), ("Oxygen Deficiency", ("oxygen", "confined space")), ("Fall Hazard", ("fall", "height", "ladder", "scaffold")), ("Suspended Load", ("suspended load", "crane", "overhead load")), ("Vehicle Movement", ("vehicle", "truck", "reversing")), ("Fire", ("fire", "welding", "hot work")), ("Explosion", ("explosion", "flammable")), ("Line of Fire", ("line of fire", "stood below", "pinch point")), ("Chemical Exposure", ("chemical", "acid", "spill")), ("Moving Machinery", ("moving machinery", "rotating", "unguarded")), ("Excavation Collapse", ("trench", "collapse", "excavation")), ("Mechanical Energy", ("mechanical", "machine"))],
    "barrier": [("Energy Isolation", ("energy isolation", "isolation", "isolated")), ("Lockout Tagout", ("lockout", "tagout", "loto")), ("Gas Testing", ("gas testing", "gas test")), ("Atmospheric Monitoring", ("atmospheric monitoring", "monitoring")), ("Permit", ("permit",)), ("Fall Protection", ("harness", "fall protection")), ("Guardrail", ("guardrail", "guard rail")), ("Barricading", ("barricade", "exclusion zone")), ("Lifting Plan", ("lifting plan", "lift plan")), ("Spotter", ("spotter", "banksman")), ("Fire Watch", ("fire watch",)), ("PPE", ("ppe", "helmet", "gloves")), ("Vehicle Controls", ("seatbelt", "speed limiter")), ("Competent Person", ("competent person", "qualified rigger")), ("Authorization", ("authorization", "authorisation", "approved")), ("Interlock", ("interlock",)), ("Procedure", ("procedure",))]
}

NEGATION_TERMS = {"not", "no", "never", "absent", "missing", "without", "failed", "ineffective", "removed"}
VERIFICATION_TERMS = {"verified", "applied", "checked", "confirmed", "completed", "running", "used", "followed"}
TEMPORAL_TERMS = {"before", "during", "after", "previously", "planned", "expected", "later", "earlier", "currently"}


def _tokenize(text: str) -> list[str]:
    return re.findall(r'\b\w+\b', text.lower())


def _extract_evidence(document: PreprocessedText) -> StructuredEvidence:
    items = []
    
    for sentence in document.sentences:
        tokens = _tokenize(sentence)
        text_lower = sentence.lower()
        
        # 1. Activities
        for concept, phrases in MATCHERS["activity"]:
            for phrase in phrases:
                if phrase in text_lower:
                    items.append(EvidenceItem(EvidenceType.ACTIVITY, concept, phrase))
                    
        # 2. Hazards
        for concept, phrases in MATCHERS["hazard"]:
            for phrase in phrases:
                if phrase in text_lower:
                    items.append(EvidenceItem(EvidenceType.HAZARD, concept, phrase))
                    
        # 3. Controls (with context)
        for concept, phrases in MATCHERS["barrier"]:
            for phrase in phrases:
                if phrase in text_lower:
                    # Find context window (up to 4 words before/after)
                    phrase_tokens = _tokenize(phrase)
                    if not phrase_tokens:
                        continue
                        
                    first_token = phrase_tokens[0]
                    last_token = phrase_tokens[-1]
                    
                    start_idx = tokens.index(first_token) if first_token in tokens else -1
                    end_idx = tokens.index(last_token) if last_token in tokens else -1
                    
                    window = []
                    if start_idx != -1 and end_idx != -1:
                        window_start = max(0, start_idx - 5)
                        window_end = min(len(tokens), end_idx + 6)
                        window = tokens[window_start:window_end]
                    else:
                        window = tokens # Fallback
                        
                    negated = any(term in window for term in NEGATION_TERMS)
                    verified = any(term in window for term in VERIFICATION_TERMS)
                    
                    # More advanced temporal/context checking
                    before_idx = window.index("before") if "before" in window else -1
                    
                    if negated and verified:
                        status = "not verified"
                    elif negated:
                        status = "not performed" if "without" in window else "failed"
                    elif before_idx != -1 and 0 < (window.index(first_token) - before_idx) <= 2 and verified:
                        # e.g., "started work before isolation was verified"
                        status = "not verified"
                    elif verified:
                        status = "verified"
                    elif "planned" in window or "discussed" in window:
                        status = "unknown"
                    else:
                        status = "unknown"
                        
                    temporal = next((term for term in TEMPORAL_TERMS if term in window), None)
                    items.append(EvidenceItem(EvidenceType.CONTROL, concept, phrase, negated, status, temporal))
                    
    return StructuredEvidence(items)


def extract_entities(document: PreprocessedText) -> ExtractedEntities:
    """Wrapper to maintain backward compatibility while executing new logic."""
    structured = _extract_evidence(document)
    
    activity = structured.get_primary(EvidenceType.ACTIVITY)
    hazard = structured.get_primary(EvidenceType.HAZARD)
    barrier = structured.get_primary(EvidenceType.CONTROL)
    
    act_str = activity.normalized_concept if activity else None
    haz_str = hazard.normalized_concept if hazard else None
    bar_str = barrier.normalized_concept if barrier else None
    
    # Evaluate barrier status
    if barrier:
        if barrier.verification_status == "verified":
            status = BarrierStatus.EFFECTIVE
            failure = None
        elif barrier.verification_status == "unknown":
            status = BarrierStatus.UNKNOWN
            failure = None
        else:
            status = BarrierStatus.FAILED
            failure = barrier.verification_status
    else:
        # Check for unassociated failure terms globally as fallback
        failure = next((phrase for phrase in ("not verified", "not performed", "missing", "bypassed", "failed", "inadequate", "expired") if phrase in document.normalized_text), None)
        status = BarrierStatus.FAILED if failure else BarrierStatus.UNKNOWN
        
    terms = [item.original_span for item in structured.items] + ([failure] if failure else [])
    confidence = min(1.0, 0.18 * len(terms) + (0.18 if act_str and haz_str else 0.0))
    
    return ExtractedEntities(act_str, haz_str, bar_str, status, failure, round(confidence, 3), terms)

def get_structured_evidence(document: PreprocessedText) -> StructuredEvidence:
    return _extract_evidence(document)
