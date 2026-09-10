# Practitioners workbook against the provider implementation

Reviewed 2026-09-07 against `40a29d2` on `chore/monorepo`. Source:
`/Users/piira/Downloads/Practitioners & orgs.xlsx`, SHA-256
`ec690c205cbe9172538a6908100cde63353a1cc18652941ffe07c157117e48e9`.
Three sheets: "Minet EAP Partner list" (100 practitioner rows), "EAP
Consultants - General" (68 rows), "Requirement Checklist" (19 provider rows).
All figures below were computed from the file at that hash.

**Ownership.** The provider module belonged to the provider worktrees
(`wt-agent1..3`), now dormant per `docs/migrations/PROVIDERS_MIGRATION.md`'s
2026-09-07 entry directing provider-module work onto the main branch. This
review started advisory and implementing nothing; P-08 through P-10 below were
implemented and tested on 2026-09-07 under that same direction, at the user's
explicit request, before any real import runs. It follows the decisions already
adopted in `docs/migrations/PROVIDERS_MIGRATION.md` and flags where the workbook
meets or misses them.

## Where the implementation already fits the file

The model separation the migration adopted is exactly what this workbook
needs, and none of it has to be invented:

- **Practitioners vs organisations vs affiliations.** The partner list mixes
  both in one column: `INDIVIDUAL/COMPANY NAME` holds "Individual" for 22 rows
  and an organisation for the rest, with 9 organisations carrying more than
  one practitioner (ICFC 12, Minders 6, Chapters 6+2, New Life 4). That maps
  cleanly onto `providers`, `provider_organisations` and
  `provider_affiliations`, which already exist with the right fields,
  including `registration_number` for the checklist's certificate column.
- **Name reconciliation.** 17 names appear on both sheets, before spelling
  variants. The alias pipeline (`provider_aliases`: source_system,
  source_value, normalized_value, resolution state, candidate ids) is built
  for precisely this, and the rule that identity is never inferred from a
  normalized name alone is already policy.
- **Specialty catalogue.** A global specialty vocabulary and tenant links
  exist (`/provider-specialties`), and `ProviderProfile.specialties` holds the
  assignment.

## Findings

### P-01: 57 profession spellings for roughly a dozen roles

`PROFESSION` holds 57 distinct values across 100 rows: "Clinical Psychologist"
(16), "Clinical Psychology" (4), "Counselling Psychologist" (7), "Counseling
Psychologist" (3), and so on. The consultants sheet adds `Speciality` with 50
distinct values of its own. Same class of problem as the session extract's
S-06, and the same rule should apply: an explicit, version-controlled mapping
into the specialty catalogue, applied at import with an unmapped outcome, no
fuzzy matching. Which role names become catalogue entries is a product/clinical
decision, not an engineering one.

### P-02: the requirement checklist has no home in the model

The checklist tracks seven engagement documents per provider (contract, KYC,
certificate of registration, MoA, licence, declaration form, lead consultant
CV) in a vocabulary of ✓ (32), X (54), "open" (12), and ad hoc durations
("1year", "2024"). The implementation models `accreditation_status` as one
value and `license_info` as one JSON blob; there is no per-document compliance
record, so this sheet cannot be represented without flattening it into a
remark. If tracking engagement paperwork per provider matters, that is a small
new table for the provider owner to design; if not, the checklist stays a
spreadsheet and only `accreditation_status` is derived from it. Decision
needed either way; recorded, not assumed.

### P-03: per-practitioner rates are captured but deliberately unmodelled

The consultants sheet carries `Counsel` and `Talks` rates per practitioner
(60,000 / 500,000 UGX and similar). `docs/migrations/PROVIDERS_MIGRATION.md`
records supplier contracts as a deferred capability requiring its own design,
and nothing in the current model holds a practitioner rate; `rate_ugx` lives on
the session. The import should preserve these columns as source data and not
invent a rate field. If supplier contracting is picked up, this sheet is its
seed data.

### P-04: contact columns do not fit one-to-one

- Two mobile columns per practitioner; the model has one `contact_phone`.
  Decision: second number to `license_info`-style JSON, or dropped, or a
  contacts table. Do not silently concatenate.
- One cell holds two emails
  (`janetkidda@gmail.com/info@safeplacesUganda.com`); the second is an
  organisation address. Split by hand at import review, not by code.
- Only 39 of 100 partner rows have an email at all. `contact_email` is
  nullable, so this imports cleanly; worth knowing for outreach expectations.

### P-05: nothing in the file supplies tier, region, panel status or gender

The booking gate runs on `tier`, `region` (UgandaRegion), `accreditation_status`
and `panel_status`. The workbook has none of them: `OFFICE LOCATION` holds
suburbs ("Muyenga", "Rubaga"), which a person can map to regions but code must
not guess, and there is no tier anywhere. Imported practitioners therefore
arrive `Pending`/unassessed and are not bookable until someone assesses them,
which is the correct default under the existing rules, not a defect. The
`Saluttion` column (Mr./Mrs./Dr.) could be read as gender; it must not be, for
the same reason identity is not inferred from names.

### P-06: the consultants sheet's `Contract` column is not contract data

Values: "Done" (30), blank (21), "Partnership"/"partnership" (16),
"Employee" (1). This is a status memo, not a contract reference. Import it as
source provenance only. The one "Employee" row is worth a human look: an
employee is not an external practitioner, and enrolling them as one would
blur the practitioner/staff boundary the migration keeps deliberate.

### P-07: several rows use a person's own name, or another practitioner's
name, as the organisation

Found 2026-09-07 while staging this workbook for real against a local dev
database (see `practitioner-import-review/README.md` for the full run; names
and emails are deliberately not repeated here, see that file's access note).
Corrected 2026-09-07: an earlier version of this finding cited rows 86 and 100
for this pattern; those two row numbers actually belong to unrelated,
ordinary rows. The rows that actually exhibit the pattern are, exactly:

- Three exact self-name matches (the organisation column equals the
  practitioner's own name after trimming and case-folding): `Minet EAP
  Partner list` rows 82 and 83, and `EAP Consultants - General` row 50.
- Two near-match pairs, where the organisation column on one row equals
  another practitioner's name elsewhere in the workbook rather than the
  row's own name: `Minet EAP Partner list` row 88 and `EAP Consultants -
  General` row 55 name each other's row as their organisation, and share one
  contact email between them; `Minet EAP Partner list` row 102 and `EAP
  Consultants - General` row 48 share a different contact email, and row 48
  already names a real, separately-listed organisation as its own company,
  which is the more likely true employer for both.

The importer takes each organisation column literally, so an unreviewed apply
would create up to five single-practitioner "organisations" that are really
just this data-entry inconsistency. Not asserted as fact, not fixed here:
this is exactly the class of candidate the alias/duplicate pipeline exists to
raise, and it needs the same human reconciliation as any other duplicate-name
candidate before an apply. Unowned; the provider module owner should resolve
it alongside the existing `provider_aliases` queue. Of these rows, only row
83 is currently `Accepted`; it is the only one of the five that needed a
correction in `practitioner-import-review/practitioners.system.json` today.

### P-08: apply did not carry a practitioner's phone number or profession
onto the created record — phone half fixed 2026-09-07

Found 2026-09-07 while building a system-shaped export of the currently
`Accepted` rows. `apply_practitioner_import.py` set `contact_phone = None`
unconditionally on every created practitioner, and left
`provider_profile.specialties` at its empty default; neither the workbook's
mobile number columns nor `mapped_profession` (computed at staging specifically
to decide Accepted vs. NeedsReview) reached the created `ProviderEntity`. A
narrower, more actionable instance of the "To fix" table's "Typed profile
promotion" item in `docs/migrations/PROVIDERS_MIGRATION.md`, not a new category
of gap.

**Phone: fixed and tested 2026-09-07.** `apply_practitioner_import.py` now sets
`contact_phone` from the row's own provenance (`CONTACT MOBILE 1`, else `MOBILE
CONTACT 2`, first non-blank only, never concatenated). Recorded as an adopted
decision in `docs/migrations/PROVIDERS_MIGRATION.md`. Covered by new unit tests
in `tests/unit/application/test_apply_practitioner_import.py`.

**Profession/specialty: deliberately not fixed.** Populating
`provider_profile.specialties`, even as free text, would answer the P-01
catalogue-vocabulary question by writing code around it instead of a person
deciding it. Still unowned; the provider module owner should decide P-01
first, then create the corresponding `ProviderSpecialtyLinkEntity` rows, or
explicitly accept that specialty stays manual-entry-only after import.

### P-09: staging had no check for an organisation name colliding with a
practitioner name — fixed 2026-09-07

Found 2026-09-07 alongside P-07. The duplicate-identity check compared a
row's own normalised *name* against other rows' normalised names, but never
compared a row's *organisation* column against any practitioner's name. Row
83 (P-07) staged as `Accepted` with an empty `reasons` list: nothing about it
looked wrong to the pipeline, even though its organisation column was
verifiably its own practitioner name.

**Fixed and tested 2026-09-07.** `practitioner_import_staging.py` now runs
the same normalisation already used for name-deduplication against each
row's `organisation_name`, and adds an `OrganisationNameCollision` reason
when it matches any practitioner name in the batch, symmetric to the
existing duplicate-name check. Re-staging the real workbook after the fix
moved row 83 from `Accepted` to `NeedsReview` and automatically caught 4 of
the other 5 rows named in P-07 (not the Dr. Kasenene Paul / Dorothy Kasenene
pair, which hinges on a shared email rather than a name collision, and is
correctly still unresolved). Covered by new unit tests in
`tests/unit/application/test_practitioner_import_staging.py`.

### P-10: review reasons were free-text English sentences with no machine-
readable code — fixed 2026-09-07

Found 2026-09-07 while building `practitioner-import-review/practitioners.json`
and `role_descriptions.json` from the API's own `reasons` field: distinguishing
"unmapped profession" from "duplicate-name candidate" from "double email cell"
required regex-matching English prose (`"Same normalised name as (.+):
candidates for one identity"`), because the field carried only a message string,
never a code. The same shape of defect that finding 3 in
`docs/migrations/PROVIDERS_MIGRATION.md` already fixed for `ValidationException`
field errors elsewhere in this same migration: a message good enough to display
is not good enough to build a review UI or any other consumer against, because
prose can be reworded without anyone noticing it broke a downstream parser.

**Fixed and tested 2026-09-07.** `PractitionerImportRowEntity.reasons` is now
a tuple of `ImportReviewReason(code, message)`, with `ImportReasonCode`
(`ALREADY_STAGED`, `MISSING_NAME`, `UNMAPPED_PROFESSION`,
`UNMAPPED_SPECIALITY`, `DUPLICATE_NAME_CANDIDATE`,
`ORGANISATION_NAME_COLLISION`, `MULTI_EMAIL_CELL`, `EMPLOYEE_CONTRACT_MEMO`,
`APPLY_FAILED`) in `app/domain/enums/provider_network.py`. The mapper,
repository JSON column, and `PractitionerImportRowPreview` API schema all
carry the new shape; this is a breaking API contract change to that one
field, but nothing outside the pipeline consumed it yet (no review UI exists
per `docs/migrations/PROVIDERS_MIGRATION.md`), so nothing else needed updating.
`ruff`/`ruff format`/`lint-imports`/the `app/domain` pyright gate all pass,
and the full practitioner-import unit and PostgreSQL-backed integration
suite passes (64 tests). Not run: web contract regeneration, since no
contract-consuming file changed.

## Suggested order for the provider owner

1. Decide P-02 (checklist home) and the P-01 catalogue vocabulary, both
   product decisions.
2. Import organisations first, then practitioners, then affiliations, through
   the existing alias pipeline with this workbook as `source_system`.
3. Keep P-03 rates and P-06 statuses as preserved source columns, unmodelled.
4. Leave every imported practitioner unbookable until tier, region and
   accreditation are assessed by a person (P-05).
5. P-09 and P-10 are now implemented; any review UI or other consumer built
   on top of `reasons` should use the `code` field, not match on `message`.

2026-09-07: staging was run for real against a local dev database
(`practitioner-import-review/README.md` has the batch reference and full
export); nothing was applied. P-08 (phone half only), P-09 and P-10 were
implemented and tested in the provider module's actual code during this
same session, at the user's request, before the workbook was re-staged with
the fixed pipeline; see each finding above for what changed and what is
still open. The provider worktrees are dormant; this file and
`practitioner-import-review/` are now the live record of this work.
