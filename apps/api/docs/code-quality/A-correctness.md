# Track A: Correctness & Safety

Back to [README](./README.md).

---

## BE-A01: SSRF host filter missed six standard address encodings

**Severity:** 🔴 Critical · **Effort:** S · **Status:** ✅ Done · **Owner:** Claude · **PR:** -

**Problem.** `validate_document_file_url` in `app/shared/utils/document_validation.py`
exists to reject localhost and private addresses in a client-supplied document
URL. It did that with one regex over the textual host, so it caught
`127.0.0.1` and `localhost` but not any other way of writing the same address.

Probed, before the fix. Each of these was accepted:

| Host | Resolves to | Encoding |
|------|-------------|----------|
| `2130706433` | 127.0.0.1 | decimal |
| `0x7f000001` | 127.0.0.1 | hexadecimal |
| `017700000001` | 127.0.0.1 | octal |
| `[::ffff:127.0.0.1]` | 127.0.0.1 | IPv4-mapped IPv6 |
| `[fd00::1]` | unique-local | IPv6 private |
| `[fe80::1]` | link-local | IPv6 link-local |

An HTTP client resolves all six. The regex recognised none. `169.254.169.254`
was blocked in its dotted form, but the decimal form of it was not, so the
cloud metadata endpoint was reachable by writing the address differently.

**Fix applied.** The host is now parsed with `ipaddress` and rejected on
`is_loopback`, `is_private`, `is_link_local`, `is_reserved`, `is_unspecified` or
`is_multicast`, with IPv4-mapped addresses unwrapped first. The original regex
was kept alongside it rather than replaced, because `ipaddress` refuses the
shorthand dotted forms that the regex does catch: `127.1` is a valid host to a
resolver but not a valid argument to `ip_address`. Removing the regex regressed
that case, which the test suite caught.

**Acceptance criteria**

- [x] All six encodings above are rejected.
- [x] `127.1` shorthand stays rejected.
- [x] Public URLs still pass, including a bare public IP (`8.8.8.8`).
- [x] Cover in `tests/unit/shared/test_document_validation.py` (37 tests).

**Residual risk, not fixed here.** This validates the URL at the point of
submission. It is not a guarantee about the request that later fetches it: DNS
for a hostname the validator accepted can resolve to a private address, and a
redirect can move a fetch onto one. Closing that needs the check at fetch time
on the resolved address, in whatever component does the fetching. Worth its own
ticket when a fetcher exists.

---

## BE-A02: `verify_signature` raised `TypeError` on a non-ASCII header

**Severity:** 🟠 High · **Effort:** XS · **Status:** ✅ Done · **Owner:** Claude · **PR:** -

**Problem.** `app/core/webhook_signature.py` verifies the `X-Webhook-Signature`
header on the public survey ingestion endpoint. It compared with
`hmac.compare_digest(expected, received)` on two `str` values.
`compare_digest` refuses `str` operands containing any character above U+007F
and raises `TypeError: comparing strings with non-ASCII characters is not
supported`.

Probed, before the fix:

```python
verify_signature("s", b"body", "sha256=\xff\xfe")
# TypeError: comparing strings with non-ASCII characters is not supported
```

The function's own docstring promises it "never raises so the caller can return
a uniform 401 without leaking which check failed". The route is public and
unauthenticated, so any client could turn a request into a 500 by putting one
non-ASCII byte in that header. That is a self-inflicted error surface rather
than an authentication bypass: the signature never validated, so nothing was
admitted that should not have been.

**Fix applied.** Both sides are encoded to ASCII before comparison, and a header
that cannot be ASCII-encoded returns `False`. Constant-time comparison is
preserved because `compare_digest` on `bytes` is the intended usage.

**Acceptance criteria**

- [x] Non-ASCII headers return `False` rather than raising.
- [x] A valid signature with a non-ASCII character appended is rejected.
- [x] Round trip, `sha256=` prefix, wrong secret and tampered body all unchanged.
- [x] Cover appended to `tests/unit/core/test_webhook_signature.py`.

---

## BE-A03: Paginated queries had no total order

**Severity:** 🟠 High · **Effort:** S · **Status:** ✅ Done · **Owner:** Claude · **PR:** -

**Problem.** `_query_all` in `app/infrastructure/repositories/base.py` is the
shared page query behind 14 repositories. It applied `LIMIT`/`OFFSET` with an
`ORDER BY` only when `sort_by` happened to name a real column, and never added a
tiebreaker.

Two consequences, both read from the generated SQL:

1. The default sort is `created_at`, which is not unique. Rows sharing a
   timestamp had no defined order between them, so a page boundary landing
   inside such a group could show one row on two consecutive pages and skip
   another entirely. Bulk-imported rows share timestamps readily, and
   `scripts/import_historical_sessions.py` exists.
2. An unrecognised `sort_by` failed the `hasattr` check and emitted no
   `ORDER BY` at all. Every page was then an arbitrary slice, and paging through
   a list could show and miss rows freely. `sort_by` is a plain string query
   param with no allowlist (see BE-A06), so a typo reached this path.

**Fix applied.** The id column is now always appended as the final sort key, in
the same direction as the requested sort. An unknown `sort_by` still produces a
total order, on id alone.

`sort_by` never reaches SQL as text in either case: it is a `getattr` lookup
against the model, so an unknown value is dropped rather than interpolated.
That is checked explicitly in the new tests.

**Acceptance criteria**

- [x] Known column produces `ORDER BY <col> <dir>, id <dir>`.
- [x] Unknown column produces `ORDER BY id <dir>`, not an unordered query.
- [x] Direction applies to the tiebreaker too.
- [x] `_count_all` filters identically to `_query_all` (checked for equality
      filters, `None`-valued filters, unknown keys and search).
- [x] Cover in `tests/unit/infrastructure/test_base_repository_ordering.py` (15 tests).

**Note.** Two repositories, `person_repository.py:172` and
`tenant_repository.py:102`, already sorted safely via their own
`ALLOWED_SORT_COLUMNS`. This fix does not change them.

---

## BE-A04: Login limiter grows without bound on an attacker-controlled key

**Severity:** 🟠 High · **Effort:** S · **Status:** ⬜ Todo

**Problem.** `MemoryLoginRateLimitBackend` in `app/core/login_rate_limit.py:43`
keeps attempts in `defaultdict(lambda: deque(maxlen=100))`, keyed by client IP.
Old timestamps are trimmed from a deque when that IP is next checked, but the
dict entry itself is never removed, and an IP that is never seen again is never
revisited.

The key comes from `_get_client_ip` at line 140, which prefers
`X-Forwarded-For`, then `X-Real-IP`, then the peer address. The first two are
request headers. Behind a proxy that appends rather than replaces, or with the
app reachable directly, a client chooses its own key.

Probed:

```python
b = MemoryLoginRateLimitBackend()
for i in range(5000):
    b.record(f"10.0.{i//256}.{i%256}")
len(b._attempts)   # 5000
```

Each bucket also holds up to 100 floats. Distinct header values are distinct
buckets, which is exactly the behaviour that makes the limiter work per client,
and also what makes it unbounded: one request per key is enough to create one,
and nothing evicts it. A client spraying distinct `X-Forwarded-For` values grows
the process's memory until it is killed, and each of those requests is also a
free login attempt because the counter for a fresh key starts at zero.

**Recommended fix.** Two parts, and the second matters more than the first.

1. Evict expired buckets. A periodic sweep, or an LRU with a hard cap on the
   number of tracked keys, so the structure has a ceiling.
2. Stop trusting the header unconditionally. Read the client IP from
   `X-Forwarded-For` only when the immediate peer is a trusted proxy, and take
   the rightmost untrusted hop rather than the leftmost. As written, the
   leftmost value is whatever the client sent, so a rotating header defeats the
   limiter regardless of eviction. This needs a deployment fact (which proxy,
   how many hops) that this review does not have, which is why it is a ticket
   and not a fix.

**Acceptance criteria**

- [ ] Tracked keys have a documented ceiling.
- [ ] Expired buckets are removed without waiting for the same key to return.
- [ ] The trusted-proxy assumption is written down in the module docstring.
- [ ] A test asserts the bucket count does not grow past the cap under a spray
      of distinct header values.

**Existing cover.** `tests/unit/core/test_login_rate_limit.py` pins the current
counting, window and header-precedence behaviour, including the fact that two
distinct forwarded values are counted separately. That test documents today's
behaviour and will need updating with the fix.

---

## BE-A05: Redis limiter extends its own window on every attempt

**Severity:** 🟡 Medium · **Effort:** XS · **Status:** ⬜ Todo · **Depends on:** BE-A04

**Problem.** The Redis backend's `record` at `app/core/login_rate_limit.py:104`
runs `INCR` then `EXPIRE key window_sec` on every attempt, so the TTL is pushed
forward each time. The counter is a fixed window that keeps being extended, not
the sliding 15-minute window the memory backend implements.

A client attempting once every 14 minutes accumulates count indefinitely and
stays locked out well past the documented 15 minutes. The two backends therefore
disagree about the same configuration, and only one matches the docstring.

Read, not probed: exercising it needs a Redis instance, which this review did
not have. The divergence is visible in the code.

**Recommended fix.** Set the expiry only when the key is created, or model the
window the way the memory backend does with a sorted set of timestamps. The
first is a one-line change (`SET key 1 EX window NX` then `INCR`, or check the
`INCR` return value); the second makes the two backends genuinely equivalent.

Both `check` and `record` are also separate round trips, so two concurrent
requests can both pass `check` before either records. A Lua script or a
`WATCH`/`MULTI` would close that. It matters less than it looks: the limit is 5
and the race widens it by the number of concurrent requests, not indefinitely.

**Acceptance criteria**

- [ ] The window does not extend on subsequent attempts.
- [ ] Memory and Redis backends produce the same verdict for the same attempt
      sequence, asserted by a shared test parametrised over both.
- [ ] Whether check-and-record needs to be atomic is decided and written down.

---

## BE-A06: `sort_by` is an unvalidated column lookup in 32 of 34 repositories

**Severity:** 🟡 Medium · **Effort:** M · **Status:** ⬜ Todo

**Problem.** `sort_by` arrives as `Query("created_at")` on every list route and
is passed to `_query_all`, which resolves it with `hasattr`/`getattr` against
the model. Two repositories validate it against an allowlist first
(`person_repository.py:172`, `tenant_repository.py:102`); the other 32 do not.

This is not SQL injection. The value is never interpolated into SQL; it is an
attribute lookup, and an unknown name is dropped. BE-A03 removed the
worst consequence by keeping the query ordered regardless. What remains:

- Any mapped column is sortable, including ones not meant to be part of the
  public contract, which turns the sort parameter into an oracle for ordering
  rows by a field the API never returns.
- A typo silently sorts by id instead of erroring, so a client cannot tell a
  supported sort from an unsupported one.
- The two repositories that do validate raise on a bad value while the other 32
  ignore it, so the same mistake behaves differently per endpoint.

**Recommended fix.** Decide where the allowlist belongs before writing it. Two
options, and this review does not have a basis to pick:

- **Per repository**, extending the existing `ALLOWED_SORT_COLUMNS` pattern to
  the other 32. Consistent with what is there, but 32 copies of a set literal.
- **At the route**, as an enum or `Literal` on the query param, so the allowed
  values appear in the OpenAPI contract and the frontend can render exactly the
  sorts that exist. More work, and it moves a persistence concern into the API
  layer, which the import contracts may object to.

Either way an unsupported value should produce one consistent response, and 422
fits better than silently sorting by something else.

**Acceptance criteria**

- [ ] Every list endpoint validates `sort_by` the same way.
- [ ] An unsupported value produces the same status everywhere.
- [ ] Supported sorts are discoverable from the published contract.
- [ ] The two existing allowlists are folded into whatever is chosen, not left
      as a third pattern.

---

## BE-A07: A 500 response bypasses the middleware stack

**Severity:** 🟡 Medium · **Effort:** S · **Status:** ⬜ Todo

**Problem.** The catch-all handler exists and works. `app/core/exception_handlers.py:154`
registers `@app.exception_handler(Exception)` and returns the standard envelope
with a `request_id` in the body. What does not work is everything wrapped around
it.

FastAPI installs an `Exception` handler as `ServerErrorMiddleware`'s handler, and
`ServerErrorMiddleware` is the outermost layer of the stack. Anything added with
`add_middleware` sits inside it, so a response produced on that path never
travels back out through those layers.

Probed, with both middlewares mounted:

| Response | Envelope | `X-Frame-Options` | `X-Content-Type-Options` | `X-Request-ID` |
|----------|----------|-------------------|--------------------------|----------------|
| 200 `/ok` | n/a | `DENY` | `nosniff` | present |
| 400 `ValueError` | yes | `DENY` | `nosniff` | present |
| 500 unhandled | yes | absent | absent | absent |

So an unhandled exception is the one response class that ships without
`X-Frame-Options`, `X-Content-Type-Options` and `Referrer-Policy`. The 400 path
keeps them, because a handler registered for a specific exception type runs
inside `ExceptionMiddleware`, which is inside the stack.

Correlation is only half lost, which is worth stating precisely: the `request_id`
is still in the response body, because the handler reads it from the contextvar
directly. It is the `X-Request-ID` header that is missing, so a client
correlating by header cannot, while a log-to-body comparison still works.

**Recommended fix.** Two options, and the choice is a design decision rather
than a mechanical fix:

- Set the headers inside the handler. Small and local, but now the header list
  lives in two places and can drift from `SecurityHeadersMiddleware`.
- Mount `SecurityHeadersMiddleware` outside `ServerErrorMiddleware`, by wrapping
  the ASGI app rather than using `add_middleware`. Keeps one source for the
  header list, at the cost of a less obvious mount.

**Acceptance criteria**

- [ ] Security headers are present on a 500.
- [ ] `X-Request-ID` is present on a 500.
- [ ] The header list is not duplicated, or the duplication is deliberate and
      commented.
- [ ] `tests/unit/shared/test_security_headers.py::TestFiveHundredBypassesTheStack`
      is inverted to assert presence once fixed.

**Corrected.** An earlier version of this entry claimed there was no catch-all
handler and that a 500 returned a bare response. Both were wrong; the handler is
at line 154 and the envelope is correct. Caught by eap-85. The finding that
survives is the bypass above, which is what justified the security-headers test
in the first place.

---

## BE-A11: `alembic_version` holds three rows, so `upgrade head` fails

**Severity:** 🔴 Critical · **Effort:** XS · **Status:** ⬜ Todo

**Problem.** `alembic upgrade head` fails against the shared database:

```
Requested revision a5b7c9d1e3f4 overlaps with other requested revisions
e1a5b8c3d7f2, e1a5c7b9d3f2
```

`alembic_version` holds three rows where a clean history would hold one:

```
['a5b7c9d1e3f4', 'e1a5b8c3d7f2', 'e1a5c7b9d3f2']
```

`a5b7c9d1e3f4` was applied while it still declared the single parent
`z4u7v9w1q3s6`, so alembic inserted it as a third independent head beside the
other two. The file was then edited to declare all three as parents, making it a
merge revision. Alembic now sees a merge and two of its own parents all recorded
as current, and refuses. When a merge is applied normally, alembic deletes the
parent rows because the merge subsumes them; that never happened here because
the revision was not a merge when it ran.

**The schema is correct.** Verified read-only: every branch's DDL is applied,
`clients.suspension_reason` is present, `contracts.start_date` and `end_date`
are `date`. Only the bookkeeping rows are wrong. No data is at risk.

**How to check it.** `alembic current` is misleading here. It prints a single
line, `a5b7c9d1e3f4 (head) (mergepoint)`, because it collapses the display to
the effective head. Only a direct read shows the problem:

```sql
SELECT version_num FROM alembic_version ORDER BY 1;
```

`alembic upgrade head --sql` is no help either: it is offline, never reads
`alembic_version`, and crashes anyway (BE-A09).

**Recommended fix.** Reduce the table to the single row `a5b7c9d1e3f4`, which is
the state a clean merge application would have produced. No DDL, no data change.
This has to be sequenced with BE-A10: that ticket needs the same revision either
re-run or superseded, so repairing the rows first without deciding the file
leaves the same trap for whoever migrates next.

**Not attempted.** This is a write to a database several sessions share, and the
decision belongs to the feature's owner and the user, not to a reviewer.

**Acceptance criteria**

- [ ] `SELECT version_num FROM alembic_version` returns exactly one row.
- [ ] `alembic upgrade head` exits 0 against the shared database.
- [ ] The BE-A10 design decision is made before or with this repair.
- [ ] `README.md:37` and `:56`, which tell a developer to run `alembic upgrade
      head`, are true again.

---

## BE-A09: `alembic upgrade --sql` crashes a twelfth of the way through

**Severity:** 🟡 Medium · **Effort:** S · **Status:** ⬜ Todo

**Problem.** Offline mode is unusable. `uv run alembic upgrade head --sql` exits
1 after emitting four of the 45 revisions:

```
sqlalchemy.exc.NoInspectionAvailable: No inspection system is available for
object of type <class 'sqlalchemy.engine.mock.MockConnection'>
```

Two migrations branch on the live schema by calling `inspect()` on the bound
connection:

- `alembic/versions/32b395f52e9f_add_missing_service_tables.py:45`
- `alembic/versions/3ae4af283411_add_client_code_and_employee_code_fields.py:25`

Offline mode binds a `MockConnection`, which records SQL instead of executing
it and cannot be inspected, so the first of those aborts the run. The pattern is
`if 'code' not in columns:`, which is a migration deciding at runtime whether it
has already been applied.

The consequence is that nobody can review the SQL before it reaches a database,
and no offline or DBA-gated deploy path works. It also removes the one check
that does not require touching a shared database, which matters in a repo where
several people share one.

**How this surfaced.** It was mistaken for a passing check. A clean-looking
prefix of the output was read as evidence that `upgrade head` succeeded, when
the run had aborted before reaching the revision in question. Two things made
that easy: the output begins with a plausible `CREATE TABLE alembic_version`
bootstrap, and piping through `grep` replaces alembic's exit code with grep's.

**Recommended fix.** Make the two migrations declarative. A migration should
know what it does from its own position in the history rather than asking the
database, and the conditional in `3ae4af283411` exists to make a re-run safe,
which the version table already guarantees. If a guard is genuinely wanted,
`op.get_context().is_offline_mode()` lets the migration skip inspection and emit
the DDL unconditionally.

**Acceptance criteria**

- [ ] `alembic upgrade head --sql` exits 0 and emits every revision.
- [ ] No migration calls `inspect()` on the bound connection.
- [ ] CI runs the offline render, so a future migration cannot reintroduce it.

---

## BE-A10: The clients model expects a table no migration creates

**Severity:** 🔴 Critical · **Effort:** S · **Status:** ⬜ Todo

**Problem.** The client aliases feature has moved from a JSON column to a
normalised table, but only half of that move exists. The model layer is on the
new design and the database is on the old one.

Verified offline, without touching the shared database:

```
client_aliases in Base.metadata:        True
alias_records lazy strategy:            selectin
clients.aliases column present in model: False
```

Three facts together make this a runtime break rather than untidiness:

1. `app/infrastructure/models/client_alias_model.py` maps `ClientAliasModel` to
   a table named `client_aliases`, and `models/__init__.py:24` imports it, so it
   is part of `Base.metadata`.
2. No migration creates `client_aliases`. The only aliases migration,
   `a5b7c9d1e3f4_add_client_aliases.py`, adds a JSON column `clients.aliases`
   and nothing else.
3. `client_model.py` declares `alias_records` with `lazy="selectin"`, so every
   load of a `ClientModel` eagerly issues a second SELECT against
   `client_aliases`. Not only queries that ask for aliases; every client query.

So any client read against the current database fails on a table that does not
exist. And the column that was added is now orphaned: `clients.aliases` is
mapped by nothing, because the model no longer declares it.

**Why it matters beyond the break.** BE-A09 records that
`a5b7c9d1e3f4` was applied to the shared database to fix what was believed to be
a live `UndefinedColumnError`. That diagnosis was for the older design. Applying
it added a column nothing uses and did not create the table that is actually
missing, so the break it was meant to fix is still there in a different form.

**Recommended fix.** Decide which design is intended first; the fix differs
completely.

- If aliases are a table, write the migration that creates `client_aliases`
  with its tenant-scoped unique index on `(tenant_id, normalized_alias)` and the
  `clients.id` foreign key with `ondelete="CASCADE"`, and drop the now-unused
  `clients.aliases` column in the same revision.
- If aliases stay a JSON column, delete `client_alias_model.py`, remove it from
  `models/__init__.py`, and drop `alias_records` from `client_model.py`.

Either way `lazy="selectin"` deserves a second look. It makes every client
query pay for aliases whether or not the caller wants them, which is the eager
loading that `C-structure.md` records as deliberately absent everywhere else in
this codebase.

**Acceptance criteria**

- [ ] The model layer and the migration history agree on one design.
- [ ] A client read succeeds against a freshly migrated database.
- [ ] No mapped table lacks a migration, asserted by a test that compares
      `Base.metadata.tables` against the tables the migrations create.
- [ ] `clients.aliases` is either mapped or dropped, not orphaned.

**Ownership.** Not written by this session. The file mtimes put the CSV import
work at 23:51 to 23:54 on 2026-09-04 and `client_model.py` at 00:17 on 09-05.
The owner was still unidentified when this was filed; see the handoff note in
the README.

**This cannot fix itself, which is the part that makes it urgent.** The
migration file was rewritten at 00:21 on 09-05 and now does the right thing: it
creates `client_aliases`, copies the JSON values across, and drops
`clients.aliases`. That work will never run. Revision `a5b7c9d1e3f4` is already
recorded in `alembic_version`, stamped when the file's contents were still
"add a JSON column", so `alembic upgrade` considers it done and skips it.

Verified read-only against the shared database:

| | State |
|---|---|
| `client_aliases` table | does not exist |
| `clients.aliases` column | present |
| `a5b7c9d1e3f4` in `alembic_version` | applied |

So the database is pinned to the old design while the model expects the new one,
and no ordinary migration command closes the gap. Repairing it means either
stamping the revision back and re-running it, or writing a follow-up revision
that does the create-and-copy. That is a decision for the feature's owner, and
it has to be sequenced with the `alembic_version` row repair in BE-A11, because
both touch the same bookkeeping.

That revision id has now carried three different definitions in one evening:
add a JSON column with a single parent, the same with three parents, and
create-table-and-drop-column with three parents. One of the three is what the
database recorded. An applied revision is a fact about a database, so editing
one after it has run makes the file and the database disagree permanently.

The rewritten migration also calls `sa.inspect(bind)` at line 44, which is the
exact pattern BE-A09 records as breaking `alembic upgrade --sql`. So the offline
render stays broken, and the acceptance criterion there should be checked
against this file too.

---

## BE-A08: Outbox dispatcher cannot run on more than one replica

**Severity:** 🟡 Medium · **Effort:** M · **Status:** ⬜ Todo

**Problem.** `app/application/services/outbox_dispatcher.py:9` says so directly:
concurrent dispatchers against the same database are safe but inefficient, and
the worker should be pinned to one replica until `SELECT ... FOR UPDATE SKIP
LOCKED` is wired. Confirmed by grep: no `with_for_update` or `SKIP LOCKED`
anywhere in `outbox_repository.py`.

The comment is honest and the current behaviour is not incorrect, since each row
is updated by id. But the constraint lives only in a code comment, so nothing
stops a second replica being scheduled, and the failure mode is duplicate
delivery of domain events rather than an error anyone would notice.

**Recommended fix.** Claim rows with `SELECT ... FOR UPDATE SKIP LOCKED` so
multiple workers can share the table. Until then, the single-replica constraint
belongs somewhere an operator will see it: the deployment manifest or the
worker's own startup log, not only a module docstring.

**Acceptance criteria**

- [ ] Either row claiming is implemented, or the constraint is asserted at
      startup rather than documented in a comment.
- [ ] If implemented, a test with two concurrent dispatchers shows each row
      dispatched once.
