# Feedback Memory

## Purpose

Learn stable preference signals from repeated user decisions without training a model or sending feedback to an external service.

## Events

Record a local append-only event for decisions such as:

- `interested`
- `saved`
- `not_interested`
- `dismissed`
- `applied`
- `interview`
- `offer`
- `rejected`

Store a local job identifier, source URL when appropriate, positive tags, negative tags, a short optional note, and timestamp. Do not store raw resume text or credentials.

## Aggregation

`scripts/local_state.py` rebuilds `memory/preferences.json` from feedback events. The aggregate contains decision counts and positive/negative tag frequencies. It is explainable, reversible, and local.

Use memory as a tie-breaker or a suggestion. Explicit current instructions and persistent profile fields always win. Ask before turning a learned tag into a hard profile constraint.

## Controls

- Show memory: display aggregate counts and source file location without exposing the home path in shared output.
- Forget one job: remove its events and rebuild aggregates.
- Forget all: require explicit confirmation, clear events, and rebuild an empty aggregate.
- Export: create a redacted JSON export only when the user asks.
