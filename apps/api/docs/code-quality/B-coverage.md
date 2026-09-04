# Track B: Test Coverage

Back to [README](./README.md).

Unit coverage is 64.06% over 17,029 statements, against a gate of 60%. The
headline number is healthy; the distribution is not. Coverage is concentrated in
`app/domain/` and thin across the layer that talks to the database.

---

## BE-B01: Security-critical helpers had no unit cover

**Severity:** 🟠 High · **Effort:** M · **Status:** ✅ Done · **Owner:** Claude · **PR:** -

**Problem.** Four modules whose whole purpose is to refuse hostile input had
little or no unit cover, which is how BE-A01 and BE-A02 survived.

| Module | Before | After |
|--------|-------:|------:|
| `app/shared/utils/document_validation.py` | 20% | 89% |
| `app/shared/utils/password_generator.py` | 21% | 100% |
| `app/shared/middleware/security_headers.py` | 23% | 100% |
| `app/core/login_rate_limit.py` | 25% | 66% |
| `app/core/webhook_signature.py` | 100% | 100% |
| `app/infrastructure/repositories/base.py` | 24% | 60% |

**Fix applied.** 113 tests across five files:

- `tests/unit/shared/test_document_validation.py` (37) covers path traversal,
  absolute and drive-letter paths, scheme rejection, and every numeric encoding
  of a loopback or private address from BE-A01.
- `tests/unit/core/test_login_rate_limit.py` (20) covers the window, the 429
  and its `Retry-After`, per-IP isolation, header precedence, and backend
  selection. It documents the current header trust, which BE-A04 will change.
- `tests/unit/infrastructure/test_base_repository_ordering.py` (15) covers the
  ordering fix and asserts `_count_all` filters identically to `_query_all`.
- `tests/unit/shared/test_security_headers.py` (14) covers each header, both
  HSTS states, both CSP states, and headers on error responses.
- `tests/unit/shared/test_password_generator.py` (23) covers length bounds and
  asserts the character-class guarantee holds over 200 draws rather than one.
- `tests/unit/core/test_webhook_signature.py` gained 8 cases for the non-ASCII
  header crash.

Suite went from 641 to 754 passing. Total coverage 63% to 64%.

**Acceptance criteria**

- [x] Every documented rejection path has a negative test.
- [x] The character-class guarantee is asserted over many draws.
- [x] Ordering and count-matching are pinned at the SQL level.
- [x] `pnpm test:api` passes with the gate.

---

## BE-B02: 13 mappers and 15 repositories sit at 0% unit coverage

**Severity:** 🟠 High · **Effort:** L · **Status:** ⬜ Todo

**Problem.** 28 files in `app/infrastructure/` have no unit coverage at all.
Every mapper below is the only thing standing between a database row and a
domain entity, and a field dropped in a mapper is silent.

At 0%, mappers: `benchmark_consent`, `care_callback`, `case`, `clinical_note`,
`critical_incident`, `dsar`, `eap_programme`, `eligible_member`, `engagement`,
`non_compete_clause`, `report`, `survey`, `utilisation_event`.

At 0%, repositories: `benchmark_consent`, `care_callback`, `case`,
`clinical_note`, `critical_incident`, `diagnosis`, `dsar`, `eap_programme`,
`eligible_member`, `engagement`, `non_compete_clause`, `outbox`, `report`,
`survey`, `utilisation_event`.

Also at 0%: `app/infrastructure/services/dsar_service.py`,
`report_query_runner.py`, `benchmark_collector.py`, and
`app/application/services/outbox_consumers.py`.

Note what is on that list. `dsar` is subject-access and erasure, which is a
regulatory obligation. `clinical_note` and `case` are the encrypted clinical
path. `benchmark_consent` gates cross-tenant aggregation. These are the highest
consequence files in the codebase and none of them has a unit test.

Some are exercised indirectly through `tests/e2e`, which is why this is not
catastrophic. But that suite does not run locally (BE-B04), so in practice
nobody sees these paths until CI.

**Recommended fix.** Mappers first, because they are pure functions and need no
database: a round-trip test per mapper (entity to model to entity, asserting
every field survives) is cheap and catches the dropped-field class of bug. Then
repositories, using the `_CapturingSession` pattern from
`tests/unit/infrastructure/test_base_repository_ordering.py` to assert the SQL
each query builds without needing Postgres.

Prioritise by consequence, not by file size: `dsar`, `clinical_note`, `case`,
`benchmark_consent` before `utilisation_event`.

**Acceptance criteria**

- [ ] Every mapper has a round-trip test asserting no field is dropped.
- [ ] Encrypted fields are asserted to round-trip through encrypt and decrypt.
- [ ] Each repository's filter and count paths are asserted to agree.
- [ ] No file in `app/infrastructure/mappers/` remains at 0%.

---

## BE-B03: The privacy wall is enforced on 3 routers and tested on 1

**Severity:** 🟠 High · **Effort:** M · **Status:** ⬜ Todo

**Problem.** `require_clinical_scope` guards three routers: `cases.py`,
`clinical_notes.py` and `eap_programmes.py`. The end-to-end wall test,
`tests/e2e/test_clinical_scope_wall.py`, exercises `/cases` and `/auth/me`
only. So two of the three guarded routers have no HTTP-level test that an
employer-side user is refused.

`tests/unit/core/test_access_scope_wall.py` does cover the scope mechanism
itself, and that is the part most likely to regress. What is missing is the
wiring assertion: that every route which should carry the guard actually carries
it. A route added to `clinical_notes.py` without the dependency would pass every
test in the suite today.

**Worth confirming, not a finding.** `eligible_members.py` uses
`get_current_user` rather than the clinical guard, which its docstring says is
deliberate: it is the employer-side roster, and the entity docstring confirms
clinical entities never reference it. One endpoint,
`enrol_eligible_member` at line 83, does inject `ClinicalSubjectRepository` and
`EligibleMemberClinicalLinkRepository`, because enrolling a member creates the
pseudonymous subject as a side effect. It returns only the employer-side
response, so it writes into clinical space without reading it back. That reads
as correct by design, but it is the one place where the two sides meet in a
single handler, and it deserves an explicit test saying so.

`care_callbacks.py`, `critical_incidents.py` and `diagnoses.py` carry no
clinical guard either. Whether that is right is a product question this review
cannot settle: the frontend's own note in `src/api/endpoints/care-callbacks.ts`
says care callbacks are deliberately not behind the wall.

**Recommended fix.** A test that enumerates the route table and asserts the
guard is present on every route under the clinical routers, in the style of the
existing `tests/unit/api/test_fixture_endpoints_have_no_filters.py`, which
already reads the published contract to assert a property across many routes.
That converts the wall from a convention into something CI checks. Then decide,
and write down, which side of the wall care callbacks, critical incidents and
diagnoses belong on.

**Acceptance criteria**

- [ ] A test asserts every route in the clinical routers has the scope guard.
- [ ] `clinical_notes` and `eap_programmes` have HTTP-level refusal tests.
- [ ] The intended side of the wall is documented for the three unguarded
      routers.
- [ ] `enrol_eligible_member` has a test asserting the response carries no
      clinical field.

---

## BE-B04: `tests/e2e` cannot run locally, so nobody runs it

**Severity:** 🟡 Medium · **Effort:** S · **Status:** ⬜ Todo

**Problem.** `uv run pytest tests/e2e` produces 6 passed and 444 errors. Every
error is the same:

```
asyncpg.exceptions.InvalidAuthorizationSpecificationError:
role "postgres" does not exist
```

`.env.test` points at `postgresql+asyncpg://postgres:postgres@localhost:5432/eap_test`.
CI provisions a `postgres:16` service with those credentials, so the suite runs
there. Locally, nothing creates that role: `apps/api/docker-compose.yml` defines
a `db` service with user `evexia`, not `postgres`, and `README.md` suggests a
database named `evexia_db`. Three different sets of local database facts.

`pnpm test:api` only runs `tests/unit`, so the e2e suite is invisible in normal
work and only reachable in CI. That is the practical reason this review could
not verify any route-level behaviour.

**Recommended fix.** One command that stands up a database matching `.env.test`.
Either add a `postgres`-role service to the compose file and a
`pnpm test:api:e2e` script that depends on it, or change `.env.test` to match
the compose file and update the CI service to agree. The important part is that
the three sources of local database facts become one.

**Acceptance criteria**

- [ ] A documented command runs the e2e suite locally from a clean checkout.
- [ ] `.env.test`, `docker-compose.yml` and `README.md` agree on credentials
      and database name.
- [ ] `pnpm verify` either includes the e2e suite or says why it does not.

---

## BE-B05: Coverage gate sits at 60% while actual is 64%

**Severity:** 🟢 Low · **Effort:** XS · **Status:** ⬜ Todo · **Depends on:** BE-B02

**Problem.** `--cov-fail-under=60` in `package.json` and in CI, against an actual
64.06%. Four points of headroom means coverage can fall by four points without
CI noticing.

**Recommended fix.** Raise the gate to just under current, so it ratchets rather
than sags. Do it after BE-B02 rather than now, so the number moves once.

**Acceptance criteria**

- [ ] Gate is within two points of actual coverage.
- [ ] The gate is raised in `package.json` and `.github/workflows/ci.yml`
      together, since both spell it out separately.
