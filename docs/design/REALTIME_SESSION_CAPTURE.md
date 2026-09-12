# Real-time session capture and month-end reconciliation

Decision date: 2026-09-12. Baseline: `8f7afda1`, with concurrent edits present
in the tree. Status: design decisions recorded; phases 1 and 2 starting now,
the rest not implemented.

The module was built to capture work that had already happened, from a
counsellor's spreadsheet. This records how the same module takes a session
that is arranged now and confirmed later, and how the two paths meet without
counting the same session twice.

## The workflow being modelled

The owner's description, in their terms:

1. A member requests support. It arrives by email, phone call, or in person.
   Requests are recorded internally by the team for now; a member-facing
   request surface comes later.
2. A team member schedules it: picks an available counsellor and assigns them.
3. The schedule is tracked in the system.
4. **The session happens outside the system.** Nothing observes it.
5. At month end the counsellor submits who they met.
6. The team cross-checks that submission against what the system expected.
7. Confirmed sessions become completed, and join the delivered figures.

Step 4 is the constraint everything else follows from. The system never
witnesses delivery; it only ever holds an expectation and, later, a
counsellor's account of what happened.

## What exists today

More of this is already built than the brief assumed.

**The booking lifecycle is real, not stubbed.** `POST /service-sessions`
creates with `status=SCHEDULED`
(`app/application/use_cases/service_session_use_cases.py:108`), and
`/complete`, `/cancel`, `/reschedule`, `/no-show` and `/feedback` all exist as
endpoints. `SessionStatus` already carries `Scheduled`, `Rescheduled`,
`Completed`, `Cancelled` and `NoShow`
(`app/domain/enums/session.py:12-17`).

**The booking gate is strong.** `_require_bookable`
(`app/api/routes/service_sessions.py:182`) reads the practitioner under a row
lock, so a preview cannot authorise a booking a concurrent suspension has
already invalidated; it evaluates eligibility *at the scheduled time* rather
than now; it adds supplier approval and affiliation validity for
organisation-delivered work; and it reports every failing reason rather than
the first.

**The list endpoint already filters what a reconciliation queue needs**:
`status`, `scheduled_from`/`scheduled_to`, provider, client and member
(`app/api/routes/service_sessions.py:750-760`).

**There is no availability model of any kind.** Searching the API for
availability, slots, calendars or booking overlap returns only name and email
uniqueness checks. Nothing prevents booking one counsellor twice in the same
hour.

**Scheduled work is deliberately absent from the dashboard.**
`app/api/schemas/dashboard_schemas.py:8` states it: "Scheduled bookings are
not delivery and are deliberately absent from the series; a booking pipeline
would be its own series with its own name." That remains correct for the
delivery series. It also means nothing currently answers "what is booked" or
"what is past its date and still unconfirmed".

**Nothing ages a stale booking.** `MARK_NO_SHOW` exists only as a manual
endpoint. A session booked for last Tuesday that nobody confirmed sits in
`Scheduled` indefinitely, indistinguishable from one booked for next Tuesday.

## The defect this design closes

The month-end import can create a second record for a session already in the
system, and nothing detects it.

The import's idempotency key is `source_id`, taken from the counsellor's
spreadsheet (`app/application/services/historical_import.py:12,182`). A
session booked through the API has no `source_id`, so it is invisible to that
key. There is a near-duplicate guard, `_same_looking_session`
(`app/application/services/session_import_staging.py:753`), which matches on
date, practitioner, client, service and member and holds the row for a person
rather than guessing — but it queries `SessionImportRowModel`
(`app/infrastructure/repositories/provider_network_repository.py:544`), that
is, **rows from previous imports only**. It cannot see a booked session.

The import also writes terminal states directly: only `Completed` and
`NoShow` are accepted
(`app/application/use_cases/historical_session_import.py:175`), so an imported
session never passes through `Scheduled` and never meets the booked record.

The owner's instruction on this was explicit: source is not the differentiator.
The flow is to be designed so the two paths meet, not so the accident of
provenance keeps them apart.

## Decisions

### 1. The request is its own entity, outside the clinical wall, keyed on `member_id`

`Case` already models much of a request: `presenting_problem`,
`referral_source`, `assigned_counsellor_id`, and an
`Intake → Assessment → Active → Closed` lifecycle
(`app/domain/entities/case.py:67-87`, `app/domain/enums/clinical.py:4-12`).
It is nonetheless the wrong home.

Every case route is behind `require_clinical_scope`
(`app/api/routes/cases.py:89,119,135,156`), and a Case identifies the person
by pseudonymous `clinical_subject_id`, never `member_id`. Scheduling staff
would have to be granted clinical scope to do their job, widening who can see
clinical data. Care Callbacks already set the opposite precedent and stays
outside the wall on a real `member_id`.

A request is also not a field on the session. It exists before a counsellor is
chosen, and a session requires `provider_id`. It can be declined or lapse
without producing a session, and one request can produce several.

Consequence: a new non-clinical aggregate, readable by scheduling staff, that
may reference a Case once a clinician opens one without exposing the Case.

### 2. Request channel is a new field, not `Case.referral_source`

`referral_source` records **who referred** (Self, InformalManager,
FormalMandatory, HR, CISMFollowUp, EmployerProactive — the reference table
seeded in `tests/conftest.py:164`). The owner asked for **how the request
arrived**: email, phone call, in person. These are different axes and both are
worth having. A request carries a channel of its own; it does not overload the
referral source.

### 3. The month-end log becomes a reconciliation batch, not an insert path

This is the substantive change. The counsellor's submission stops being "rows
that create sessions" and becomes "rows matched against what the system
expected", with creation as one outcome among several.

This reuses a pattern the repo already has three times — member imports,
practitioner imports and session imports all run batch → rows → per-row
outcome → per-row decision → apply, with nothing written until a person has
reviewed. Reconciliation is a fourth instance of the same shape and should
look like one.

### 4. Reconciliation is a four-way match, and all four outcomes are named

A two-way match (found / not found) loses information the team needs.

| Expected | On the log | Outcome | Resolution |
| --- | --- | --- | --- |
| yes | yes | **Confirm** | complete the scheduled session |
| yes | no | **Unconfirmed** | a person decides: no-show, cancelled, or the counsellor omitted it |
| no | yes | **Unscheduled** | create the session; it was arranged directly |
| yes | yes, differing | **Conflict** | a person confirms whether it is the same session |

The third row is why the insert path cannot simply be switched off. Walk-ins
and directly-arranged sessions are real delivery and must still be recorded.

### 5. A match is held for confirmation, never auto-completed on a fuzzy signal

`_same_looking_session` already takes this position for imports, and says so:
two genuinely distinct sessions can share date, practitioner, client and
service, so it holds the row for a person rather than silently calling it a
duplicate or silently importing it twice. Reconciliation keeps that stance.
Only an exact match completes without review; anything inside a tolerance
window is held.

The schedule makes matching materially easier than it is for a bare import.
The extract carries no time of day, so the import has to guess across the
whole tenant. With a schedule, the question narrows to "which of *this
counsellor's* expected sessions this month is this line", against a small
candidate set.

### 6. "Available" means no conflicting booking here, and is labelled as such

Two things could be meant. Whether the counsellor has no other session booked
in this system at that time is derivable today from existing session rows and
needs no new data. Whether they are genuinely free in their own diary is not
knowable for external, organisation-affiliated practitioners.

Only the first is adopted. The control must say what it checked, because
presenting an unverifiable claim as availability is worse than offering none.

## Company-wide sessions, and where this design does not yet reach

A health talk is delivered to a client, not to a member, and the model already
holds that properly: `SessionAttendance.COMPANY_WIDE`, enforced as an aggregate
invariant rather than only at the route
(`ServiceSessionEntity._require_attendance_matches_member`), with a headcount
required because the room is the only measure of its reach. The web form
carries the same rules.

Phases 1 to 3 handle talks, and this is tested rather than assumed
(`TestCompanyWideSessions`):

- The clash and availability checks are **attendance-blind**, which is right:
  the practitioner is the scarce thing, not the audience. A talk blocks a
  one-to-one at the same hour and the reverse.
- An overdue talk joins the awaiting-confirmation queue like any other booking.
- The staging matcher discriminates correctly, because a talk carries
  `member_id IS NULL` and an individual session does not.

Two places where this design does **not** yet reach, both found by asking the
question rather than by a failing test:

**Decision 1 does not cover a talk.** It keys the request on `member_id`, and a
talk has no member: it is arranged with the client, usually with HR, and no
individual requested it. Phase 4 cannot be built as written. Either the request
carries an attendance of its own and a nullable member, mirroring the session,
or client-level engagements are a separate thing from member requests. Not
decided here; it needs the owner, because it is a question about how the
business books talks rather than about the schema.

**The reconciliation match grain degrades for talks.** Decision 5 matches on
date, practitioner, client, service and member. Strip the member and two talks
for the same client, on the same day, by the same practitioner are
indistinguishable to the matcher, which is a realistic shape for a workplace
programme running a morning and an afternoon session. The held-for-a-person
behaviour keeps that safe rather than silent, but it will fire more often on
talks than on one-to-ones. Headcount may be the discriminator worth adding when
phase 5 is built.

## Decision 7: a follow-up links to the session it came from

A counsellor ends a session saying the person will be back. Nothing in the
system carried that forward: **no session links to any other session**, and
`session_number` is an ordinal copied from the source spreadsheet, never
computed and never enforced. `Engagement` is a Cluster B consultancy project,
not a clinical episode, so it is the wrong container.

The obvious container, a case, is deliberately out of reach. Completing a
session with a `case_id` consumes the authorisation and then discards the link;
`_draw_down` never persists it. That is recorded policy, not an oversight
(`docs/migrations/SERVICES_MIGRATION.md:289`): "There is no bridge, and
building one would defeat the pseudonymity the case aggregate exists to
protect." A session carries an employer-side `member_id` and a case is keyed on
a pseudonymous subject; storing one on the other builds precisely that bridge.

Decision: `follow_up_of_session_id`, a nullable self-reference on
`service_sessions`.

It works **because** both ends are employer-side. Linking a session to a
session creates no bridge to the clinical subject, so a scheduler with no
clinical scope can book and see the chain, while the case stays where it is.
The link is a scheduling fact, not a clinical one: it says this booking was
made off the back of that one, which is exactly what a team member does when a
counsellor says the person is coming back.

Consequences:

- Any session may name the one it follows. A chain is walked one hop at a time
  rather than through a container, which is the cost of not having a case to
  hang it on.
- The link is set when the follow-up is **booked**, not when the previous
  session is completed. The two are separate acts and the second can happen
  weeks later.
- An imported session will not have one. A spreadsheet of month-end work does
  not record which session prompted which, and inventing a chain from date
  order would be a guess presented as a fact.

### Decision 8, reversed: the continuation outcome stays ToBeContinued

`ToBeContinued` is the source spreadsheet's "T" code
(`app/domain/enums/session.py:56`), and it describes the case rather than the
session: the session itself finished perfectly well, and what continues is the
person's care. On that reading it was renamed `FollowUpNeeded`, to name the
action rather than the state.

The owner reversed it: it is the word the team already uses. That outranks the
argument above, and the data agrees with them. 124 of the 369 sessions on the
dev database already carry `ToBeContinued`, so the rename was a data migration
imposed on a vocabulary nobody had asked to change, to buy a precision the
people reading it did not need.

Recorded rather than deleted because the reasoning was sound and the decision
still went the other way. Reopen it only with the team, not from the code.

Consequence: `SessionClinicalStatus` is untouched, and the migration that
carries decision 7 adds the follow-up column alone.

Worth keeping separate in anyone's head: the outcome and the link are different
facts. `ToBeContinued` says the counsellor expects the person back;
`follow_up_of_session_id` says which booking answered that. A session can carry
either without the other, and a test pins that.

## Open questions, not decided here

These change the design and need the owner, or real data, to settle.

**Drawdown under bulk confirmation.** `complete_service_session` optionally
draws a session down against a case's authorisation (`_draw_down`,
`app/api/routes/service_sessions.py:448`). If sessions consume an allowance,
what should happen when two hundred are confirmed in one reconciliation run?
This is the sharpest unknown, and it is an entitlement question, not a
technical one.

**Date tolerance.** The schedule says 3 March, the log says 5 March, same
counsellor and member. One session that slipped, or two sessions? A window
is proposed under decision 5, but its width is a product decision. Too narrow
and every rescheduled-without-updating session becomes a false Unscheduled;
too wide and two real sessions collapse into one.

**Reporting lag.** Delivered figures will under-report the current month and
jump at reconciliation. Whether "Sessions delivered" shows confirmed work
only, or confirmed against expected as two series, is the owner's call. The
range presets added in `8f7afda1` make the jump more visible, not less.

**Assignment signal.** For choosing a counsellor, is slot availability
actually the useful question, or is current load ("who has fewest active cases
this month") what the team really goes on? Not evaluated here.

## Phases

1. **Teach the reconciliation matcher about booked sessions.** Extend
   `_same_looking_session` to look at `service_sessions` as well as
   `session_import_rows`, so a log line for an already-booked session is held
   for review instead of silently inserted. Closes the defect above and is
   independent of everything else. **Starting now.**
2. **An awaiting-confirmation queue.** Scheduled sessions whose
   `scheduled_at` has passed, surfaced so the team can see what is owed before
   the counsellor's log arrives. One query over filters that already exist
   (`service_sessions.py:750-760`). This is the reconciliation screen's
   ancestor, so the work is not thrown away. **Starting now.**
3. ~~Availability and conflict checking at booking time, per decision 6.~~
   **Done** (`93f91a77`). A booking carries no length until it is completed,
   so the span comes from the service's `duration_minutes` with a nominal hour
   as fallback; that assumption lives in `app/domain/services/session_scheduling.py`
   and the API reports which length it used. Create and reschedule refuse a
   clash with 409 `PRACTITIONER_DOUBLE_BOOKED`; `GET
   /service-sessions/availability` answers for the practitioners the caller
   names. Not done: free/busy inside the practitioner search dropdown, which
   needs `EntityPicker` to carry per-row state. The notice under the field
   covers the case that matters, which is the practitioner already chosen.
4. The request entity, per decisions 1 and 2.
5. Reconciliation as a batch, per decisions 3, 4 and 5.
6. A member-facing request surface.
7. Follow-up links, per decision 7. **Done.** The outcome rename in
   decision 8 was reversed by the owner and is not built.

## Standing of this document

Every claim about the current implementation above carries a `file:line` and
was read, not recalled. The decisions are adopted policy under the owner's
delegation, not findings: in particular decisions 1, 2, 4, 5 and 6 are design
judgements that a different team could reasonably settle another way. The open
questions are genuinely open and must not be treated as settled by silence.

Nothing here has been measured against real reconciliation data, because none
has passed through the system yet. The match grain in decision 5 in particular
should be revisited once a real month-end submission has been reconciled.
