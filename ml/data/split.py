"""SIF Sentinel ML Data Layer — Group-aware data splitting."""
from __future__ import annotations

import json
import random
import sys
from collections import defaultdict
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

# Ensure backend modules can be imported
BACKEND_DIR = Path(__file__).parents[2] / "backend"
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.services.nlp.preprocessing import preprocess_text
from ml.data.dataset import normalize_binary_target


@dataclass(frozen=True)
class SplitManifest:
    random_seed: int
    train_ratio: float
    val_ratio: float
    test_ratio: float
    total_records: int
    train_records: int
    val_records: int
    test_records: int
    unique_groups: int
    train_groups: int
    val_groups: int
    test_groups: int
    train_positive_count: int
    val_positive_count: int
    test_positive_count: int
    train_positive_ratio: float
    val_positive_ratio: float
    test_positive_ratio: float
    train_ids: list[str]
    val_ids: list[str]
    test_ids: list[str]

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def normalize_text_group_key(text: str) -> str:
    """Use Phase 2 canonical normalization as the grouping key."""
    return preprocess_text(text).normalized_text


def group_aware_split(
    records: list[dict[str, Any]],
    train_ratio: float = 0.70,
    val_ratio: float = 0.15,
    test_ratio: float = 0.15,
    random_seed: int = 2026,
    text_col: str = "report_text",
    target_col: str = "sif_potential",
    id_col: str = "id",
) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]], SplitManifest]:
    """
    Deterministically split records into train, validation, and test partitions
    such that identical/normalized report_text groups are never divided across splits.
    Stratifies groups by label to preserve class balance across partitions.
    """
    if abs((train_ratio + val_ratio + test_ratio) - 1.0) > 1e-6:
        raise ValueError(
            f"Split ratios must sum to 1.0; got {train_ratio} + {val_ratio} + {test_ratio}"
        )

    # 1. Group records by normalized report_text
    group_to_records: dict[str, list[dict[str, Any]]] = defaultdict(list)
    group_to_label: dict[str, int] = {}

    for row in records:
        raw_text = str(row[text_col]).strip()
        group_key = normalize_text_group_key(raw_text)
        label = normalize_binary_target(row[target_col])

        if group_key in group_to_label and group_to_label[group_key] != label:
            raise ValueError(
                f"Contradictory labels in group '{group_key}': "
                f"existing={group_to_label[group_key]} vs new={label}"
            )

        group_to_records[group_key].append(row)
        group_to_label[group_key] = label

    # 2. Separate groups by positive (SIF) vs negative (NON_SIF)
    pos_groups = [g for g, lbl in group_to_label.items() if lbl == 1]
    neg_groups = [g for g, lbl in group_to_label.items() if lbl == 0]

    # Deterministic sort before shuffle to guarantee absolute reproducibility
    pos_groups.sort()
    neg_groups.sort()

    rng = random.Random(random_seed)
    rng.shuffle(pos_groups)
    rng.shuffle(neg_groups)

    # Helper to distribute groups into train/val/test targeting record counts
    train_groups: set[str] = set()
    val_groups: set[str] = set()
    test_groups: set[str] = set()

    for groups in (pos_groups, neg_groups):
        total_recs_in_class = sum(len(group_to_records[g]) for g in groups)
        target_train = int(round(total_recs_in_class * train_ratio))
        target_val = int(round(total_recs_in_class * val_ratio))

        curr_train = 0
        curr_val = 0

        for g in groups:
            recs_cnt = len(group_to_records[g])
            if curr_train + recs_cnt <= target_train or (curr_train < target_train and curr_val >= target_val):
                train_groups.add(g)
                curr_train += recs_cnt
            elif curr_val + recs_cnt <= target_val or curr_val < target_val:
                val_groups.add(g)
                curr_val += recs_cnt
            else:
                test_groups.add(g)

    # 3. Verify zero group overlap
    assert not (train_groups & val_groups), "Leakage detected: train_groups intersect val_groups!"
    assert not (train_groups & test_groups), "Leakage detected: train_groups intersect test_groups!"
    assert not (val_groups & test_groups), "Leakage detected: val_groups intersect test_groups!"

    # 4. Materialize partition records
    train_records: list[dict[str, Any]] = []
    val_records: list[dict[str, Any]] = []
    test_records: list[dict[str, Any]] = []

    for g in sorted(train_groups):
        train_records.extend(group_to_records[g])
    for g in sorted(val_groups):
        val_records.extend(group_to_records[g])
    for g in sorted(test_groups):
        test_records.extend(group_to_records[g])

    # Re-verify normalized text intersection across materialized records
    train_texts = {normalize_text_group_key(r[text_col]) for r in train_records}
    val_texts = {normalize_text_group_key(r[text_col]) for r in val_records}
    test_texts = {normalize_text_group_key(r[text_col]) for r in test_records}

    assert not (train_texts & val_texts), "Normalized text leaked between train and validation!"
    assert not (train_texts & test_texts), "Normalized text leaked between train and test!"
    assert not (val_texts & test_texts), "Normalized text leaked between validation and test!"

    # 5. Extract IDs for reproducible manifest
    train_ids = [str(r.get(id_col, "")) for r in train_records]
    val_ids = [str(r.get(id_col, "")) for r in val_records]
    test_ids = [str(r.get(id_col, "")) for r in test_records]

    train_pos = sum(1 for r in train_records if normalize_binary_target(r[target_col]) == 1)
    val_pos = sum(1 for r in val_records if normalize_binary_target(r[target_col]) == 1)
    test_pos = sum(1 for r in test_records if normalize_binary_target(r[target_col]) == 1)

    manifest = SplitManifest(
        random_seed=random_seed,
        train_ratio=train_ratio,
        val_ratio=val_ratio,
        test_ratio=test_ratio,
        total_records=len(records),
        train_records=len(train_records),
        val_records=len(val_records),
        test_records=len(test_records),
        unique_groups=len(group_to_records),
        train_groups=len(train_groups),
        val_groups=len(val_groups),
        test_groups=len(test_groups),
        train_positive_count=train_pos,
        val_positive_count=val_pos,
        test_positive_count=test_pos,
        train_positive_ratio=round(train_pos / len(train_records), 4) if train_records else 0.0,
        val_positive_ratio=round(val_pos / len(val_records), 4) if val_records else 0.0,
        test_positive_ratio=round(test_pos / len(test_records), 4) if test_records else 0.0,
        train_ids=train_ids,
        val_ids=val_ids,
        test_ids=test_ids,
    )

    return train_records, val_records, test_records, manifest


def persist_split_manifest(manifest: SplitManifest, output_path: Path | str) -> None:
    """Save the split manifest to JSON."""
    out_path = Path(output_path)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with out_path.open("w", encoding="utf-8") as f:
        json.dump(manifest.to_dict(), f, indent=2)
