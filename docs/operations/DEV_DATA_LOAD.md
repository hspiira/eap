# Reference data loaded into the dev environment

What has been loaded into the local dev database (`evexia_db`, tenant
`jfj783wwafdgpvoz48snol6q`) from the client's two workbooks, in the order it
had to happen, with the counts each pass produced and what each one left open.

Nothing here was loaded by writing SQL. Every pass runs through the real API
over ASGI, so each row met the same validation, authorisation and audit path a
person using the UI would meet. Only authentication is stubbed, and the actor
is a real admin user, so the audit trail names somebody.

Sources:

- `Practitioners & orgs.xlsx` — practitioners, organisations, affiliations.
- `logs & More.xlsx` — services, diagnoses, diagnosis types, companies, staff,
  the counselor name mapping, and the activity logs.

The extracts these scripts produce land in `apps/api/data/taxonomy/`, which is
git-ignored: the staff extract is employee personal data and does not belong in
version control.

## What is loaded

| Table | Count | Loaded by |
| --- | --- | --- |
| `diagnosis_types` | 16 | `scripts/import_taxonomy.py` |
| `diagnoses` | 88 | `scripts/import_taxonomy.py` |
| `services` | 18 | `scripts/import_taxonomy.py` |
| `clients` | 43 | `scripts/import_clients.py` |
| `client_aliases` | 63 | `scripts/import_clients.py` |
| `providers` | 113 | `POST /practitioner-imports/{batch}/apply` |
| `provider_organisations` | 13 | same apply |
| `provider_affiliations` | 43 | same apply |
| `provider_aliases` resolved | 170 | `scripts/resolve_provider_aliases.py` |
| `provider_aliases` unmapped | 142 | queued, awaiting a person |
| `eligible_members` | 3,305 | `scripts/import_members.py` |
| `service_sessions` | 369 | `POST /session-imports/{batch}/apply` |

The 369 sessions are 368 imported from the activity log over two passes plus
one that predates the load.

## Order, and why it is not arbitrary

1. **Taxonomy** first, because a service must exist before a session can name
   it and a diagnosis before a session can carry one.
2. **Clients and their aliases**, because a member's company code and a
   session's company column both resolve against them.
3. **Practitioners**, because an alias resolves to a practitioner id and a
   session is attributed to one.
4. **Members**, because a session is attributed to a member of a client.
5. **Aliases**, because resolving one needs the practitioners to exist.
6. **Sessions**, because a session names all four.

Order matters more than it looks. A staged session row keeps no copy of the
source values it was judged from, so a batch staged before its reference data
arrived cannot be re-judged: the extract has to be staged again. The first
activity-log batch was staged too early and every one of its 7,471 rows stalled
on the practitioner step; it was abandoned and restaged after the aliases were
resolved.

## Staff roster

`scripts/extract_staff.py` turns the workbook's `Staff` sheet into the roster
importer's CSV shape and `scripts/import_members.py` feeds it through
`POST /members/import`, which previews every row and then commits each one on
its own.

- 3,291 rows imported over two passes, 0 failed. Re-running the extract and
  the importer now reports all 3,291 as duplicates and writes nothing.
- 1,654 rows held, written to `staff_roster_held.csv` with the reason:

| Held | Reason | Who unblocks it |
| --- | --- | --- |
| 1,653 | `Staff_ID` carries no staff number, only the `IDI-` prefix | the client must supply the staff numbers |
| 1 | an exact repeat of an earlier KPMG row | nobody: the person is imported once |

The KPMG row is not two people sharing an id. Both rows carry the same name,
email, gender and staff number, so it is one person entered twice, and
`staff_roster_held.csv` now says so rather than reporting it as a conflict.

`Stanbic Bank Uganda` was resolved and its 2,043 employees imported. The
Companies mapping already collapses eleven Stanbic spellings into the one
client, including "Stanbic" alone and two misspellings, but never saw the
spelling the Staff sheet uses. `EXTRA_ALIASES` in `scripts/extract_companies.py`
records that decision where a later environment applies it too. It is still an
identity call and the client owner should confirm it.

The IDI sheet is not a roster. All 1,653 rows carry a name and a status and
nothing else: no staff number, no email, no gender, no department, and every
name is distinct. `employer_member_id` is required and unique per client, and
minting one would produce ids that match nothing in IDI's HR system, so that
when the real staff numbers arrive the client gets two members per person.
`staff_roster_pending.csv` holds the 1,653 names with an empty Staff Number
column for IDI to fill and return.

Five rows carried an unparseable email; the address was blanked and the row
reported, rather than dropping the person.

Company codes are the client's own shorthand from the sheet, resolved to this
system's codes through the clients and aliases loaded in step 2. The user has
offered to supply production company codes; those should be slotted into
`scripts/extract_companies.py` as an explicit name-to-code map before the
production load, because the code appears on reports and in member ids.

## Sessions

`scripts/extract_sessions.py` writes the `Activity Logs` sheet out as a CSV,
keeping the cleaned columns a person added (`COUNSELOR (CLEAN)`,
`COMPANY (CLEAN)`, `STATUS (CLEAN)`) beside the originals so staging chooses.
Only formatting is normalised: Excel dates become ISO, whole numbers lose their
`.0`. `POST /session-imports` then judges every row.

`ACTIVITY LOG ID` was not offered as the source key: 284 of its values repeat
and five are blank, and the preflight refuses such a column rather than let a
repeat silently stage as a duplicate. Rows are keyed by file hash and row
number instead, which is stable for this extract.

7,471 rows staged twice. The first pass, before the canonical practitioners
existed, imported 85 and held 5,283 on an unknown counselor. The second, after
they were created, imported 283 more:

| Rows | Outcome | What it waits on |
| --- | --- | --- |
| 6,444 | UnresolvedMember | rosters for the clients the log names |
| 637 | MissingPractitioner | the row names no counselor at all |
| 283 | Accepted, imported | done |
| 85 | Duplicate | already imported by the first pass |
| 14 | UnresolvedService | an intervention with no catalogue service |
| 6 | UnresolvedClient | a company that resolves to no client |
| 2 | UnmappedPractitioner | two spellings nobody has decided |

### The practitioners were created from the canonical list

The activity log names 121 distinct counselors. The practitioners workbook
produced 60, and only 4 of the 121 were among them: Daniel Kanamara alone
accounts for 1,304 sessions and was not a practitioner, nor were Stella
Twinamatsiko (911), Faith (852), Cynthia Miiro (614) or Olivia Kaggwa (539).

The `Counselors` sheet's `CANONICAL LIST` column is a curated one-spelling-per-
person list of 56 names, authored by somebody who knows them.
`scripts/build_canonical_practitioners.py` writes the 53 that were not already
practitioners into a workbook the practitioner import reads, so they were
created through the same staged, reviewed, audited path as every other
practitioner rather than by a route invented for them. Names already held were
left out, so applying could not produce a second record for one person.

UnmappedPractitioner fell from 5,283 rows to 2. What it bought in imports is
smaller, 283 sessions, because the rows behind it then hit the member step.

Two things to know about these 53 records. They carry a name and nothing else:
no profession, tier, region, accreditation or organisation, and they are
`Pending`, which is not bookable, exactly as decision P-05 requires. And seven
of them are a single word, so they cannot tell two people apart: `David`,
`Esau`, `Faith`, `Kebbie`, `Dr. Love`, `Dr. Kalisa`, `Dr. Kasenene`. They are
what the source calls those counselors, and 852 sessions hang off `Faith`
alone, but somebody who knows the team should give each a full name before
this reaches production.

### The member rosters are now the blocker

6,444 rows name a member the client's roster does not hold, or name no member
id at all. Only five clients have any roster, because the Staff sheet covers
six companies while the activity log names 23. Rows that used to stall at the
practitioner step now reach the member step and stop there, which is why this
number rose as the practitioner one fell.

Rows that name an individual and carry no member id stay staged rather than
being attached to somebody by name.

## Practitioner alias resolution

`scripts/resolve_provider_aliases.py` resolves a source name to a practitioner
from two recorded decisions, and refuses everything else.

1. **Provenance.** The practitioner import batch records which row created
   which practitioner. An alias staged from that row names that practitioner as
   a matter of record. 59 resolved this way.
2. **The reviewed mapping.** The `Counselors` sheet is a person's own list of
   source spelling to canonical name. 1 resolved this way (`Moses Mpanga`, to
   the practitioner that already existed before the batch).

204 aliases are left unmapped: 87 from the practitioners workbook and 117 from
the activity log. Decision 5 in `docs/migrations/PROVIDERS_MIGRATION.md` is why:
a normalised name is not identity, and an alias that merely looks like a
practitioner's name is a question for a person, not a match for a script.

Queueing a name needed a route that did not exist. Staging reads reconciliation
decisions and never opens one, so a source system whose names nobody had queued
gave a reviewer nothing to act on, and every activity-log row stalled on the
practitioner step regardless of what the `Counselors` sheet said. Admin-only
`POST /provider-aliases` now opens an entry, unmapped, attributing nothing;
naming the practitioner is still the separate audited resolve step.

### What the Counselors sheet is worth

The sheet has 3,558 rows but only 76 filled pairs, 72 distinct source spellings
and 56 distinct canonical names. It resolved four aliases, because 53 of its 56
canonical names are not practitioners in this environment. Its value is capped
by the practitioner records, not by the mapping: it is a correct answer to a
question the environment cannot yet act on.

Re-run the script after any practitioner load. It is idempotent, it never
reopens an alias somebody already decided, and it resolves only from provenance
or the reviewed sheet.

## Open, needing a person

Ordered by how many rows each one releases.

1. **Member rosters for the other clients.** 6,444 session rows wait on them.
   The Staff sheet covers six companies; the activity log names 23.
2. **IDI staff numbers.** 1,653 employees wait on one column;
   `staff_roster_pending.csv` is ready to send.
3. **Full names for seven canonical practitioners**, and a profession, tier and
   region for all 53, before any of them can be booked.
4. **637 session rows that name no counselor**, and rows that name an
   individual with no member id. Both are source gaps, not mapping gaps.
5. **142 unmapped practitioner aliases**, of which 2 block session rows.
6. **109 `NeedsReview` rows** in the practitioner import batch
   (`rbmhgppuptpyknd1j4hyciyz`), which apply correctly passed over.
7. **Confirm the `Stanbic Bank Uganda` alias.** It is recorded and applied; it
   is still an identity call somebody else should sign off.
8. **Clinician sign-off** on the 16 diagnosis types and 88 diagnoses.
9. `Crisis Intervention` exists in dev but is not in the workbook catalogue;
   the taxonomy importer reports it and leaves it alone rather than retiring
   it. 14 session rows fail on an intervention with no catalogue service.

## Re-staging, and the three faults that blocked it

Reference data improves and rows that could not be resolved before now can.
That is what the Duplicate row outcome is for, and it did not work. Three
faults, each hidden behind the one before it, found by trying to use it:

1. The file-hash uniqueness covered every batch, so an extract could never be
   staged a second time and Duplicate was unreachable for any file. It now
   covers only a batch still awaiting a decision.
2. A duplicate row claimed the same replay key as the row it deferred to, so
   the outcome could not be persisted even when reached. It now defers with a
   key naming the batch that holds the claim. The key staging decided is also
   the one stored: the entity used to re-derive it and quietly drop the
   decision, which made the first fix look like it had done nothing.
3. A row that imported nothing still claimed its source row, so a second
   staging returned all 7,471 rows as duplicates. Staging now releases the
   rows of earlier judgings of the same file that produced no session.

A staged session row still keeps only its resolved ids and its raw
practitioner name, not the raw company, member reference, intervention or
status it was judged from, so a re-judge means staging the extract again
rather than re-scoring the rows in place. The practitioner import rows keep a
full provenance JSON and do not have this problem. Giving session rows the same
is the change worth making before a production load.

## Backup

A dump taken before the first load is at
`evexia_db_before_import.dump` in the session scratchpad. It is not in version
control and will not survive the machine; take a fresh dump before any
production load.

## The audit trail is staged but never delivered (found 2026-09-08)

`audit_logs` and `entity_changes` are both empty in `evexia_db`, while
`outbox_events` holds **3,668 events with `delivered_at` null and
`delivery_attempts` at 0**. The worker that drains the outbox into the audit
tables has never been run against this environment, so no load recorded here
has produced a readable audit trail.

| Aggregate | Events waiting |
| --- | --- |
| EligibleMember | 3,309 |
| ProviderAlias | 170 |
| Provider | 117 |
| ProviderAffiliation | 43 |
| ProviderOrganisation | 14 |
| PractitionerImportBatch | 6 |
| SessionImportBatch | 5 |
| Client | 3 |

Zero delivery attempts, not failed attempts, so nothing is retrying and
`last_error` is empty on every row. Run `apps/api/scripts/outbox_worker.py`
against this database to drain them; the events are durable and none is lost by
having waited.

Until it is run, every Activity tab in the UI correctly reports no recorded
activity. That is the data being absent, not the page being broken: a separate
frontend fault that made those tabs return 404 was fixed in `407ab5d`.

Worth deciding before a production load: whether the worker runs as a service
alongside the API, or whether draining the outbox is a step in the load
procedure. Nothing currently runs it.
