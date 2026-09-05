"""SIF Sentinel ML Data Layer — Dataset loading and validation."""
from __future__ import annotations

import csv
import hashlib
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

# Forbidden metadata columns that must NEVER be passed as model inputs
FORBIDDEN_FEATURE_COLUMNS = frozenset({
    "id",
    "report_type",
    "activity",
    "hazard",
    "barrier",
    "barrier_status",
    "barrier_failure",
    "sif_level",
    "life_saving_rule",
    "source_type",
})

REQUIRED_COLUMNS = ("report_text", "sif_potential")


@dataclass(frozen=True)
class DatasetSummary:
    file_path: str
    file_size_bytes: int
    sha256_hash: str
    total_rows: int
    usable_rows: int
    empty_rows: int
    positive_count: int
    negative_count: int
    positive_ratio: float
    unique_text_count: int
    duplicate_text_groups: int
    duplicate_label_contradictions: int
    columns: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def compute_file_sha256(path: Path | str) -> str:
    path = Path(path)
    h = hashlib.sha256()
    with path.open("rb") as f:
        while chunk := f.read(65536):
            h.update(chunk)
    return h.hexdigest()


def normalize_binary_target(value: Any) -> int:
    """Normalize target representation to 1 (SIF) or 0 (NON_SIF)."""
    if isinstance(value, (bool, int)):
        return int(bool(value))
    val_str = str(value).strip().lower()
    if val_str in {"true", "1", "sif", "yes", "high", "medium"}:
        return 1
    if val_str in {"false", "0", "non_sif", "no", "low"}:
        return 0
    raise ValueError(f"Unrecognized binary target value: {value!r}")


def load_and_validate_dataset(
    path: Path | str,
    text_col: str = "report_text",
    target_col: str = "sif_potential",
) -> tuple[list[dict[str, Any]], DatasetSummary]:
    """
    Load dataset from CSV, strictly validate schema, detect duplicates,
    verify label consistency across duplicate text groups, and return records and summary.
    """
    file_path = Path(path)
    if not file_path.exists():
        raise FileNotFoundError(f"Dataset file not found: {file_path}")

    sha256_hash = compute_file_sha256(file_path)
    file_size = file_path.stat().st_size

    records: list[dict[str, Any]] = []
    with file_path.open("r", encoding="utf-8", errors="replace", newline="") as f:
        reader = csv.DictReader(f)
        if reader.fieldnames is None:
            raise ValueError(f"CSV file at {file_path} is empty or missing headers.")
        
        columns = list(reader.fieldnames)
        for req in (text_col, target_col):
            if req not in columns:
                raise ValueError(
                    f"Required column '{req}' missing from dataset. Found columns: {columns}"
                )

        for row_idx, row in enumerate(reader, start=1):
            records.append(row)

    total_rows = len(records)
    if total_rows == 0:
        raise ValueError(f"Dataset at {file_path} contains 0 rows.")

    usable_records: list[dict[str, Any]] = []
    empty_rows = 0
    positive_count = 0
    negative_count = 0

    # Duplicate grouping by exact stripped text
    text_groups: dict[str, list[int]] = {}

    for idx, row in enumerate(records):
        raw_text = row.get(text_col, "")
        if raw_text is None or not str(raw_text).strip():
            empty_rows += 1
            continue

        text = str(raw_text).strip()
        label_int = normalize_binary_target(row[target_col])
        if label_int == 1:
            positive_count += 1
        else:
            negative_count += 1

        if text not in text_groups:
            text_groups[text] = []
        text_groups[text].append(label_int)

        usable_records.append(row)

    # Check for contradictory labels in identical report_text
    duplicate_groups = 0
    contradictions = 0
    for text, labels in text_groups.items():
        if len(labels) > 1:
            duplicate_groups += 1
            if len(set(labels)) > 1:
                contradictions += 1

    if contradictions > 0:
        raise ValueError(
            f"Dataset contains {contradictions} duplicate text groups with contradictory labels!"
        )

    summary = DatasetSummary(
        file_path=str(file_path),
        file_size_bytes=file_size,
        sha256_hash=sha256_hash,
        total_rows=total_rows,
        usable_rows=len(usable_records),
        empty_rows=empty_rows,
        positive_count=positive_count,
        negative_count=negative_count,
        positive_ratio=round(positive_count / len(usable_records), 4) if usable_records else 0.0,
        unique_text_count=len(text_groups),
        duplicate_text_groups=duplicate_groups,
        duplicate_label_contradictions=contradictions,
        columns=columns,
    )

    return usable_records, summary


def extract_model_inputs(
    records: list[dict[str, Any]],
    text_col: str = "report_text",
    target_col: str = "sif_potential",
    forbidden_cols: frozenset[str] = FORBIDDEN_FEATURE_COLUMNS,
) -> tuple[list[str], list[int]]:
    """
    Extract ONLY report_text and the binary label.
    Explicitly guarantees that no forbidden metadata or outcome fields can ever
    be passed to the vectorizer or classifier.
    """
    texts: list[str] = []
    labels: list[int] = []

    for row in records:
        # Extract text strictly from text_col
        text_val = str(row[text_col]).strip()
        label_val = normalize_binary_target(row[target_col])

        # Assert no forbidden column is used as the text source
        for col in forbidden_cols:
            if col in row and col == text_col:
                raise ValueError(f"Forbidden column '{col}' cannot be used as text_col!")

        texts.append(text_val)
        labels.append(label_val)

    return texts, labels
