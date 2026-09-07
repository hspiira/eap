# Practitioners workbook against the provider implementation

Reviewed 2026-09-07 against `40a29d2` on `chore/monorepo`. Source:
`/Users/piira/Downloads/Practitioners & orgs.xlsx`, SHA-256
`ec690c205cbe9172538a6908100cde63353a1cc18652941ffe07c157117e48e9`.
Three sheets: "Minet EAP Partner list" (100 practitioner rows), "EAP
Consultants - General" (68 rows), "Requirement Checklist" (19 provider rows).
All figures below were computed from the file at that hash.

**Ownership.** The provider module belongs to the provider worktrees
(`wt-agent1..3`); this review is advisory and implements nothing. It follows
the decisions already adopted in `PROVIDERS_MIGRATION.md` and flags where the
workbook meets or misses them.

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
(60,000 / 500,000 UGX and similar). `PROVIDERS_MIGRATION.md` records supplier
contracts as a deferred capability requiring its own design, and nothing in
the current model holds a practitioner rate; `rate_ugx` lives on the session.
The import should preserve these columns as source data and not invent a rate
field. If supplier contracting is picked up, this sheet is its seed data.

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

## Suggested order for the provider owner

1. Decide P-02 (checklist home) and the P-01 catalogue vocabulary, both
   product decisions.
2. Import organisations first, then practitioners, then affiliations, through
   the existing alias pipeline with this workbook as `source_system`.
3. Keep P-03 rates and P-06 statuses as preserved source columns, unmodelled.
4. Leave every imported practitioner unbookable until tier, region and
   accreditation are assessed by a person (P-05).

No import was run, and nothing here changes code. The provider worktrees own
implementation; this file is their input.
