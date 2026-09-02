from dataclasses import dataclass


def normalize_component(value: str | None) -> str:
    return " ".join((value or "unknown").strip().casefold().split())


def display_component(value: str) -> str:
    return " ".join(word.capitalize() for word in value.split())


@dataclass(frozen=True)
class PatternKey:
    activity: str
    hazard: str
    barrier: str
    failure_type: str

    @property
    def key(self) -> str:
        return "|".join((self.activity, self.hazard, self.barrier, self.failure_type))


def build_pattern_key(activity: str | None, hazard: str | None, barrier: str | None, failure_type: str | None) -> PatternKey:
    return PatternKey(*(normalize_component(value) for value in (activity, hazard, barrier, failure_type)))
