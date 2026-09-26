# MIRROR — Architecture

## The one-sentence version

A deterministic behavioral engine measures the user, a small fitted
choice model predicts them, a database remembers them, and an LLM only
puts the results into language.

## Layers

| Layer | Owns | Never does |
|---|---|---|
| Frontend | Interaction, event capture, rendering | Compute features, call LLM, decide predictions |
| Event log | Append-only record of what happened | Interpretation |
| Behavior engine | Feature extraction, normalization, choice-model fit | Language generation |
| Prediction engine | Numeric prediction, confidence, counterfactuals | Free-text explanation |
| AI layer | Scenario generation, narration, reflection | Numbers, metrics, timers, scoring |
| Database | Memory, versioning, timeline | Business logic |

The boundary is enforced in code: `app/behavior/` and `app/prediction/`
sit outside `app/ai/` so a metric cannot accidentally be routed through
a language model.

## The core loop as state

Every arrow is a persisted row. The timeline screen is a query, not a
reconstruction.

## Data flow

1. The user interacts with a scenario. Every click, hover, drawer open,
   and slider move is buffered client-side.
2. Events are batched (2s / 10-event threshold) and POSTed. The event
   id is a client UUID, so retries dedupe on the server.
3. Submitting a decision recomputes the user's behavior profile in the
   same request. A new `behavior_profiles` version is written, and a
   `model_updates` row records what changed.
4. A prediction is a separate request. It loads the latest profile,
   runs the softmax over the current scenario's options, computes the
   three-part confidence, and persists the result.
5. Resolving the prediction against the decision runs the compare
   metrics and — if the choice was wrong — calls the reflection path
   (LLM if available, template otherwise). A new profile version is
   written with the resolved error analysis.

## Why the choice model

See `docs/limitations.md`. Short version: softmax with strong L2 is
the simplest model that is still *fitting*, not just averaging, at
n = 8. It is also the only model whose weights we can display on
screen without lying about their meaning.

## Failure modes and their handles

| Failure | Handle |
|---|---|
| LLM timeout | Template fallback; `narrative_source = "template"` |
| LLM returns invalid JSON | `json_repair.py` + 1 retry; then template |
| LLM invents a number | Numeric-consistency check discards the response |
| Database unreachable | `/api/status` reports `db: error`; frontend shows offline pill |
| Concurrent profile writes | `persist_profile` catches `IntegrityError` and returns the winning version |
| Empty user history | Fingerprint returns all-null features; prediction returns 409 |