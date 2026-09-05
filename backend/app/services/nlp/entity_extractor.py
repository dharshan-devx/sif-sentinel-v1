import re
from dataclasses import dataclass, field

from app.core.constants import BarrierStatus
from app.knowledge.taxonomy import safety_concepts
from app.services.nlp.evidence_model import EvidenceItem, EvidenceType, StructuredEvidence
from app.services.nlp.preprocessing import PreprocessedText

try:
    from rapidfuzz import fuzz
    HAS_RAPIDFUZZ = True
except ImportError:
    HAS_RAPIDFUZZ = False


@dataclass(frozen=True)
class ExtractedEntities:
    activity: str | None
    hazard: str | None
    barrier: str | None
    barrier_status: BarrierStatus
    barrier_failure: str | None
    confidence: float
    matched_terms: list[str]
    all_activities: list[str] = field(default_factory=list)
    all_hazards: list[str] = field(default_factory=list)
    all_barriers: list[str] = field(default_factory=list)


# Fallback matchers dictionary for backward-compatibility with any module/test inspecting MATCHERS
MATCHERS = {
    "activity": [
        ("Confined Space Work", ("confined space", "entered tank", "vessel entry", "entered vessel", "tank entry")),
        ("Maintenance", ("maintenance", "repair", "service", "servicing")),
        ("Inspection", ("inspection", "inspect")),
        ("Construction", ("construction",)),
        ("Excavation", ("excavat", "trench")),
        ("Lifting", ("lifting", "crane", "hoist", "suspended load")),
        ("Driving", ("driving", "vehicle", "truck", "reversing")),
        ("Hot Work", ("hot work", "welding", "cutting", "grinding")),
        ("Electrical Work", ("electrical", "energized", "cable")),
        ("Material Handling", ("material handling", "manual handling")),
        ("Work at Height", ("work at height", "working at height", "ladder", "scaffold", "roof")),
        ("Pipeline/Line Work", ("pipeline", "line break", "line work")),
        ("Loading/Unloading", ("loading", "unloading")),
        ("Operations", ("operator", "operations")),
    ],
    "hazard": [
        ("Stored Energy", ("energy isolation", "stored energy", "isolation", "lockout", "pressure release")),
        ("Electrical Energy", ("electrical", "energized", "live wire")),
        ("Pressure", ("pressure", "pressurized", "pneumatic", "hydraulic")),
        ("Toxic Atmosphere", ("toxic", "gas testing", "gas test", "flammable atmosphere", "atmospheric testing")),
        ("Oxygen Deficiency", ("oxygen", "confined space")),
        ("Fall Hazard", ("fall", "height", "ladder", "scaffold", "fall hazard")),
        ("Suspended Load", ("suspended load", "crane", "overhead load")),
        ("Vehicle Movement", ("vehicle", "truck", "reversing")),
        ("Fire", ("fire", "welding", "hot work")),
        ("Explosion", ("explosion", "flammable")),
        ("Line of Fire", ("line of fire", "stood below", "pinch point")),
        ("Chemical Exposure", ("chemical", "acid", "spill")),
        ("Moving Machinery", ("moving machinery", "rotating", "unguarded")),
        ("Excavation Collapse", ("trench", "collapse", "excavation")),
        ("Mechanical Energy", ("mechanical", "machine")),
    ],
    "barrier": [
        ("Energy Isolation", ("energy isolation", "isolation", "isolated")),
        ("Lockout Tagout", ("lockout tagout", "lockout", "tagout", "loto")),
        ("Gas Testing", ("gas testing", "gas test", "atmospheric testing", "atmospheric verification", "gas monitoring")),
        ("Atmospheric Monitoring", ("atmospheric monitoring", "continuous monitoring")),
        ("Permit", ("permit", "safe work permit")),
        ("Fall Protection", ("fall protection", "harness", "lanyard", "lifeline")),
        ("Guardrail", ("guardrail", "guard rail", "handrail")),
        ("Barricading", ("barricading", "barricade", "exclusion zone")),
        ("Lifting Plan", ("lifting plan", "lift plan")),
        ("Spotter", ("spotter", "banksman")),
        ("Fire Watch", ("fire watch",)),
        ("PPE", ("ppe", "helmet", "gloves", "safety glasses")),
        ("Vehicle Controls", ("vehicle controls", "seatbelt", "speed limiter")),
        ("Competent Person", ("competent person", "qualified rigger")),
        ("Authorization", ("authorization", "authorisation", "approved")),
        ("Interlock", ("interlock",)),
        ("Procedure", ("procedure", "sop", "jsa")),
    ],
}

NEGATION_TERMS = {
    "not", "no", "never", "absent", "missing", "without", "failed",
    "ineffective", "removed", "unverified", "bypassed", "ignored",
    "lacking", "unavailable", "omitted", "defeated"
}
VERIFICATION_TERMS = {
    "verified", "applied", "checked", "confirmed", "completed",
    "running", "used", "followed", "conducted", "installed",
    "inspected", "obtained", "in place"
}
TEMPORAL_TERMS = {
    "before", "during", "after", "previously", "planned", "expected",
    "later", "earlier", "currently", "prior", "prior to", "following",
    "while", "until"
}

# Conservative fuzzy matching threshold
FUZZY_THRESHOLD = 88


def _tokenize(text: str) -> list[str]:
    return re.findall(r"\b\w+\b", text.lower())


def _fuzzy_match_phrase(target_phrase: str, text_tokens: list[str]) -> bool:
    """Conservatively check if multi-word phrase appears in tokens with minor typo."""
    if not HAS_RAPIDFUZZ:
        return False

    target_words = target_phrase.lower().split()
    n = len(target_words)
    if n == 0 or len(text_tokens) < n:
        return False

    # Only apply fuzzy matching for phrases >= 6 characters and multiple words
    # or single words with length >= 7 to prevent short-word false positives
    if len(target_phrase) < 6:
        return False

    for i in range(len(text_tokens) - n + 1):
        window_str = " ".join(text_tokens[i:i + n])
        if abs(len(window_str) - len(target_phrase)) <= 2:
            score = fuzz.ratio(target_phrase, window_str)
            if score >= FUZZY_THRESHOLD:
                return True

    return False


def _extract_evidence(document: PreprocessedText) -> StructuredEvidence:
    items: list[EvidenceItem] = []
    concepts = safety_concepts()

    activities_map = concepts.get("activities", dict(MATCHERS["activity"]))
    hazards_map = concepts.get("hazards", dict(MATCHERS["hazard"]))
    barriers_map = concepts.get("barriers", dict(MATCHERS["barrier"]))

    for sentence in document.sentences:
        text_lower = sentence.lower()
        tokens = _tokenize(sentence)

        # 1. Activities
        for concept, phrases in activities_map.items() if isinstance(activities_map, dict) else activities_map:
            for phrase in phrases:
                phrase_lower = phrase.lower()
                if phrase_lower in text_lower or _fuzzy_match_phrase(phrase_lower, tokens):
                    method = "EXACT" if phrase_lower in text_lower else "FUZZY"
                    items.append(EvidenceItem(EvidenceType.ACTIVITY, concept, phrase, match_method=method))
                    break

        # 2. Hazards
        for concept, phrases in hazards_map.items() if isinstance(hazards_map, dict) else hazards_map:
            for phrase in phrases:
                phrase_lower = phrase.lower()
                if phrase_lower in text_lower or _fuzzy_match_phrase(phrase_lower, tokens):
                    method = "EXACT" if phrase_lower in text_lower else "FUZZY"
                    items.append(EvidenceItem(EvidenceType.HAZARD, concept, phrase, match_method=method))
                    break

        # 3. Controls (with context, negation, and temporal analysis)
        for concept, phrases in barriers_map.items() if isinstance(barriers_map, dict) else barriers_map:
            for phrase in phrases:
                phrase_lower = phrase.lower()
                matched = phrase_lower in text_lower
                method = "EXACT"
                if not matched and _fuzzy_match_phrase(phrase_lower, tokens):
                    matched = True
                    method = "FUZZY"

                if matched:
                    phrase_tokens = _tokenize(phrase_lower)
                    if not phrase_tokens:
                        continue

                    first_token = phrase_tokens[0]
                    last_token = phrase_tokens[-1]

                    start_idx = tokens.index(first_token) if first_token in tokens else -1
                    end_idx = tokens.index(last_token) if last_token in tokens else -1

                    if start_idx != -1 and end_idx != -1:
                        window_start = max(0, start_idx - 6)
                        window_end = min(len(tokens), end_idx + 7)
                        window = tokens[window_start:window_end]
                    else:
                        window = tokens

                    window_str = " ".join(window)

                    # Negation and verification detection
                    negated = any(term in window for term in NEGATION_TERMS)
                    verified = any(term in window for term in VERIFICATION_TERMS)

                    # Specific safety phrasing checks
                    has_without = "without" in window
                    has_not_used = any(p in window_str for p in ("not used", "did not use", "was not used"))
                    has_bypassed = any(p in window_str for p in ("bypassed", "override", "overridden", "defeated"))
                    has_expired = "expired" in window
                    has_missing = any(p in window for p in ("missing", "absent", "unavailable", "lacking"))

                    # Temporal checks
                    has_before = any(p in window for p in ("before", "prior"))
                    before_idx = -1
                    for b_term in ("before", "prior"):
                        if b_term in tokens:
                            before_idx = tokens.index(b_term)
                            break

                    # Temporal inversion check:
                    # e.g., "Worker entered vessel before gas testing was completed"
                    # Only applies when an action/activity occurred BEFORE the 'before'/'prior' term,
                    # and the control is AFTER the 'before'/'prior' term.
                    # Does NOT apply to "Before maintenance, energy isolation was verified".
                    temporal_inversion = False
                    if before_idx != -1 and start_idx != -1:
                        if before_idx < start_idx and verified:
                            # Check if tokens before 'before' contain action/activity indicators
                            prefix_tokens = tokens[:before_idx]
                            has_preceding_action = any(
                                t in prefix_tokens for t in (
                                    "entered", "started", "began", "commenced", "proceeded",
                                    "worked", "working", "opened", "climbed", "operated",
                                    "performed", "used", "carried", "went", "cut", "welded"
                                )
                            )
                            if has_preceding_action:
                                temporal_inversion = True


                    # Status classification
                    if has_bypassed:
                        status = "bypassed"
                    elif has_expired:
                        status = "expired"
                    elif has_without or has_not_used:
                        status = "not performed"
                    elif has_missing:
                        status = "missing"

                    elif temporal_inversion:
                        status = "not verified"
                        negated = True
                    elif negated and verified:
                        status = "not verified"
                    elif negated:
                        status = "failed"
                    elif verified:
                        status = "verified"
                    elif any(term in window for term in ("planned", "discussed", "scheduled")):
                        status = "unknown"
                    else:
                        status = "unknown"

                    temporal = next((term for term in TEMPORAL_TERMS if term in window), None)
                    items.append(EvidenceItem(
                        evidence_type=EvidenceType.CONTROL,
                        normalized_concept=concept,
                        original_span=phrase,
                        negated=negated,
                        verification_status=status,
                        temporal_status=temporal,
                        match_method=method
                    ))
                    break

    return StructuredEvidence(items)


def extract_entities(document: PreprocessedText) -> ExtractedEntities:
    """
    Extract canonical safety concepts, barrier status, and failure descriptions.
    
    Preserves backward compatibility with existing ExtractedEntities dataclass
    while providing multi-entity tracking.
    """
    structured = _extract_evidence(document)

    all_activities = structured.all_concepts(EvidenceType.ACTIVITY)
    all_hazards = structured.all_concepts(EvidenceType.HAZARD)
    all_barriers = structured.all_concepts(EvidenceType.CONTROL)

    # Primary activity and hazard
    activity_item = structured.get_primary(EvidenceType.ACTIVITY)
    hazard_item = structured.get_primary(EvidenceType.HAZARD)

    act_str = activity_item.normalized_concept if activity_item else None
    haz_str = hazard_item.normalized_concept if hazard_item else None

    # For barrier, if any control failed or is unverified, prioritize it as primary
    controls = structured.get_by_type(EvidenceType.CONTROL)
    primary_barrier_item = None
    for ctrl in controls:
        if ctrl.verification_status in ("failed", "not verified", "not performed", "missing", "bypassed", "expired"):
            primary_barrier_item = ctrl
            break
    if not primary_barrier_item and controls:
        primary_barrier_item = controls[0]

    bar_str = primary_barrier_item.normalized_concept if primary_barrier_item else None

    # Evaluate barrier status and failure description
    if primary_barrier_item:
        if primary_barrier_item.verification_status == "verified":
            status = BarrierStatus.EFFECTIVE
            failure = None
        elif primary_barrier_item.verification_status == "unknown":
            status = BarrierStatus.UNKNOWN
            failure = None
        elif primary_barrier_item.verification_status == "missing":
            status = BarrierStatus.FAILED
            failure = "missing"
        else:
            status = BarrierStatus.FAILED
            failure = primary_barrier_item.verification_status
    else:
        # Fallback for unassociated failure terms globally in document
        failure = next(
            (phrase for phrase in (
                "not verified", "not performed", "missing", "bypassed",
                "failed", "inadequate", "expired", "not used"
            ) if phrase in document.normalized_text),
            None
        )
        status = BarrierStatus.FAILED if failure else BarrierStatus.UNKNOWN

    terms = [item.original_span for item in structured.items] + ([failure] if failure else [])
    confidence = min(1.0, 0.18 * len(terms) + (0.18 if act_str and haz_str else 0.0))

    return ExtractedEntities(
        activity=act_str,
        hazard=haz_str,
        barrier=bar_str,
        barrier_status=status,
        barrier_failure=failure,
        confidence=round(confidence, 3),
        matched_terms=terms,
        all_activities=all_activities,
        all_hazards=all_hazards,
        all_barriers=all_barriers
    )


def get_structured_evidence(document: PreprocessedText) -> StructuredEvidence:
    return _extract_evidence(document)
