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
| `provider_aliases` resolved | 60 | `scripts/resolve_provider_aliases.py` |
| `provider_aliases` unmapped | 87 | staged, awaiting a person |
| `eligible_members` | 1,262 | `scripts/import_members.py` |

`session_import_rows` is still empty: no activity log has been staged yet.

## Order, and why it is not arbitrary

1. **Taxonomy** first, because a service must exist before a session can name
   it and a diagnosis before a session can carry one.
2. **Clients and their aliases**, because a member's company code and a
   session's company column both resolve against them.
3. **Practitioners**, because an alias resolves to a practitioner id and a
   session is attributed to one.
4. **Members**, because a session is attributed to a member of a client.
5. **Aliases**, because resolving one needs the practitioners to exist.
6. **Sessions**, still to do.

## Staff roster

`scripts/extract_staff.py` turns the workbook's `Staff` sheet into the roster
importer's CSV shape and `scripts/import_members.py` feeds it through
`POST /members/import`, which previews every row and then commits each one on
its own.

- 1,248 rows imported, 0 failed.
- 3,697 rows held, written to `staff_roster_held.csv` with the reason:

| Held | Reason | Who unblocks it |
| --- | --- | --- |
| 2,043 | company `Stanbic Bank Uganda` resolves to no client or alias | needs an alias decision; the extract will not guess which client this is |
| 1,653 | `Staff_ID` carries no staff number, only the `IDI-` prefix | the client must supply the staff numbers |
| 1 | `Staff_ID` `KPMG-63110641` repeats within KPMG | the client must say which of the two people it belongs to |

Five rows carried an unparseable email; the address was blanked and the row
reported, rather than dropping the person.

Company codes are the client's own shorthand from the sheet, resolved to this
system's codes through the clients and aliases loaded in step 2. The user has
offered to supply production company codes; those should be slotted into
`scripts/extract_companies.py` as an explicit name-to-code map before the
production load, because the code appears on reports and in member ids.

## Practitioner alias resolution

`scripts/resolve_provider_aliases.py` resolves a source name to a practitioner
from two recorded decisions, and refuses everything else.

1. **Provenance.** The practitioner import batch records which row created
   which practitioner. An alias staged from that row names that practitioner as
   a matter of record. 59 resolved this way.
2. **The reviewed mapping.** The `Counselors` sheet is a person's own list of
   source spelling to canonical name. 1 resolved this way (`Moses Mpanga`, to
   the practitioner that already existed before the batch).

87 aliases are left unmapped. Decision 5 in `PROVIDERS_MIGRATION.md` is why: a
normalised name is not identity, and an alias that merely looks like a
practitioner's name is a question for a person, not a match for a script.

### The Counselors sheet contributes almost nothing yet

Worth knowing before anyone plans work around it:

- The sheet has 3,558 rows but only 76 filled pairs, 72 distinct source
  spellings, 56 distinct canonical names.
- Only 12 of those 72 spellings appear among the 147 staged aliases. The
  staged aliases came from the practitioners workbook; the sheet describes the
  activity logs, a different name space.
- 53 of the 56 canonical names are not practitioners in this environment. The
  people the activity logs name are largely not in the practitioners workbook.

So the sheet becomes useful only once the activity logs are staged, and even
then most of its canonical names will resolve to nobody until those
practitioners exist. Re-run the script after staging sessions; it is idempotent
and never re-opens an alias somebody already decided.

## Open, needing a person

- `Stanbic Bank Uganda`: add it to the companies mapping, or confirm which
  existing client it is. 2,043 staff rows wait on it.
- IDI staff numbers: 1,653 rows wait on the client.
- `KPMG-63110641`: one duplicate id.
- 87 unmapped practitioner aliases.
- 109 `NeedsReview` rows in the practitioner import batch
  (`rbmhgppuptpyknd1j4hyciyz`), which apply correctly passed over.
- Clinician sign-off on the 16 diagnosis types and 88 diagnoses.
- `Crisis Intervention` exists in dev but is not in the workbook catalogue; the
  taxonomy importer reports it and leaves it alone rather than retiring it.

## Backup

A dump taken before the first load is at
`evexia_db_before_import.dump` in the session scratchpad. It is not in version
control and will not survive the machine; take a fresh dump before any
production load.
