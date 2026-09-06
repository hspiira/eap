# Services and diagnoses: state of play, 2026-09-06

A review of `apps/api/docs/SERVICES_MODULE.md` and the untracked
`SERVICES_MIGRATION.md` against the code as it stands, and what I recommend
doing next.

Every claim below was checked against the repository or the local database,
not taken from the documents. Where the documents are accurate I say so
briefly; the value here is in the three places they are not.

## 1. The documents are broadly accurate

Verified against the code:

| Claim | Verified |
| --- | --- |
| `services.category` typed as `ServiceCategory` with a CHECK constraint | `service_model.py:37-47`, plus all three schemas at `service_schemas.py:23,42,67` |
| Diagnosis prevalence no longer stubbed | `report_query_runner.py:52-57` groups and suppresses; the `not_implemented` branch at `:90` is for other query types |
| Tenant overlay applied server-side | `diagnoses.py:_build_tree`, `_visible`, `_label`, `_order` |
| 42 alias rows, 29 type-only, all `confirmed` | queried the local database directly |
| Write routes gated on platform admin | `diagnoses.py:239-248` and the gating tests |

So phases 0, 1, 3, 4 and 6 are done as described, and phase 5's *infrastructure*
is done with only the data questions outstanding. The "all six phases
implemented" summary is fair.

## 2. Three things the documents get wrong or omit

### 2.1 Entitlement drawdown is unreachable from the product (highest value)

`SERVICES_MIGRATION.md` marks phase 2 complete and says "both paths now exist".
The backend path does. The product path does not.

`ServiceSessionCompleteRequest.case_id` (`service_session_schemas.py:64`) is the
only trigger for automatic drawdown. Both frontend callers omit it:

- `apps/web/src/routes/service-sessions/$sessionId.tsx:124` sends
  `{ duration, notes }`
- `apps/web/src/components/ServiceSessionFormSheet.tsx:194` sends
  `{ duration, notes }`

A repository-wide search finds no frontend code that sends `case_id` on
completion at all. So `drawdown.consumed` is always false in the running
product, the detail page's "N authorized sessions left" message never appears,
and entitlement drawdown remains as manual as it was before phase 2.

This is not a defect in the phase 2 code, which is sound and tested. It is an
unfinished seam: the feature was built to be *driven* by a caller holding
clinical context, and no such caller was ever wired. The case detail page
(`routes/cases/$caseId.tsx`) does not reference sessions or authorizations at
all, so the natural caller does not exist yet either.

The document treats "automatic resolution from a session alone" as the only
deferred piece, blocked on the members migration retiring `/persons`. That
framing hides a nearer and cheaper option: a user who is *already looking at a
case* can name it. That needs no bridge and no pseudonymity compromise.

### 2.2 The fail-open platform gate is in two files, not one

`SERVICES_MIGRATION.md` records the sidebar gate at `AppSidebar.tsx:100` as a
discovery. The same fail-open logic is duplicated in
`components/common/RequirePlatformAdmin.tsx:34`, whose own docstring states the
behaviour as intended: "When the env var is empty (dev/single-tenant) we skip
the check entirely."

That is the more serious of the two. The sidebar merely shows a link; this one
guards whole routes. The backend does the opposite, failing closed
(`authorization.py:203`). Two copies of the same truth, both able to drift from
the API, and only one of them written down.

Not an access-control hole, because the API is authoritative and returns 403.
It is a correctness and consistency problem, and phase 4 already built the fix
pattern: `GET /diagnoses/capabilities`.

### 2.3 `/persons` is still mounted

`apps/api/app/api/routes/__init__.py:50` still includes `persons_router`, and
`apps/web/src/routes/persons/` still holds four route files. The blocker phase 2
defers to is therefore genuinely unresolved, which the document says, but it is
worth stating that nothing has moved on it and it is owned by the members
migration rather than this one.

## 3. What I recommend, in order

### First: make drawdown reachable (2.1)

Two options, and I would do the first.

**(a) Pass the case from a clinical context.** Add a case picker to the
completion dialog, shown only where clinical scope exists, or add a "complete
session" action to the case detail page which already has `caseId` in hand. This
is the design phase 2 assumed and it needs no new architecture.

**(b) Leave it manual and say so.** If nobody is expected to complete a session
from clinical context yet, then the honest move is to record in the migration
log that phase 2 shipped an API with no product caller, so the next reader does
not assume drawdown is live.

Either way, correct the phase 2 entry. Right now it reads as done.

### Second: settle questions 4 and 5, or time-box them

These are the only things standing between phase 5 and closure, and they are
not engineering work. Four alias rows and the `Others` bucket are rejected at
import until a clinical owner rules. That is the right default and it is pinned
by a test. But "being worked through" has no date on it, and rejection means
those legacy rows cannot be imported at all.

Recommend: ask for a decision with a deadline, and if none arrives, load the
four rows as `confidence = 'inferred'` so they are importable and filterable for
later review, rather than blocking the whole legacy import on five values.

### Third: unify the platform gate (2.2)

Replace both copies with the capabilities endpoint, or at minimum make
`RequirePlatformAdmin` fail closed to match the API. Small, contained, and it
removes a documented inconsistency before someone builds a third copy.

### Fourth, and only if asked: reordering UI

The API supports `sort_order`; the page has no drag affordance. This is the
lowest-value item on the list. It is cosmetic, it is correctly recorded as
deferred, and it should not jump the queue ahead of a feature that does not
work end to end.

## 4. What I would not do

- **Do not add a services-to-diagnoses join.** Both documents reject it with
  evidence and I agree. The session is the correct join.
- **Do not revisit `BenchmarkScope`.** The phase 6 rejection is well argued:
  prevalence is a distribution, `per_tenant_values` returns one number per
  tenant by design.
- **Do not act on the 16 inferred assignments.** The clinical owner confirmed
  them; they are loaded as `confirmed` and the open risk entry is now stale.
