# Audit coverage: what is recorded, and what is not

The audit trail is event-driven. `audit_change` reads `entity.events`, so a
mutating method that appends nothing is invisible to `audit_logs` however
healthy the outbox and worker are. This document records which writes are
audited, the decisions behind that line, and what is still open.

## The decision

Clients, contracts and service assignments are audited in full: creation,
every field update, and every lifecycle move. They were chosen first because
they are the records a person edits daily and the ones a dispute is argued
from, and because a client is the aggregate almost everything else hangs off.

The roster follows them. `EligibleMember` emits on creation, on suspend,
reinstate and terminate, and on a roster-details edit. Three of its methods
stay silent deliberately: `link_account` and `unlink_account` are an
association between two aggregates that the members route records as its own
operation, and `record_import` is bookkeeping under an import batch that
already emits, where a roster file of three thousand rows would otherwise
write three thousand audit rows for one operation a person performed once.

Sessions are audited too, under a redaction rule. A delivery record carries
`notes`, `feedback`, `issue_topic` and a diagnosis, so the trail records which
field a person touched and when, and not what it says. See below.

Not decided here, and deliberately left: the remaining 93 silent mutators
across the other aggregates. Auditing everything indiscriminately is not
automatically right, and for special-category health data it creates its own
disclosure surface, which is why `test_audit_coverage.py` refuses to assert it.
That scope is a product call.

## What this pass changed

Baseline moved from 148 silent mutators to 93, which is three separate things
and they should not be read as one number:

| Change | Count | What it was |
| --- | --- | --- |
| Coverage | -14 | `ClientEntity` and `ContractEntity` now emit on create, on every field update, and on archive and restore. Neither has a silent mutator left. |
| Coverage | -9 | `ServiceAssignmentEntity` in full, and `EligibleMember` apart from the three above. |
| Coverage | -12 | `ServiceSessionEntity` in full, under the redaction rule below. |
| Coverage | -8 | `Case`, `ClinicalNote`, `ClinicalSubject` and `OutreachRecord`. Amending a signed note recorded nothing before this. |
| Measurement | -3 | The detector follows a private helper. A method that hands the append to one, `ContractEntity._record_status_change`, read as silent while it emitted. |
| Measurement | -9 | The detector no longer reads `self.x == y` as an assignment, so read predicates like `is_active` were never mutators at all. |

Only the coverage rows are coverage. The other twelve were the ruler being wrong.

## Three faults found on the way

These are why the trail was thinner than the coverage number suggested.

1. **`extract_field_changes` compared attributes starting with `_`.** Every
   domain entity is a plain dataclass with public fields, so both sides of the
   comparison came out empty and an audited update recorded the event with no
   diff under it. The create branch looked for `_id` for the same reason and
   never found one. It now reads the public dataclass fields, skipping
   `events`, `created_at` and `updated_at` as bookkeeping the audit row already
   carries.
2. **No route passed `old_entity`.** The parameter existed through
   `audit_change`, `audit_entity_operation` and `process_entity_events_for_audit`
   and had no caller, so the UPDATE branch had nothing to diff against. The
   client and contract update routes now take a copy before the use case
   mutates the entity in place.
3. **Contract lifecycle emitted nothing.** `renew` and `terminate` emitted;
   activate, sign, archive, restore and every billing field did not. Creating
   five contracts, signing each and archiving four produced zero outbox rows.

## Why the contract emits `ContractStatusChanged`

`map_domain_event_to_audit_action` (`app/shared/utils/audit_helper.py`) buckets
any event whose name contains "activated" as a **CREATE**. A `ContractActivated`
event would therefore file an activation as a creation, putting a second birth
in the trail for a contract that already existed. One event carrying
`from_status` and `to_status` covers activate, archive and restore and maps to
UPDATE, which is what happened.

The mapper itself is left alone. `ClientActivated` and `ProviderActivated`
already flow through it, so changing the rule changes the action recorded for
existing events, and that is a decision to make explicitly rather than fold
into this. Recorded here as open.

## Evidence

- `tests/unit/domain/test_audit_coverage.py` pins the baseline at 122 and
  asserts neither aggregate has a silent mutator left.
- `tests/integration/test_audit_chain.py` runs HTTP to `audit_logs` against
  real PostgreSQL: a rename reaches `entity_changes` carrying
  `name: Acme Corp -> Acme Holdings`, a creation is filed as CREATE, and a
  contract activation is filed as UPDATE rather than CREATE.

## The roster's own audit path is gone

`members.py` used to enqueue its outbox rows by hand through
`record_member_change`. That path could not carry a field diff, a caller
address or a user agent, and it hardcoded `is_special_category` to true. All
twelve call sites and the bulk importer now go through `audit_change`, and
`member_audit.py` is deleted.

Three things had to be decided to make that safe:

**The event vocabulary is preserved where it existed.** The old path built
event names as `f"{resource_type}{operation}"`, so the trail already contains
`EligibleMemberMerged`, `EligibleMemberMergedIntoMember`, `MemberNextOfKinCreated`
and the rest. The new domain events carry those exact names so a query written
against the old trail still matches. The one deliberate change: suspend,
reinstate and terminate now emit `EligibleMemberStatusChanged` with `from_status`
and `to_status`, rather than three separately named events, which matches how
contracts, sessions and assignments already record a lifecycle move.

**Both the member and their next of kin are redacted.** A next of kin never
consented to being on the system, so `MemberNextOfKin` was in the redaction set
from the start. The member's own row was not, on the reasoning that seeing a
coverage date or member code move is the point of auditing a roster edit.

That was reversed on 2026-09-09, after a review pointed out what the row
actually holds: `national_id`, `passport_number`, `date_of_birth` and contact
details. The audit store is append-only, so a value copied into it survives any
later correction or erasure of the record it came from, and stays readable to
every authenticated user in the tenant. The current values are already visible
on the live member record to the same audience, so this was a retention and
data-minimisation problem rather than a disclosure one, which is why it was
rated low. `EligibleMember` now joins the redaction set: which field moved,
when, and by whom is still recorded, and only the before and after values are
dropped.

Field-level redaction was considered and not built. Keeping coverage dates and
member codes readable while dropping the identifiers would preserve more signal,
but it needs a per-resource field allowlist that nothing else in the audit path
has, and a field added to the member later would default to being retained. The
blunt rule fails closed; a follow-up can refine it if the lost detail is missed.

**The special-category flag is preserved, not re-decided.** Whether a roster
row belongs in the DPO's special-category report is that office's call. The
old path said yes; `SPECIAL_CATEGORY_RESOURCE_TYPES` keeps saying yes. What
changed is that reporting and redaction are now separate: `redacts_content`
follows clinical content, `is_special_category` follows what the DPO reports
on. Flagged for the DPO to confirm rather than quietly narrowed.

## Special-category records are audited without their content

`ServiceSession` is now in `CLINICAL_RESOURCE_TYPES`, and the audit handler
redacts the values on any field change for a special-category resource: the
field name and the fact of the change survive, `old_value` and `new_value`
become `[redacted]`. A field that was empty and stayed empty reads as null
rather than as a redaction, so the trail does not imply content that never
existed.

The reason is the audience. `audit_logs` is read by administrators, and the
DPO report exists precisely because that is a wider group than the care team.
Once `extract_field_changes` started working, an unredacted session edit would
have copied the note text, the presenting issue and the diagnosis into
`entity_changes` for all of them. Who edited which field of which session, and
when, is the auditable fact; the clinical content is in the record itself,
behind the clinical scope wall.

Redaction is per resource, not blanket: a client rename still records
`Acme Corp -> Acme Holdings`, because that is ordinary business data and the
before-and-after is the point of auditing it.

## Route-level gaps (2026-09-10 pass)

A second pass compared every `@router.post/put/patch/delete` handler against
its audit call, rather than entity emissions. The scope question left open
above has since been answered by the product owner: every event that affects
or triggers a data change is to be logged. Against that requirement:

1. **DSAR execution is unaudited.** `request_export` and `request_erasure`
   audit; `execute_export` (`dsar.py:119`), `cancel_erasure` (`dsar.py:171`)
   and `execute_erasure` (`dsar.py:192`) do not. Erasure execution is the
   single most destructive write in the system and leaves no audit row.
2. **`apply_batch` is unaudited.** `session_imports.py:315` writes every
   accepted historical session row and closes the batch with no `audit_change`
   call. Staging and abandoning the same batch are both audited.
3. **Auth writes nothing.** `auth.py` has four mutation endpoints and zero
   audit references: `set_initial_password` (a credential change), `login`
   (writes lockout counters and last-login state, `auth.py:226-244`),
   `refresh_token` and `logout`. `AuditActionType.LOGIN` and `LOGOUT` exist
   and `audit_filter.py:40` lists them as always-log, but nothing in the
   codebase ever emits them. The same holds for `EXPORT` and `IMPORT`.
4. **Provider specialties are one-quarter audited.** Only `retire_specialty`
   audits; `create_specialty` (`provider_specialties.py:74`), `add_link`
   (`:152`) and `remove_link` (`:197`) do not.
5. **Eleven vocabulary route files mutate with no audit at all:**
   `case_referral_sources`, `client_tiers`, `diagnoses` (eight mutations,
   including per-tenant settings and alias overlays), `document_types`,
   `kpi_categories`, `kpi_measurement_units`, `next_of_kin_relationships`,
   `presenting_problems`, `service_categories`, `survey_sources`,
   `utilisation_event_types`. These call repository create/update directly
   with no domain entity and no events, so adding `audit_change` alone would
   log nothing; each needs either events on an entity or a direct audit write.

Judgement, not measurement: items 1 to 3 are ranked first on data
sensitivity. That ordering is an inference from what the endpoints touch,
not a stakeholder decision.

## Still open

- The other 93 silent mutators, pending the scope call above.
- The remaining 93 sit on `UserEntity`, `ServiceEntity`, `PersonEntity`,
  `TenantEntity` and the smaller reference aggregates. None of them holds
  client or clinical data, which is why they are last rather than next.
- `map_domain_event_to_audit_action` treating "activated" as CREATE.
- `apps/web/src/routes/audit.tsx` is a placeholder. The read API exists
  (`/audit/logs`, `/logs/{id}/changes`, `/entity/{type}/{id}/changes`) and
  nothing in the UI calls it.
- The worker is a separate process nobody runs in dev, so a local database
  accumulates outbox rows and no audit rows. Local `evexia_db` held 3,668
  undelivered events and 0 audit rows when this was written.
