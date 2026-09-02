from dataclasses import dataclass

from app.core.constants import BarrierStatus
from app.knowledge.taxonomy import BARRIER_FAILURES
from app.services.nlp.preprocessing import PreprocessedText


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
    "hazard": [("Stored Energy", ("energy isolation", "stored energy", "isolation", "lockout", "pressure release")), ("Electrical Energy", ("electrical", "energized", "live wire")), ("Pressure", ("pressure", "pressurized")), ("Toxic Atmosphere", ("toxic", "gas testing", "gas test")), ("Oxygen Deficiency", ("oxygen", "confined space")), ("Fall Hazard", ("fall", "height", "ladder", "scaffold")), ("Suspended Load", ("suspended load", "crane", "overhead load")), ("Vehicle Movement", ("vehicle", "truck", "reversing")), ("Fire", ("fire", "welding", "hot work")), ("Explosion", ("explosion", "flammable")), ("Line of Fire", ("line of fire", "stood below", "pinch point")), ("Chemical Exposure", ("chemical", "acid", "spill")), ("Moving Machinery", ("moving machinery", "rotating", "unguarded")), ("Excavation Collapse", ("trench", "collapse", "excavation"))],
    "barrier": [("Energy Isolation", ("energy isolation", "isolation", "isolated")), ("Lockout Tagout", ("lockout", "tagout", "loto")), ("Gas Testing", ("gas testing", "gas test")), ("Atmospheric Monitoring", ("atmospheric monitoring", "monitoring")), ("Permit", ("permit",)), ("Fall Protection", ("harness", "fall protection")), ("Guardrail", ("guardrail", "guard rail")), ("Barricading", ("barricade", "exclusion zone")), ("Lifting Plan", ("lifting plan", "lift plan")), ("Spotter", ("spotter", "banksman")), ("Fire Watch", ("fire watch",)), ("PPE", ("ppe", "helmet", "gloves")), ("Vehicle Controls", ("seatbelt", "speed limiter")), ("Competent Person", ("competent person", "qualified rigger")), ("Authorization", ("authorization", "authorisation", "approved"))]
}


def _find(kind: str, text: str) -> tuple[str | None, list[str]]:
    for concept, phrases in MATCHERS[kind]:
        found = [phrase for phrase in phrases if phrase in text]
        if found:
            return concept, found
    return None, []


def extract_entities(document: PreprocessedText) -> ExtractedEntities:
    activity, activity_terms = _find("activity", document.normalized_text)
    hazard, hazard_terms = _find("hazard", document.normalized_text)
    barrier, barrier_terms = _find("barrier", document.normalized_text)
    failure = next((phrase for phrase in BARRIER_FAILURES if phrase in document.normalized_text), None)
    if not failure and "before" in document.normalized_text and "was verified" in document.normalized_text:
        failure = "not verified"
    if failure == "without" and barrier:
        failure = "not performed"
    status = BarrierStatus.FAILED if barrier and failure else BarrierStatus.EFFECTIVE if barrier else BarrierStatus.UNKNOWN
    terms = activity_terms + hazard_terms + barrier_terms + ([failure] if failure else [])
    confidence = min(1.0, 0.18 * len(terms) + (0.18 if activity and hazard else 0.0))
    return ExtractedEntities(activity, hazard, barrier, status, failure, round(confidence, 3), terms)
