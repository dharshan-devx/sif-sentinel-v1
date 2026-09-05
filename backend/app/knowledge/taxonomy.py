import json
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).parent
BARRIER_FAILURES = ("not verified", "not performed", "missing", "bypassed", "failed", "inadequate", "expired", "not available", "not used", "not followed", "ignored", "without")


@lru_cache
def load_json(name: str) -> list | dict:
    with (ROOT / name).open(encoding="utf-8") as source:
        return json.load(source)


def activities() -> list[str]:
    return load_json("activities.json")


def hazards() -> list[str]:
    return load_json("hazards.json")


def barriers() -> list[str]:
    return load_json("barriers.json")


def life_saving_rules() -> list[dict]:
    return load_json("life_saving_rules.json")


def safety_concepts() -> dict:
    return load_json("safety_concepts.json")

