# Field-level encryption expansion

Working record for extending `app/core/encryption.py`'s AES-256-GCM field
encryption beyond `service_sessions` and moving the key-encryption key (KEK)
off a plain settings value toward a real key-management service. Tracked in
git; update as decisions change.

## Background

Prior state (confirmed by direct code reading, not assumption):

- Only `service_sessions.notes/feedback/issue_topic/partner_name` were
  encrypted at rest.
- `ClinicalNoteModel`'s docstring claimed "body fields are encrypted at rest"
  with no implementing code. That claim is now true.
- `EligibleMember.national_id`, `.passport_number`, `.date_of_birth` were
  plaintext columns.
- The KEK came only from `settings.ENCRYPTION_KEK`, a base64 value read
  directly from config/environment. No KMS integration existed anywhere in
  the repo (confirmed by grep: no boto3/google-cloud-kms/azure-keyvault/hvac
  dependency, no AWS/GCP/Azure/Vault reference in code, docs, or CI).
- No database- or infrastructure-level at-rest encryption evidence exists.
  Only TLS-in-transit is confirmed (`sslmode=require`, `channel_binding=require`
  on the Neon connection string).
- A separate, non-overlapping mechanism (`clinical_data_classification.py`,
  `AuditEventHandler`, `redact_values`) redacts audit-log diffs only. It never
  touches the source table's stored value.

## Decisions

- Add `national_id`, `passport_number`, `date_of_birth` on `EligibleMember`,
  and `body`/`amendments` on `ClinicalNote`, to the same AES-256-GCM,
  per-tenant-DEK scheme `service_sessions` already uses. `amendments` was
  included alongside `body` even though the user's request said "clinical
  note content" without naming it explicitly: an amendment carries the same
  category of clinical narrative as the note body it corrects, so leaving it
  plaintext would defeat the point.
- No blind-index column is added for `national_id`/`passport_number`.
  Encrypting with a random per-call nonce makes `WHERE column = value`
  lookups impossible without one, but no such exact-match lookup exists
  anywhere in the codebase today (confirmed by search). Revisit if a future
  feature needs to look up a member by national ID or passport number.
- Build a pluggable `KeyProvider` (`SettingsKeyProvider` default,
  `AWSKMSKeyProvider` optional) rather than hard-switching to one KMS
  vendor, mirroring this codebase's existing pattern for optional backends
  (`app/core/login_rate_limit.py`: a `Protocol`, an always-available default,
  an optional real backend behind `try: import X except ImportError`, one
  factory function). AWS was the concrete KMS implemented because it was the
  only one with any adjacent signal to build against; it is not a stated
  infrastructure decision, and no other cloud vendor's absence was evaluated.
- **`ENCRYPTION_KEY_PROVIDER` stays `"settings"` by default.** Raised to the
  user that AWS KMS is not actually free (confirmed from
  https://aws.amazon.com/kms/pricing/: $1/month per customer-managed key,
  first 20,000 requests/month free, $0.03/10,000 requests beyond that). The
  user chose to stay on the zero-cost settings-based provider for now rather
  than pay the ~$1/month AWS KMS fee. The AWS KMS provider code remains in
  the tree, unused unless `ENCRYPTION_KEY_PROVIDER=aws-kms` is set, so it is
  available without further work if the decision changes.
- Not built: a free, self-hosted alternative (e.g. HashiCorp Vault's Transit
  engine). Discussed as an option; not requested. If the settings-based KEK
  is judged insufficient later, Vault is the next candidate under the same
  `KeyProvider` interface, not a new architecture.

## Backfill migrations

Both new tables already hold real plaintext rows in every environment this
has been tested against, unlike the original `service_sessions` encryption
migration (`c1d3e5f7b9a2`), which skipped a backfill because that table was
empty at the time. A schema-only change here would make `decrypt()` raise on
the first read of any existing row the moment the mapper change deploys, so
both migrations do a real, symmetric encrypt/decrypt backfill:

- `b4d6f8h0j2l4_encrypt_member_pii.py` — widens `eligible_members.national_id`,
  `.passport_number` (`VARCHAR(100)` to `TEXT`) and `.date_of_birth` (`DATE`
  to `TEXT`, via `postgresql_using="date_of_birth::text"`/`::date`),
  encrypting/decrypting every non-null row in `upgrade`/`downgrade`.
- `c5e7g9i1k3m5_encrypt_clinical_note_body.py` — widens `clinical_notes.body`
  and `.amendments` (`JSON` to `TEXT` and back, via explicit
  `postgresql_using` casts on both sides), re-serialising each row's
  JSON exactly as the mapper would before encrypting it, so a row written
  before or after this migration reads back identically. Rows are fetched
  before the column type changes, since decoding needs the JSON-typed value.

Both migrations wire up the same `KeyProvider` `app/main.py` would at
startup, since Alembic runs outside the FastAPI lifespan and nothing has
called `set_key_provider()` yet when a migration runs. A KMS-backed
`ENCRYPTION_KEY_PROVIDER`, if configured later, is honoured here exactly as
it would be at request time.

## Verification performed

- Both migrations run end-to-end, forward and backward, against an isolated,
  disposable `eap_encryption_test` Postgres database (created with `createdb`,
  dropped with `dropdb` after), seeded with minimal FK-satisfying rows.
  **Never run against the shared `evexia_db` dev database.** Confirmed
  afterward via `psql evexia_db -c "select version_num from alembic_version;"`
  that `evexia_db` remained at the prior head (`s8u0w2y4a6c8`), untouched.
- `.venv/bin/python -m pytest tests/unit -q`: 2260 passed, 0 failed, no
  regressions from before this change.
- New unit tests: `test_eligible_member_encryption.py` (4 tests),
  `test_clinical_note_encryption.py` (5 tests), plus `AWSKMSKeyProvider`/
  `get_key_provider` coverage added to `test_encryption.py` (10 new tests).
- `lint-imports`: all three architecture contracts kept (`Domain is pure`,
  `Application depends only on domain`, `API routes do not import
  infrastructure directly`).
- `pyright` on every touched file: 1 error (unresolved `boto3` import),
  matching the accepted, pre-existing pattern for the optional `redis`
  dependency in `login_rate_limit.py`. No other errors.
- `ruff check` / `ruff format --check`: clean on every touched file.

## Scope expansion: the remaining plaintext fields

The user asked to encrypt the rest of the plaintext PII/clinical fields the
background research had already found (see Background above) rather than
leave them for later. Added to the same scheme:

- `Case.referral_notes`, `ClinicalSubject.notes_for_continuity` (already
  `TEXT` columns, encrypt/decrypt only, no widening).
- `OutreachRecord.notes`, `.triage_responses`, `.triage_scores` (the latter
  two follow the `ClinicalNote.body` pattern: JSON serialise, then encrypt;
  unlike `.body` these are nullable, so `None` stays `None` through both
  directions rather than becoming an empty JSON value).
- `MemberNextOfKin.name`, `.phone`, `.email` (`VARCHAR` widened to `TEXT`,
  same as `eligible_members.national_id`/`.passport_number`).

Two correctness issues surfaced while wiring this up, both fixed as part of
the same change rather than left for later:

- `OutreachRecordRepositoryImpl.save()` updated an existing row by copying
  plaintext values straight from the domain entity onto the ORM model,
  bypassing `OutreachRecordMapper.to_model()` entirely. Every other
  repository in this codebase builds the model via its mapper first and
  copies encrypted fields from that; this one didn't, so an update (as
  opposed to a create) would have written plaintext into the encrypted
  columns. Fixed to route through the mapper like its siblings. Checked
  every other save() path added by this and the prior encryption change
  (`EligibleMemberRepositoryImpl`, `CaseRepositoryImpl`,
  `ClinicalNoteRepositoryImpl`, `MemberNextOfKinRepositoryImpl`) and
  confirmed none of them have the same bug.
- `MemberNextOfKinRepositoryImpl.list_for_member()` ordered contacts with
  `ORDER BY name ASC` at the SQL level. Once `name` is ciphertext, that
  sorts encrypted bytes, not names. Fixed by dropping `name` from the SQL
  `ORDER BY` (keeping `is_primary DESC`, which stays plaintext) and sorting
  the decrypted entities by name in Python afterward. Checked every other
  encrypted field added by this and the prior change for the same
  ordering/exact-match risk (grep across `app/infrastructure/repositories/`)
  and found no other instance.

New migration `d6f8h0j2l4n6_encrypt_remaining_pii_fields.py` backfills all
four tables, verified the same way as the first round: full upgrade and
downgrade cycle against a disposable, isolated database, seeded with one
real row per table, confirming the decrypted value matches the original
plaintext exactly (including the JSON round-trip for the outreach triage
fields) and that downgrade restores the original column types.

## evexia_db status

Both migrations have run against the shared local `evexia_db`. This was not
a planned, confirmed action: it happened by mistake while verifying a test
fix, because `alembic upgrade head` was run with `TEST_DATABASE_URL` set,
but this repo's Alembic config reads `settings.DATABASE_URL`, and
`ENVIRONMENT=test` was not set, so `Settings` fell back to the repo-root
`.env`, which points at `evexia_db`.

Checked directly before deciding anything: `evexia_db` had 0 rows with
`national_id`, 0 with `passport_number`, and 4 rows with `date_of_birth`
(now encrypted in place); `clinical_notes` had 0 rows (schema-only change).
Told the user immediately with the exact numbers and that the change was
fully reversible via `downgrade()`. The user chose to leave it migrated
rather than revert it, since it is the intended end state, just applied
earlier than confirmed. `evexia_db` is now at Alembic head `c5e7g9i1k3m5`.

No production database has been touched.

The new `d6f8h0j2l4n6` migration (the scope expansion above) has **not**
been run against `evexia_db`. Checked directly: `cases.referral_notes`,
`clinical_subjects.notes_for_continuity`, `outreach_records` (notes/triage),
and `member_next_of_kin` all have 0 non-null/0 rows there today, so running
it would be a schema-only, zero-data-impact change, but it has not been run
without asking first this time.

## Outstanding

- The new `d6f8h0j2l4n6` migration has not been applied to `evexia_db` or
  any production database.
- `scripts/generate_kms_kek.py` is a one-time bootstrap for
  `ENCRYPTION_KMS_KEY_ID`/`ENCRYPTION_KEK_CIPHERTEXT`, needed only if the
  `aws-kms` provider is turned on later. It has not been run against a real
  AWS account; it calls `boto3.client("kms").generate_data_key(...)` and
  never prints the plaintext key, only a fingerprint.
