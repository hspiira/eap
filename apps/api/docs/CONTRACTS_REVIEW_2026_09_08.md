# Contracts: what the module represents, and what it should, 2026-09-08

A review of the contracts module across the domain, the API and the two
screens that render it, and what I recommend representing differently.

**Status: Option A is implemented.** `f6b08d91` closes 2.1, 2.3, 2.4, 2.5 and
2.6; `399ac603` closes 2.2; `da8eb76d` closes 2.7. Section 2 is kept as written
because the reasoning is worth more than a list of done items.

Every claim below was checked against the repository or the local database.
The value is in section 2; section 1 exists so section 2 can be trusted.

## 1. What is there

| Piece | Where |
| --- | --- |
| `ContractEntity`, aggregate root | `app/domain/entities/contract.py` |
| Lifecycle: activate, sign, renew, terminate, archive, restore | same file, `:84-190` |
| Five pricing models as a discriminated value object | `app/domain/value_objects/pricing.py` |
| Pricing engine and invoice preview | `app/application/services/pricing_engine.py`, `app/api/routes/pricing.py:115` |
| Utilisation events per contract | `pricing.py:162` |
| Per-term coverage and session spend | `app/api/routes/contracts.py`, `/client/{id}/metrics` |
| List and detail screens | `apps/web/src/routes/contracts/` |
| Contracts within a client | `apps/web/src/components/clients/ClientDetailWidgets.tsx` |

The pricing value object is the best-modelled part of the module. Five models,
each with its own required fields, invalid combinations rejected on
construction. Nothing below is a criticism of it.

## 2. Seven things the representation gets wrong

Ordered by what they cost.

### 2.1 A contract is a term and a relationship at the same time

`renew()` (`contract.py:84`) moves `period.end_date` on the existing row, keeps
`start_date`, overwrites `billing_rate` if a new one is given, and sets the
status to `RENEWED`. A contract renewed three times is therefore one row
spanning the whole relationship, with one rate: the intermediate terms and
every rate before the last are destroyed.

The alternative the codebase actually uses is separate rows. Seeding five years
for Stanbic Bank produced five contracts with nothing linking them
(`scripts/seed_stanbic_contracts.py`), because there is no field to link them
with. So the module offers two ways to represent a multi-year relationship, and
both lose something: one destroys the history, the other keeps it as five
unrelated rows.

This is the root of most of what follows.

### 2.2 Price is represented twice, and the screens show the wrong one

Every contract carries `billing_rate: Money` plus `payment_frequency`
(`contract.py:50`), required and non-null. It may also carry `pricing:
ContractPricing` (`:65`), optional.

`billing_rate` is what both screens display (`$contractId.tsx:239`, and the
Value column I added to the client's contracts table). `pricing` is what the
invoice preview computes from, and it refuses to run without it
(`pricing.py:133`, 400 "Contract has no pricing configuration").

All six contracts in the local database have `pricing_model` null. So the
number a user sees is not the number the system would invoice, and for a
`FEE_FOR_SERVICE` or `FRAMEWORK` contract a single `billing_rate` cannot
express the agreement at all.

### 2.3 Status is stored, and drifts from the dates

`status` is a stored column. Nothing moves a contract to `EXPIRED` when its end
date passes: the only assignment is inside `archive()` (`contract.py:149`),
which a person must call. There is no scheduled job; `ContractStatus.EXPIRED`
appears nowhere else in `app/`.

Meanwhile `is_active()` (`:242`) and `days_remaining()` (`:248`) recompute from
the clock and ignore the stored status. The two disagree the day a term ends,
and both reach the same screen: the detail page shows a green Active badge
(`$contractId.tsx:304`) beside a renewal line reading "Ended" in red
(`lib/contract-term.ts`). Neither is wrong on its own terms. Together they are
incoherent.

### 2.4 Terminating a contract soft-deletes it

`terminate()` sets `deleted_at = now` (`contract.py:146`) as well as the status
and reason. Termination is a commercial fact about a real agreement; a soft
delete is a storage concern about a row. Conflating them means a terminated
contract is filtered out of anything that excludes deleted rows, so the record
of a dispute disappears from the list where somebody would look for it.

### 2.5 A contract has no name

There is no contract number, reference or title on the entity or the table.
The UI identifies a contract by its dates: `contractLabel` in
`apps/web/src/lib/display.ts` renders "1 Oct 2025 to 30 Sep 2026". People refer
to agreements by reference in email, in disputes and on invoices, and two terms
that ran the same dates are indistinguishable in the interface.

### 2.6 Nothing stops two overlapping terms for one client

No uniqueness or exclusion constraint on `(client_id, period)`, and no
application check. The codebase has this pattern already and applies it
elsewhere: `_reject_overlap` for provider affiliations
(`provider_network_use_cases.py:222`) rejects an interval overlapping another
for the same pair.

This is not theoretical. `/contracts/client/{id}/metrics` attributes a session
to a term by date, and its docstring has to warn that overlapping terms both
count the same session.

### 2.7 Delivery is attached to a contract by date, not by reference

`service_sessions` has `client_id` and `scheduled_at` and no `contract_id`.
Every question of the form "what did this term cost" is answered by a date
window. That is an inference, and it is the reason 2.6 matters.

## 3. Three ways to represent it better

### Option A: one row per term, with the chain made explicit

Keep `ContractEntity` as a **term**, and say so.

- `renew()` stops mutating the period. It creates a successor term and returns
  it, carrying `renewed_from_id` back to the predecessor, which becomes
  `EXPIRED` on its own end date.
- Add `renewed_from_id` and a `reference` (human contract number).
- Derive `status` for the lapse case rather than storing it: a term past its
  end date reads as expired without anybody archiving it. Keep the stored
  status for the decisions a person makes (draft, active, terminated).
- `terminate()` stops setting `deleted_at`.
- Add the overlap check for `(client_id, period)` using the affiliation pattern.
- Add `contract_id` to `service_sessions`, defaulting by date for historical
  rows and set explicitly for new ones.

Cost: two migrations and a change to `renew`'s contract with its callers. No
new aggregate, no rewrite of the pricing work.

What it fixes: 2.1 (history survives, chain is navigable), 2.3, 2.4, 2.5, 2.6,
2.7.

### Option B: Agreement and Term as separate aggregates

An `Agreement` holds the relationship: client, reference, owner, the
commercials that outlive a term. A `Term` holds a period, a price and a status,
and belongs to an agreement. Renewal is a new term under the same agreement.

This is the honest model, and it makes the client screen easy: one agreement
with a term history, rather than five rows to be inferred as a sequence.

Cost: a new aggregate, a data migration, and every read path that says
"contract" has to decide which of the two it meant. Worth doing when
amendments arrive (a rate change mid-term is a fact about a term, not a new
term), not before.

### Option C: full temporal model

Terms carry versions; every amendment is a new version with a validity window;
nothing is ever updated in place. Correct for a system that must answer "what
did this agreement say on 3 March", which is a real question in a billing
dispute.

Cost is high and the module cannot yet answer simpler questions. Not now.

### What was built

`renew()` closes its term as `RENEWED` and returns a successor starting the
following day, carrying the rate, the pricing and the auto-renew flag forward
and pointing back through `renewed_from_id`. `POST /contracts/{id}/renew`
returns the successor: the caller asked for the next term and needs its id.
Renewal left `TransitionUseCase`, which loads, mutates and saves one aggregate
and cannot express a second one; a guard test in
`tests/unit/api/test_use_case_call_sites.py` caught that within a minute of
the signature changing.

`effective_status()` derives the lapse; the API serves it as `status` and the
stored value as `recorded_status`. `terminate()` no longer sets `deleted_at`.
Contracts carry a `reference`, and `_reject_overlap` refuses a second live
term over the same days, following the affiliation pattern. Two test fixtures
had been creating overlapping contracts for one client, which is what the rule
is for.

### Recommendation

**Option A, and treat Option B as the direction of travel.** A is a superset of
what is broken today and reaches it without a new aggregate, and every part of
A survives a later move to B: `renewed_from_id` becomes the agreement's
ordering, `reference` moves up to the agreement, the overlap rule becomes an
invariant of the agreement.

2.2 was decided as: pricing is the single representation. `headline_rate()`
reads the standing charge back out of it, `update_billing_rate` writes through
to it, and a migration gives every existing contract the Retainer its flat rate
already implied. Fee-for-service returns no headline figure rather than
inventing one from a rate card, so the response carries `pricing_model` for a
caller to show instead.

The original wording of that decision follows, since it is why it was asked.

The one piece I would not defer is 2.2. Two representations of price is the
defect most likely to produce a wrong number in front of a client. Decide
whether `billing_rate` is a summary of `pricing` (then derive it and stop
storing it) or whether `pricing` is optional detail (then the invoice preview
must fall back to `billing_rate` instead of refusing). It cannot stay both.

## 4. Order I would do it in

1. **Price, one representation** (2.2). Decide, then make the screens and the
   invoice preview read the same source.
2. **Status derivation and the soft-delete split** (2.3, 2.4). Small, and they
   stop the UI contradicting itself.
3. **Renewal as succession** (2.1, 2.5). The migration that matters: a
   `reference`, a `renewed_from_id`, and `renew()` returning a new term.
4. **Overlap rule** (2.6), which only becomes enforceable once 3 exists.
5. **`contract_id` on sessions** (2.7), which makes the metrics endpoint exact
   rather than inferred.

## 5. Found while implementing

The frontend has a third representation of price. `PricingConfig.tsx` is a
model-aware editor whose shapes do not match the backend's: its retainer is
`{monthly_fee, session_cap, overflow_rate}` where the backend's is
`{retainer_amount: Money}`, and its framework is three numbers where the
backend has a deposit and a rate card. It previews against `previewLocally`, a
DEV-only function in `api/endpoints/pricing.ts`.

Nothing reaches it: the only references are its own test and the design
gallery. So the editor is unreachable, disagrees with the server, and
`PATCH /contracts/{id}/pricing` has no caller in the product. Deriving
`billing_rate` on the server was therefore safe, and wiring pricing into the UI
is a separate piece of work with a shape decision of its own.

## 6. What I did not evaluate

- Whether the five pricing models match the commercial reality. I read them as
  written and they are internally consistent.
- Billing itself, beyond one fact I did check: `last_billing_date` and
  `next_billing_date` are set to `None` at creation
  (`contract_use_cases.py:59`), returned in every response
  (`routes/contracts.py:91`), and written by nothing else in `app/`. Two fields
  the API advertises and never populates. Whether billing is meant to live here
  or in the pricing engine is a question I did not answer.
- The contract detail page's History tab, which is an `EmptyState` saying the
  audit feed is not wired up (`$contractId.tsx:253`). That is now stale: as of
  `5d2f06a` a contract emits on create, sign, status change, update, renew and
  terminate, and `/audit/entity/Contract/{id}/changes` will serve it. The tab
  is buildable today.

## 7. Acted on, 2026-09-08 (web)

Two of the findings above are now closed on the frontend, in `a05f8fa`.

**The History tab is built.** It reads `/audit/logs` filtered to the contract,
joined to `/audit/entity/Contract/{id}/changes` for the field names, through the
shared `EntityActivityPanel`. Note it will read as empty in dev until the outbox
is drained: `audit_logs` is empty while `outbox_events` holds 3,668 undelivered
rows, recorded in `DEV_DATA_LOAD.md`.

**Billing shows money.** `GET /contracts/{id}/invoice-preview` had no caller;
the client had a placeholder sending `projected_sessions` to a contract id of
`"unknown"`. The billing tab now calls it properly and renders a line per charge
with quantity, unit and amount, the subtotal, and the engine's notes.

The pricing-shape mismatch in section 5 is untouched and still open. The
what-if projector in `PricingConfig.tsx` keeps its browser-side
`previewLocally`, which is a second pricing implementation modelling a session
cap and overflow rate the backend does not have. That is tolerable only while
the editor stays unreachable; it must not survive the pricing UI being wired.

One consequence of `last_billing_date` and `next_billing_date` never being
populated: the preview's default window falls back to the contract term
(`period.start_date` to `period.end_date`), so it prices the whole term rather
than a billing period. That is the honest default given the data, and it stops
being right the moment those two fields are populated.

Also worth knowing for anyone reading a preview against dev data: all 6
contracts are `Retainer`, and `_retainer` in the pricing engine ignores
utilisation events entirely, so the preview is one fixed line whatever the 59
recorded events say. That is correct for a flat retainer, and it is why the tab
keeps the usage table underneath as the evidence rather than as the charge.
