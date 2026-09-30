"""Helpers for building temporal train/validation/test splits."""

from __future__ import annotations


def temporal_split(rows, train_fraction=0.6, validation_fraction=0.2):
    """Split rows by time order without shuffling, preserving temporal dependency."""
    if not 0 < train_fraction < 1:
        raise ValueError("train_fraction must be between 0 and 1")
    if not 0 < validation_fraction < 1:
        raise ValueError("validation_fraction must be between 0 and 1")

    total = len(rows)
    if total == 0:
        return {"train": [], "validation": [], "test": []}

    train_end = int(total * train_fraction)
    validation_end = train_end + int(total * validation_fraction)

    return {
        "train": rows[:train_end],
        "validation": rows[train_end:validation_end],
        "test": rows[validation_end:],
    }
