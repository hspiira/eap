# Measuring an import

Both importers log one JSON line per staging call and per apply chunk, so the
cost of a real run against the real database can be read rather than guessed.
No flag to turn on; the lines are always emitted at INFO.

## The fields

| Field | Meaning |
| --- | --- |
| `import_kind` | `members` or `sessions` |
| `import_phase` | `stage` or `apply` |
| `batch_id` | The batch, so chunks of one run group together |
| `rows` | Rows this call processed |
| `commits` | Commits this chunk made (apply only) |
| `duration_ms` | Wall clock for the work, excluding request overhead |
| `query_ms` | Time inside SQL statements |
| `queries` | SQL statements executed |
| `ms_per_row`, `queries_per_row` | The same, divided by `rows` |

`request_id` is added automatically, so a chunk can be tied back to its HTTP
request.

## Reading it

`query_ms` against `duration_ms` is the question worth asking. If most of the
duration is SQL, the cost is round trips to the database and batching commits
is what would help next. If it is not, the time is being spent in the
application and profiling it is the next step.

`queries_per_row` is the number to watch for regressions. A change that
reintroduces a per-row lookup shows up here immediately, while row counts and
outcomes stay correct.

Collect the lines for one run with the batch id:

```
vercel logs --json | jq 'select(.batch_id == "<batch id>")'
```

Or locally, from the integration test that exercises a real apply:

```
MEMBER_TEST_DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/postgres \
  uv run pytest tests/integration/test_members_persistence.py \
  -k logs_what_the_chunk_cost -s --log-cli-level=INFO
```

## Baseline, local PostgreSQL, 2026-09-11

On a laptop against a local database, so network latency is close to zero and
these are a floor rather than a prediction of production.

| Phase | rows | duration_ms | query_ms | queries | queries/row |
| --- | --- | --- | --- | --- | --- |
| stage | 5 | 9.2 | 5.9 | 3 | 0.6 |
| apply | 25 | 162.8 | 75.0 | 203 | 8.1 |

Staging at 0.6 queries per row is the preload working: the lookups are batched
across the file rather than repeated per row.

### What the commit cadence is worth

The same 25 rows, the same 203 statements, committed two ways:

| Cadence | commits | duration_ms | query_ms | ms/row |
| --- | --- | --- | --- | --- |
| Every row | 25 | 624.3 | 290.0 | 24.97 |
| Every 10 rows | 3 | 162.8 | 75.0 | 6.51 |

**3.8x, with the query count identical.** The work did not change; only how
often it was made durable. Each commit is a WAL flush, and paying that per row
was most of what a roster import cost.

Savepoints add two cheap statements per row (`SAVEPOINT`, `RELEASE`), which is
why queries per row went from 6.6 to 8.1 while the wall clock fell. Neither
carries an fsync, so the trade is heavily net positive.

`COMMIT_EVERY_ROWS` in `app/shared/utils/batched_commit.py` is the knob. Set it
to 1 to get the old per-row behaviour back; the A/B above was produced exactly
that way.

### The durability trade

A call that dies mid-chunk leaves up to `COMMIT_EVERY_ROWS - 1` rows for the
next call to write again. Nothing is lost: a row that never committed never
claimed itself and is still pending, so the next call picks it up. What
changed is that a crash can cost repeated work, where before it could not.

Per-row isolation is unchanged. Each row writes inside its own savepoint, so a
row that fails is undone on its own and the rows around it in the same
uncommitted batch still stand. That is covered against real PostgreSQL in
`test_a_lost_row_is_undone_whole_without_taking_the_chunk_with_it`.

### Still to measure

Every figure here is local. On Neon each statement also carries a round trip,
which is the number that decides whether 8.1 queries per row is worth attacking
next. Take a reading from a real run before going further.
