"""Softmax choice model.

The same model serves two jobs:
  1. consistency feature:  mean P(chosen) under leave-one-out fitting
  2. final-choice prediction: argmax P(o) for an unseen scenario

Numpy only. No scipy. L2-regularised maximum likelihood with a fixed step
size and momentum, which is more than sufficient for 7 weights.
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from typing import Mapping, Sequence

import numpy as np

from .constants import CHOICE_FEATURE_ORDER, CHOICE_L2_LAMBDA, CHOICE_TAU


@dataclass
class ChoiceDataset:
    """One row per resolved scenario."""
    scenarios: list[np.ndarray]           # each is shape (m, d)
    chosen_indices: list[int]             # index of chosen option within that scenario
    option_labels: list[list[str]]        # labels per option, in the same order


def option_vector(attrs: Mapping[str, float]) -> np.ndarray:
    """Map an option's attributes dict to the model's feature vector."""
    return np.array(
        [
            float(attrs.get("risk", 0.5)),
            1.0 - float(attrs.get("time_cost", 0.5)),
            1.0 - float(attrs.get("money_cost", 0.5)),
            float(attrs.get("novelty", 0.5)),
            float(attrs.get("uncertainty", 0.5)),
            float(attrs.get("info_availability", 0.5)),
            float(attrs.get("reward", 0.5)),
        ],
        dtype=float,
    )


def softmax(u: np.ndarray) -> np.ndarray:
    u = u - np.max(u)
    e = np.exp(u)
    return e / np.sum(e)


def predict_proba(weights: np.ndarray, X: np.ndarray) -> np.ndarray:
    """X: shape (m, d). Returns probabilities of shape (m,)."""
    if X.size == 0:
        return np.array([])
    u = X @ weights
    return softmax(u / CHOICE_TAU)


def _loss_and_grad(
    weights: np.ndarray,
    scenarios: list[np.ndarray],
    chosen: list[int],
    lam: float,
) -> tuple[float, np.ndarray]:
    loss = lam * float(np.dot(weights, weights))
    grad = 2.0 * lam * weights.copy()
    for X, ci in zip(scenarios, chosen):
        p = predict_proba(weights, X)
        loss -= math.log(max(p[ci], 1e-12))
        # d/dw of -log p_ci  =  -(x_ci - E_p[x]) / tau
        exp_x = p @ X  # shape (d,)
        grad += -(X[ci] - exp_x) / CHOICE_TAU
    return loss, grad


def fit(
    dataset: ChoiceDataset,
    *,
    iterations: int = 400,
    lr: float = 0.05,
    lam: float = CHOICE_L2_LAMBDA,
    seed: int = 0,
) -> np.ndarray:
    """Fit softmax weights via gradient descent with momentum.

    Returns a weight vector of length len(CHOICE_FEATURE_ORDER).
    """
    d = len(CHOICE_FEATURE_ORDER)
    w = np.zeros(d, dtype=float)
    if not dataset.scenarios:
        return w

    vel = np.zeros(d, dtype=float)
    momentum = 0.9
    for _ in range(iterations):
        _, g = _loss_and_grad(w, dataset.scenarios, dataset.chosen_indices, lam)
        vel = momentum * vel - lr * g
        w = w + vel
    return w


def consistency_score(weights: np.ndarray, dataset: ChoiceDataset) -> float | None:
    """Mean P(chosen) under leave-one-out refitting.

    Returns None when fewer than 2 scenarios are available (LOO undefined).
    """
    n = len(dataset.scenarios)
    if n < 2:
        return None

    total = 0.0
    for i in range(n):
        loo = ChoiceDataset(
            scenarios=[dataset.scenarios[j] for j in range(n) if j != i],
            chosen_indices=[dataset.chosen_indices[j] for j in range(n) if j != i],
            option_labels=[dataset.option_labels[j] for j in range(n) if j != i],
        )
        w_i = fit(loo, iterations=250, lr=0.05)
        p = predict_proba(w_i, dataset.scenarios[i])
        total += float(p[dataset.chosen_indices[i]])
    return total / n


def predict_options(weights: np.ndarray, options: Sequence[Mapping]) -> list[tuple[str, float]]:
    """Return (label, probability) for each option, in input order."""
    if not options:
        return []
    X = np.stack([option_vector(o.get("attributes") or {}) for o in options])
    p = predict_proba(weights, X)
    return [(str(options[i].get("label") or f"O{i}"), float(p[i])) for i in range(len(options))]


def weights_as_dict(weights: np.ndarray) -> dict[str, float]:
    return {name: float(weights[i]) for i, name in enumerate(CHOICE_FEATURE_ORDER)}


__all__ = [
    "ChoiceDataset",
    "option_vector",
    "softmax",
    "predict_proba",
    "fit",
    "consistency_score",
    "predict_options",
    "weights_as_dict",
]