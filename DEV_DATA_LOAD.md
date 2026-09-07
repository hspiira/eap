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
| `providers` | 60 | `POST /practitioner-imports/{batch}/apply` |
| `provider_organisations` | 13 | same apply |
| `provider_affiliations` | 43 | same apply |
| `provider_aliases` resolved | 64 | `scripts/resolve_provider_aliases.py` |
| `provider_aliases` unmapped | 204 | queued, awaiting a person |
| `eligible_members` | 3,305 | `scripts/import_members.py` |
| `service_sessions` | 86 | `POST /session-imports/{batch}/apply` |

The 86 sessions are 85 imported from the activity log plus one that predates
the load.

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

7,471 rows staged, 85 applied:

| Rows | Outcome | What it waits on |
| --- | --- | --- |
| 85 | Accepted, imported | done |
| 5,283 | UnmappedPractitioner | practitioner records that do not exist |
| 1,458 | UnresolvedMember | rosters for 23 clients, and 73 rows with no member id |
| 637 | MissingPractitioner | the row names no counselor at all |
| 5 | UnresolvedService | an intervention with no catalogue service |
| 3 | UnresolvedClient | a company that resolves to no client |

### The practitioner records are the real blocker

The activity log names 121 distinct counselors. The practitioners workbook
produced 60 practitioners. Only **4** of the 121 are among them.

48 of the remaining names map, through the client's own `Counselors` sheet, to
a canonical practitioner who is not in the practitioners workbook at all:
Daniel Kanamara alone accounts for 1,304 sessions, Stella Twinamatsiko 911,
Faith 852, Cynthia Miiro 614, Olivia Kaggwa 539. Another 69 names have no
mapping and no matching practitioner, 407 rows between them.

No amount of alias work moves those rows. Either the client supplies these
practitioners, or somebody authorises creating them from the canonical name
list, which means provider records with no profession, tier, accreditation or
organisation. That is a decision, not a data fix, and it is the single largest
thing standing between this environment and a complete session history.

### The member rosters are the second blocker

1,385 of the 1,458 UnresolvedMember rows name a member id that is not on the
client's roster, spread over 23 clients. Only five clients have any roster at
all, because the Staff sheet covers six companies: Stanbic Bank 398 rows,
Absa 270, Diamond Trust Bank 132, KPMG 123, I&M Bank 79, KCB Bank 75, and so
on down to two rows each for Agro Consortium, Coca-Cola and Ithuba. Absa, KCB,
Dfcu, HRAF and the rest have no members loaded because no roster was supplied
for them.

The other 73 rows name an individual and carry no member id. They stay staged
rather than being attached to somebody by name.

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
the activity log. Decision 5 in `PROVIDERS_MIGRATION.md` is why: a normalised
name is not identity, and an alias that merely looks like a practitioner's name
is a question for a person, not a match for a script.

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

1. **The practitioners who delivered the sessions.** 5,283 session rows name a
   counselor with no practitioner record. Supply them, or authorise creating
   them from the canonical list without profession, tier or accreditation.
2. **Member rosters for the other clients.** 1,385 session rows name a member
   id on a client with no roster loaded. The Staff sheet covers six companies;
   the activity log names 23.
3. **IDI staff numbers.** 1,653 employees wait on one column;
   `staff_roster_pending.csv` is ready to send.
4. **204 unmapped practitioner aliases**, 117 of them activity-log spellings.
5. **637 session rows that name no counselor**, and 73 that name an individual
   with no member id. Both are source gaps, not mapping gaps.
6. **109 `NeedsReview` rows** in the practitioner import batch
   (`rbmhgppuptpyknd1j4hyciyz`), which apply correctly passed over.
7. **Confirm the `Stanbic Bank Uganda` alias.** It is recorded and applied; it
   is still an identity call somebody else should sign off.
8. **Clinician sign-off** on the 16 diagnosis types and 88 diagnoses.
9. `Crisis Intervention` exists in dev but is not in the workbook catalogue;
   the taxonomy importer reports it and leaves it alone rather than retiring
   it. 5 session rows fail on an intervention with no catalogue service.

## Recorded for whoever picks up the session importer

A staged session row keeps its resolved ids and its raw practitioner name, and
nothing else from the source. It does not keep the raw company, member
reference, intervention or status it was judged from, so a batch cannot be
re-judged when the reference data improves: the only recovery is to abandon it
and stage the extract again. The practitioner import rows keep a full
provenance JSON and do not have this problem. Giving session rows the same
would turn every future reference-data load into a re-judge instead of a
re-stage, and is the change worth making before a production load.

## Backup

A dump taken before the first load is at
`evexia_db_before_import.dump` in the session scratchpad. It is not in version
control and will not survive the machine; take a fresh dump before any
production load.
