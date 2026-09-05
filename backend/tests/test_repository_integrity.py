"""Regression checks for committed runtime artifacts that must remain parseable."""

import json
import re
from pathlib import Path

ROOT = Path(__file__).parents[2]
RUNTIME_FILES = (
    ROOT / "backend" / "app" / "ml" / "inference" / "predictor.py",
    ROOT / "artifacts" / "models" / "metadata.json",
)


def test_runtime_files_contain_no_unresolved_git_conflict_markers():
    marker = re.compile(r"^(?:<{7} |={7}$|>{7} )", re.MULTILINE)
    for path in RUNTIME_FILES:
        assert not marker.search(path.read_text(encoding="utf-8")), path


def test_default_model_metadata_is_valid_json():
    metadata_path = ROOT / "artifacts" / "models" / "metadata.json"
    metadata = json.loads(metadata_path.read_text(encoding="utf-8"))
    assert metadata["model_version"] == "sif-tfidf-logreg-v2"
