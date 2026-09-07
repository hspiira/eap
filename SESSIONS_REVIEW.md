# Sessions: documents against implementation

Reviewed 2026-09-07 against `7a9ab41` on `chore/monorepo`. Scope: the service
session aggregate, its API, its list UI, and the historical import path, checked
against `SERVICES_MIGRATION.md`, `PROVIDERS_MIGRATION.md` (session extract and
import acceptance), `MEMBERS_MIGRATION.md`, `MODULES_REPAIR_PLAN.md`, and the
source extract the sessions are captured in today.

Sessions are **not** behind a feature flag (`apps/web/src/lib/featureFlags.ts`),
so this module is in scope under the paused-module rule in
`MODULES_REPAIR_PLAN.md`.

## The source extract

`/Users/piira/Downloads/sessions.csv`, SHA-256
`0e8fa212455ea42bba48574eb46c639ade1238bc9fa7382bfc7eee1951774e44`,
7,470 populated rows, 47 columns, all rows dated within Apr-25 to Sep-25.
Every figure below was computed from that file at that hash.

### Inherited audit claims, now reverified

`PROVIDERS_MIGRATION.md` records counsellor figures and flags them as
"inherited audit claims, not independently reverified". They are reverified
here and all but one hold:

| Claim | Recomputed | Verdict |
| --- | --- | --- |
| 158 raw counsellor spellings | 158 | holds |
| 56 cleaned names | 56 | holds |
| 328 rows with a raw name and no clean counterpart | 328 | holds |
| across 69 distinct raw values | **71** | **correction** |
| 308 rows with no counsellor | 308 | holds |
| no contradictory raw-to-clean mapping | 0 contradictions | holds |
| `SERVICE PROVIDER` empty in populated rows | 0 populated | holds |

The caution in that document still stands: 56 cleaned names do not establish 56
distinct people. Nothing here resolves identity.

## What is already built and sound

Do not rebuild these.

- **The aggregate already models the activity log.** `ServiceSessionEntity`
  carries `session_type`, `category`, `rate_ugx`, `issue_topic`,
  `diagnosis_type_id`, `diagnosis_id`, `approved_by`, `session_number`,
  `partner_name`, `partner_relationship`, `headcount`, `client_type` and
  `clinical_outcome`, and `ServiceSessionResponse` returns all of them. Of the
  47 source columns, roughly a third are spreadsheet working columns (`↳`
  lookups, `(CLEAN)` variants, `DUPLICATE CHECK`) with no business meaning, and
  the rest map to existing fields.
- **The import gates the documents demand exist.** `ImportRowOutcome` covers
  Accepted, Duplicate, Conflicting, MissingPractitioner, UnmappedPractitioner,
  AmbiguousPractitioner, plus UnresolvedMember and UnresolvedService.
  `session_import_rows` is unique on `(tenant_id, replay_key)`, and
  `_replay_key` uses the source record key when there is one and
  `file:{hash}:row:{n}` when there is not, which is exactly the fallback
  `PROVIDERS_MIGRATION.md` prescribes.
- **Historical acceptance is correctly separated from booking eligibility.**
  `HistoricalSessionImport` does not consult the booking gate, performs no
  billing or authorization drawdown, and keeps `Unknown` delivery context when
  the source establishes nothing. That matches the rule in `CLAUDE.md`.

## What is lacking

### S-01 (blocker): 14.9% of source rows have no member, and `member_id` is required

1,113 of 7,470 rows carry no `CLIENT-ID#`. `ServiceSessionEntity.member_id` and
`HistoricalSessionRecord.member_id` are both required, so none of these rows can
be represented, let alone imported.

They are not one problem but two, and they need different answers:

- **544 group or event rows.** `CLIENT TYPE (STAFF/DEP)` is `Group/Event`,
  `GENDER` is literally `Group`, and there is no individual to identify. A
  wellness talk delivered to a room is a real delivered session with no member.
  The model has no way to say that.
- **556 rows marked `Staff`** and 13 marked `Dependant` that should have an ID
  and do not. These are unresolved identities, and the existing
  `UnresolvedMember` outcome is the right destination: quarantine, do not
  invent, per `CLAUDE.md`.

**Decision needed from the product owner before any import**: whether a session
may exist without a member. Recommended: make `member_id` optional on the
aggregate and add a required `client_id`, so a group session is attributed to
the client that commissioned it. That also fixes S-02.

### S-02: a session cannot name its client except through a member

There is no `client_id` on the session. The company is reached only as
member → client. `COMPANY` is one of the primary reporting dimensions in the
source (46 distinct companies; Stanbic 2,086 rows, Absa 1,191), and for the 544
group rows there is no member to reach it through, so those sessions cannot be
attributed to a client at all. Utilisation by client is the core employer
report; it currently depends on a join that 7% of rows cannot make.

### S-03: `Terminated` has no representation in the outcome enum

`STATUS (CLEAN)` takes Ongoing (6,408), Completed (215), Referred (25),
**Terminated (10)** and No Show (1). `SessionClinicalStatus` offers
ToBeContinued, Referred and Completed. Ongoing maps to ToBeContinued and No Show
is a `SessionStatus`, but a terminated engagement has nowhere to go and would be
silently coerced or rejected. Ten rows, but it is a lossy mapping, not a gap in
the data.

### S-04: `ACTIVITY LOG ID` must not be used as the source record key

It looks like a stable key and is not: 7,079 distinct values over 7,465 rows,
with 669 rows colliding across 283 groups. If it is passed as
`source_record_key`, `_replay_key` returns `key:{...}` and 669 legitimate
sessions are marked `Duplicate` and dropped without anyone seeing a rejection.

Independently, 620 rows in 271 groups share `DATE + NAME + CLIENT-ID + COUNSELOR
+ TIME`, so no natural composite key is unique either. **For this file, use the
`file:{hash}:row:{n}` form and do not populate `source_record_key`.** Record
that decision with the import, because a re-exported file will produce a
different hash and require the explicit reconciliation the migration document
already demands.

### S-05: three captured columns hold nothing usable

- `PARTNER RELATIONSHIP`: empty in all 7,470 rows, while `partner_relationship`
  exists on the aggregate.
- `HEADCOUNT`: populated in 28 of 7,470 rows, and in only 28 of the 642
  group/event rows. Group attendance is effectively not captured, so any
  headcount-based utilisation figure would be built on 4% coverage.
- `ISSUE GROUP`: 6,492 of 7,470 are the single value `Other`.

None of these should be presented as a reportable field until collection
changes. `HEADCOUNT` is the one worth fixing at source, since group reach is
otherwise unmeasurable.

### S-06: the controlled vocabularies are not controlled at source

Every categorical column arrives dirty, and the enums are strict:

- `SESSION TYPE`: Physical / physical / PhysicaL, Online / online.
- `CATEGORY`: 50 distinct values for four concepts, including `Individual
  Conselling`, `Individual conselling`, `Group session`.
- `GENDER`: 8 spellings, and `Group` used as a gender for 642 rows, which
  conflates the participant's gender with the session's shape.
- `DIAGNOSIS TYPE`: 63 distinct; `DIAGNOSIS`: 251 distinct; `CLASSIFICATION`: 28.
- `CLIENT FEEDBACK`: 56 distinct free-text values (`Satisfied`, `satisfied`,
  `Satisfactory`, `Content`, `tbc`, `0`, `Didn't show up`).

The import needs an explicit, reviewable normalisation table per column, held in
the repository and applied at staging with an `Unmapped` outcome for anything it
does not recognise. Do not normalise with `.title()` or fuzzy matching: 63
diagnosis types against a controlled clinical list is a decision for a clinician,
not a string function. `CLIENT FEEDBACK` should not be imported as a category at
all; it is free text, and per `PRIV-01` free text must not reach an aggregate.

### S-07: the list endpoint returns identifiers, so the UI fetches per row

`ServiceSessionResponse` carries `service_id`, `member_id` and `provider_id` but
no display names. The list page therefore issues one `membersApi.getById` per
row: a 20-row page costs 20 extra requests. Services and, as of `7a9ab41`,
counsellors are resolved with one lookup call each, but members cannot be,
because `membersApi.list` has no filter by id.

Recommended: add `member_display_label`, `client_id`, `client_name`,
`provider_display_name` and `service_name` to the list response. The members
list already does exactly this with `client_name`.

### S-08: sorting is advertised on columns the server may not support

`sort_by` defaults to `scheduled_at` and is passed through as a free string. The
new columns (counsellor, mode, category, session number, outcome) are not
sortable, so their headers are deliberately plain. Confirm the accepted
`sort_by` values and expose sorting only on those.

## UI

Changed in `7a9ab41`: the list showed a `Scheduled` cell stacking date over time
and a `Location` column that the activity log does not capture. It now has one
value per cell across Date, Time, Member, Client, Counsellor, Intervention,
Mode, Category, Session #, Status and Outcome, all of which the source records
and the response already returns. The empty-value placeholder is one shared dash.

Still open:

- Column names follow the source's language (`Intervention`, `Mode`). Confirm
  these are the words the counselling team uses before they spread further.
- `Client` renders from the member's `client_name`, so it is blank for any
  session whose member has not loaded, and would be blank for group sessions
  once S-01 allows them. S-02 fixes this properly.
- No filters exist for counsellor, mode, category or outcome, which are the
  dimensions an operator would actually slice by.
- The detail page was not reviewed.

## Recommended order

1. **S-01 and S-02 together** — the decision on member-less sessions and the
   client on the session. Everything else in the import depends on it, and it is
   a product decision, not an engineering one.
2. **S-04 and S-06** — the replay key choice and the normalisation tables.
   Both are prerequisites for staging a single row honestly.
3. **S-03** — extend the outcome enum, a small change once 1 is settled.
4. **S-07** — hydrate the list response, which removes the N+1 and unblocks the
   remaining UI work.
5. **S-05 and S-08** — collection changes and sort support, neither urgent.

Nothing here was verified in a browser, and no import was run. The counts are
from the file at the hash above and are reproducible from it.
