# Code Quality Backlog: Evexia API

> Source: review of `apps/api/` (2026-09-04). Scope: backend only.
> Companion to the frontend backlog in `apps/web/docs/code-quality/`, and it
> follows the same ticket format so the two can be worked the same way.

## How to use this backlog

1. Pick a ticket (respect **Depends on**).
2. Create a branch: `fix/<ticket-id>-short-slug` (e.g. `fix/be-a03-sort-allowlist`).
3. Set the ticket **Status** to `🟨 In progress` and add your name.
4. Do the work; meet every **Acceptance criteria** checkbox.
5. Open a PR titled `[BE-XXX] <ticket title>`; link it in the **PR** column.
6. On merge, set Status to `✅ Done`.

**Definition of Done (applies to every ticket)**

- All acceptance criteria checked.
- `pnpm lint:api`, `pnpm typecheck:api` and `pnpm test:api` pass.
- A test that fails before the fix and passes after it, named in the PR.
- `pnpm contracts:check` passes if the change touches a route, schema or docstring.

**Status legend:** ⬜ Todo · 🟨 In progress · ✅ Done · 🚫 Won't do (add reason in ticket)

---

## What this review covered

Read in full: `app/core/`, `app/shared/`, `app/infrastructure/repositories/base.py`,
the auth and Azure SSO routes, the webhook signature path, the document
validators, the pricing engine, and the pagination and privacy-wall machinery.
Sampled: the 34 repositories, the 83 route modules, the 116 domain files.

Three defects were fixed during the review because each was small, provable, and
carried a security or correctness consequence; they are recorded below as `✅ Done`
with the test that pins them. Everything else is left as a ticket rather than
changed, because each needs a decision this review should not make on its own.

**Not verified.** `tests/e2e` could not be run: all 444 tests error at fixture
setup with `asyncpg.exceptions.InvalidAuthorizationSpecificationError: role
"postgres" does not exist`, which is a local environment gap, not a code fault.
CI provisions a `postgres:16` service and does run that suite, so it is gated
there. Every finding below therefore rests on reading the code, on the unit
suite, and on direct probing of the functions in a Python shell. Findings marked
**probed** were reproduced by calling the function; findings marked **read** were
not executed.

---

## Dashboard

### Track A: Correctness & Safety ([A-correctness.md](./A-correctness.md))

| ID | Title | Severity | Effort | Depends on | Status | Owner | PR |
|----|-------|----------|--------|------------|--------|-------|----|
| BE-A01 | SSRF host filter missed six standard address encodings | 🔴 Critical | S | - | ✅ | Claude | - |
| BE-A02 | `verify_signature` raised `TypeError` on a non-ASCII header | 🟠 High | XS | - | ✅ | Claude | - |
| BE-A03 | Paginated queries had no total order | 🟠 High | S | - | ✅ | Claude | - |
| BE-A04 | Login limiter grows without bound on an attacker-controlled key | 🟠 High | S | - | ⬜ | | |
| BE-A05 | Redis limiter extends its own window on every attempt | 🟡 Medium | XS | BE-A04 | ⬜ | | |
| BE-A06 | `sort_by` is an unvalidated column lookup in 32 of 34 repositories | 🟡 Medium | M | - | ⬜ | | |
| BE-A07 | A 500 response bypasses the middleware stack | 🟡 Medium | S | - | ⬜ | | |
| BE-A08 | Outbox dispatcher cannot run on more than one replica | 🟡 Medium | M | - | ⬜ | | |
| BE-A09 | `alembic upgrade --sql` crashes a twelfth of the way through | 🟡 Medium | S | - | ⬜ | | |

### Track B: Test Coverage ([B-coverage.md](./B-coverage.md))

| ID | Title | Severity | Effort | Depends on | Status | Owner | PR |
|----|-------|----------|--------|------------|--------|-------|----|
| BE-B01 | Security-critical helpers had no unit cover | 🟠 High | M | - | ✅ | Claude | - |
| BE-B02 | 13 mappers and 15 repositories sit at 0% unit coverage | 🟠 High | L | - | ⬜ | | |
| BE-B03 | The privacy wall is enforced on 3 routers and tested on 1 | 🟠 High | M | - | ⬜ | | |
| BE-B04 | `tests/e2e` cannot run locally, so nobody runs it | 🟡 Medium | S | - | ⬜ | | |
| BE-B05 | Coverage gate sits at 60% while actual is 64% | 🟢 Low | XS | BE-B02 | ⬜ | | |

### Track C: Structure ([C-structure.md](./C-structure.md))

| ID | Title | Severity | Effort | Depends on | Status | Owner | PR |
|----|-------|----------|--------|------------|--------|-------|----|
| BE-C01 | Three notification handlers are `TODO` with a debug log | 🟡 Medium | M | - | ⬜ | | |
| BE-C02 | `password_hash` is read through `getattr(user, "_password_hash")` | 🟡 Medium | S | - | ⬜ | | |
| BE-C03 | Docstrings are the source of the published API contract | 🟢 Low | XS | - | ⬜ | | |
| BE-C04 | A second unused virtualenv sits at the repo root | 🟢 Low | XS | - | ⬜ | | |

---

## Suggested order

**Wave 1, this week.** BE-A04 and BE-A05 together: both are in one file, both are
brute-force controls, and BE-A04 is reachable from the internet. BE-A07 sits in
the same layer, though its fix is a design choice rather than a five-line
change.

**Wave 2.** BE-A06 needs a decision about where the allowlist lives before it is
worth writing; BE-B03 closes the gap on the product's core privacy promise.
BE-B04 unblocks whoever works on either, because both want e2e cover.

**Wave 3.** BE-B02 is the largest item here and the one that most changes the
review's own confidence: 28 files at 0% coverage is most of the persistence
layer.

**Anytime.** BE-C03 and BE-C04 are independent of everything else.

---

## What is already good

Worth recording, because a backlog reads as though nothing works.

- **The layering is enforced, not aspirational.** `lint-imports` runs in CI with
  three contracts, and all three pass. Domain is pure, application depends only
  on domain, routes do not reach into infrastructure.
- **The privacy wall is a real mechanism.** Access scopes are stamped at mint
  from the database, there is no legacy escape hatch, and tenant ADMIN
  deliberately does not imply clinical access. `tests/unit/core/test_access_scope_wall.py`
  pins that.
- **Clinical fields are encrypted with per-tenant derived keys.** AES-256-GCM
  with an HKDF-derived DEK per tenant, and a version byte for rotation.
- **Cross-tenant reads fail closed as 404 rather than 403**, so existence does
  not leak.
- **The pricing engine is pure domain logic** with no I/O, and it is tested.
- **Timestamps go through one helper.** `utc_now` has 251 call sites and no
  competing `datetime.now()` calls in app code.
