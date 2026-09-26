# MIRROR — Limitations

This document exists so that nobody — judges, users, or the team — mistakes
MIRROR for something it is not.

## What MIRROR measures

Only interactions inside this application: which options you view, when you
view them, how long you take to decide, whether you open additional
information, whether you reverse a choice, and your final selection.

## What MIRROR does not measure

- Thoughts, intentions, or private mental states
- Personality type, mental health, intelligence, or psychological disorders
- Anything outside this application (no camera, no microphone, no
  biometrics, no browser history, no contacts, no files)

## Confidence calibration requires more data than a hackathon run

MIRROR refuses to display a calibration report until at least **10
resolved predictions** exist. Below that threshold the numbers are
reported but explicitly labeled as early estimates.

At 5–8 observations — the size of a single hackathon demo — the
per-axis confidence is dominated by the sample-support term. That is
why every fresh profile shows LOW confidence on every axis: it is the
honest answer.

## The choice model is deliberately simple

The final-choice predictor is a softmax over seven option attributes
with L2 regularization (`lambda = 0.5`). It does not learn complex
interactions, does not use sequence information, and does not model
non-stationarity. It is chosen because it is:

1. Interpretable — you can read the weight on each attribute.
2. Stable at n = 8 — the strong prior keeps weights near zero unless the
   data pushes them.
3. Fast — microseconds per prediction.

A richer model would be appropriate at n ≥ 100 per user. At n = 8, a
richer model would fit noise.

## Scenario attribute values are hand-authored

The 12 calibration scenarios in `backend/app/simulation/scenarios_core.py`
carry hand-assigned attribute values (risk, time_cost, novelty, …). These
are the design, not the result of measurement. Changing them changes what
MIRROR can learn.

## First-action prediction is a heuristic, not a model

`engine._predict_first_action` uses a stated rule: if the user shows a
strong exploration or novelty signal, predict they will look first at
the most novel option; otherwise predict the first action matches the
final choice. The API tags it as `method: heuristic` in the response.

## The fallback path is not degraded

When the AI provider is unavailable, scenario generation, narration, and
reflection all fall through to deterministic templates. The demo runs
identically. The only visible difference is the top-right pill turning
from **live · deepseek** to **fallback mode**, and the `narrative_source`
field on predictions reading `template` instead of `llm`.

## What we would build next

- Per-user calibrations with 30+ observations so the weights are actually
  fitted rather than shrunk.
- Leave-one-scenario-out cross-validation on the choice model, gated at
  n ≥ 15.
- A proper active-learning acquisition function using expected information
  gain instead of a stated heuristic.
- Persistent user accounts with server-side storage and a real delete
  audit trail.
- Cross-domain scenario generation with domain-specific attribute sets.