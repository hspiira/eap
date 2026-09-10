# Orphaned enums found during the enum-to-table review

Recorded 2026-09-08, as part of a review of every enum in
`apps/api/app/domain/enums/` for candidates to convert to a reference table
(see the `service_categories`/`document_types`/etc. migrations landed the same
day). Distinct finding: these seven enums are defined but referenced by
nothing else anywhere in the codebase.

## Verification

For each name below, `grep -rln "\bNAME\b" app scripts tests` (excluding the
enums package itself) returns nothing: no entity field, no SQLAlchemy model
column, no Pydantic schema, no route, no test. Confirmed individually, not
inferred from the absence of a dot-attribute usage alone.

- `CrisisWarmHandoff` (`app/domain/enums/crisis.py:41`)
- `CrisisContactOutcome` (`app/domain/enums/crisis.py:50`)
- `CrisisCallerRelation` (`app/domain/enums/crisis.py:33`)
- `MandatoryReportType` (`app/domain/enums/crisis.py:66`)
- `ConsentScope` (`app/domain/enums/privacy.py:39`)
- `ConsentPurpose` (`app/domain/enums/privacy.py:48`)
- `CaringContactChannel` (`app/domain/enums/outreach.py:51`)

## Why this matters

This repo has already done one pass of exactly this cleanup: migration
`c9e3a5b7d1f4` is titled "Drop the tables behind the three unwired feature
verticals." These seven are the same situation for enums rather than tables:
either scaffolding for a feature that was never built, or a feature whose
implementation was later removed without removing the vocabulary that
described it.

## Not touched here

Whether to wire these up (build the missing entity/model/route layer for the
feature they describe) or delete them is a product decision, not a mechanical
one; a few read as safety-relevant (`MandatoryReportType`,
`CrisisWarmHandoff`), so removing them without confirming the feature is
genuinely abandoned risks deleting someone's in-progress design rather than
dead code. Left as-is pending that decision.
