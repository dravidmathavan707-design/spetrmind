"""Prediction metrics for RF future activity forecasting."""

from __future__ import annotations


def accuracy_score(y_true, y_pred):
    if len(y_true) != len(y_pred):
        raise ValueError("y_true and y_pred must have the same length")
    if not y_true:
        return 0.0
    correct = sum(int(a == b) for a, b in zip(y_true, y_pred))
    return correct / len(y_true)


def precision_score(y_true, y_pred):
    if not y_true and not y_pred:
        return 0.0
    true_positive = sum(1 for a, b in zip(y_true, y_pred) if a == 1 and b == 1)
    predicted_positive = sum(1 for b in y_pred if b == 1)
    if predicted_positive == 0:
        return 0.0
    return true_positive / predicted_positive


def recall_score(y_true, y_pred):
    actual_positive = sum(1 for a in y_true if a == 1)
    if actual_positive == 0:
        return 0.0
    true_positive = sum(1 for a, b in zip(y_true, y_pred) if a == 1 and b == 1)
    return true_positive / actual_positive


def f1_score(y_true, y_pred):
    p = precision_score(y_true, y_pred)
    r = recall_score(y_true, y_pred)
    if p + r == 0:
        return 0.0
    return 2 * p * r / (p + r)
