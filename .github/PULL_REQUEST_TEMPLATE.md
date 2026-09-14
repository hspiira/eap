# What changed

<!-- One or two sentences. What a reviewer needs before reading the diff. -->

## Status

State each honestly. A collected test is not a passing gate, and a passing gate
is not a deployment.

- [ ] Implemented
- [ ] Tested — gates below were executed, not merely collected
- [ ] Deployed

## Gates executed

Paste results, not intentions. "Ran locally" without output is not evidence.

| Gate | Result |
| --- | --- |
| API unit + coverage | |
| API integration / E2E | |
| Web unit | |
| Browser tests (Playwright) | |
| Lint / format / types | |
| Contract (OpenAPI ↔ generated) | |

## Shared change

Skip only if this touches one module and nothing it shares.

A change to shared repositories, schema, auth, parser utilities, transaction
helpers or transport reaches **both importers**. Naming one is how a member
regression ships inside a sessions PR.

- Consumers affected:
- Contracts preserved:
- Rollback behaviour:
- Both member and session import verified: <!-- yes/no, with the evidence -->

## Durability

If commit cadence, savepoints, checkpoints, resume or chunk size changed, say so
and update the docstrings describing them. Documentation that lags the
durability contract has already caused one stale description.

## Scope

Structural extraction and behaviour change belong in separate commits.

An acceptance gate that was required at the start stays open until it passes.
It cannot be relabelled out of scope to claim completion.

Unrelated findings: record once in `docs/reviews/`, with evidence and a concrete
follow-up, then continue.
