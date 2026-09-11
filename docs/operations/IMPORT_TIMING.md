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

Five rows, on a laptop, against a local database, so network latency is close
to zero and these are a floor rather than a prediction of production.

| Phase | rows | duration_ms | query_ms | queries | queries/row |
| --- | --- | --- | --- | --- | --- |
| stage | 5 | 9.2 | 5.9 | 3 | 0.6 |
| apply | 5 | 141.5 | 70.3 | 33 | 6.6 |

Staging at 0.6 queries per row is the preload working: the lookups are batched
across the file rather than repeated per row.

Apply is still 6.6 queries per row, and half the wall clock is inside SQL even
with no network in the way. On a remote database each of those queries also
carries a round trip, which is what makes a large roster slow. The remaining
lever is batching commits behind savepoints; it changes the durability
guarantee that a lost response never loses a written row, so measure a real
run against Neon first and decide against that number.

The five-row sample includes the once-per-client sequence read, so per-row
figures for a full chunk will be lower. Take a real reading before drawing
conclusions from this table.
