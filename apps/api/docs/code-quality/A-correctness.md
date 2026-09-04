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

## BE-A07: No catch-all exception handler, so a 500 ships bare

**Severity:** 🟡 Medium · **Effort:** S · **Status:** ⬜ Todo

**Problem.** `register_exception_handlers` in `app/core/exception_handlers.py:79`
registers handlers for `HTTPException`, `EvexiaException` and validation errors.
There is no handler for bare `Exception`.

Found while writing `tests/unit/shared/test_security_headers.py`: a route
raising an unexpected `ValueError` produced a 500 whose only headers were
`content-length` and `content-type`. `X-Frame-Options`,
`X-Content-Type-Options` and `Referrer-Policy` were all absent, because
Starlette's `ServerErrorMiddleware` sits outside the middleware stack and the
response never passes back through `SecurityHeadersMiddleware`.

So the one response class most likely to be triggered deliberately is also the
one that ships without the security headers and without the request id that
`app/shared/middleware/request_id.py` adds for correlation. An unexpected
exception is also the case where the response body is least controlled.

**Recommended fix.** Register a handler for `Exception` that logs with the
request id and returns the same error envelope as the others. That puts the
response back inside the middleware stack, so headers and correlation id apply,
and it stops an unexpected traceback shape from being the client's error
contract.

**Acceptance criteria**

- [ ] An unhandled exception returns the standard error envelope.
- [ ] Security headers and the request id are present on a 500.
- [ ] The exception is logged at error level with the request id.
- [ ] `DEBUG` still controls whether detail reaches the client.
- [ ] `tests/unit/shared/test_security_headers.py` gains the 500 case that this
      ticket currently makes untestable.

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
