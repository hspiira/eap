# Services module review

Scope: the service catalogue, the diagnosis taxonomy, and the mapping data in
`services.csv`. Written 2026-09-05.

The source data is not in this repository. It was supplied at
`/Users/piira/Downloads/services.csv` and every count below is taken from that
file. If it is not to hand, section 2 records its shape and section 3.4 its
defects, and a copy should be committed somewhere durable before phase 5 of
`SERVICES_MIGRATION.md` runs.

## 1. What exists today

Three separate concepts are already modelled. They are not currently connected
to each other.

### Service catalogue (what the UI calls "interventions")

| Concern | Location |
| --- | --- |
| Entity | `apps/api/app/domain/entities/service.py:19` |
| Table `services` | `apps/api/app/infrastructure/models/service_model.py:30` |
| Coarse grouping enum | `apps/api/app/domain/enums/session.py:50` (`ServiceCategory`) |
| List page | `apps/web/src/routes/services/index.tsx` |

`services.category` is a free-text `String(100)`, not the `ServiceCategory`
enum. The two are unrelated in the schema. The list page's empty state reads
"Add an intervention to the catalog so contracts can cover it", so in product
language a service row is an intervention.

### Diagnosis taxonomy

| Concern | Location |
| --- | --- |
| Entities | `apps/api/app/domain/entities/diagnosis.py` |
| Tables `diagnosis_types`, `diagnoses` | `apps/api/alembic/versions/f4a6b8c1d3e5_add_diagnosis_taxonomy.py` |
| Repository | `apps/api/app/infrastructure/repositories/diagnosis_repository.py:41` |
| Routes | `apps/api/app/api/routes/diagnoses.py` |
| Selector | `apps/web/src/components/common/DiagnosisSelector.tsx` |

Two levels, strictly one to many: a `DiagnosisType` has many `Diagnosis`. The
migration seeds 16 types and 52 diagnoses. Both tables carry `code`,
`is_active`, `version` and `effective_until`, so the taxonomy is already built
to be versioned rather than edited in place.

### Where the two meet

They do not, except on a session:

```
service_sessions.service_id          -> services.id          (FK-ish, String(25))
service_sessions.diagnosis_type_id   -> diagnosis_types.id   (nullable, no FK)
service_sessions.diagnosis_id        -> diagnoses.id         (nullable, no FK)
service_sessions.issue_topic         Text, free entry
```

See `apps/api/app/infrastructure/models/service_session_model.py:71` and
`:110-111`, and `ServiceSessionEntity.set_clinical_details` at
`apps/api/app/domain/entities/service_session.py:182`.

## 2. What `services.csv` actually is

58 data rows, two columns, `DIAGNOSIS TYPE` and `CLASSIFICATION`. 53 distinct
raw values map to 29 distinct classifications. It is not a services file and it
holds nothing about interventions. It is a legacy string normalisation table:
whatever a counsellor typed, and the canonical bucket someone later assigned it
to.

Every raw value maps to exactly one classification. There are no conflicts, so
the file is usable as a lookup as it stands.

### Relationship in the data

```
raw entry (free text, 53 values)
        │  many-to-one
        ▼
classification (29 values)
        │  mixed level
        ├──► diagnosis_types.name   (11 values)
        ├──► diagnoses.name         (15 values)
        └──► not a diagnosis at all ( 3 values)
```

Largest collapses: 9 raw variants to "Work stress & Anxiety", 6 to
"Family &  Relationship", 4 to "Loss & Grief".

### Classification to seeded taxonomy

Matching on a case and punctuation insensitive comparison against the seeded
taxonomy, 11 classifications hit a type name and 2 hit a diagnosis name
directly. The remaining 16 resolve by inspection as follows.

| Classification | Target level | Target |
| --- | --- | --- |
| Addictions | type | `ADDICTIONS` |
| Career Challenges | type | `CAREER_CHALLENGES` |
| Change Management | type | `CHANGE_MANAGEMENT` |
| Child Teenage Stress | type | `CHILD_TEENAGE` |
| Family &  Relationship | type | `FAMILY_RELATIONSHIP` |
| Financial issues | type | `FINANCIAL_WELLNESS` |
| Health Promotion | type | `HEALTH_PROMOTION` |
| Loss & Grief | type | `LOSS_GRIEF` |
| Medical Disease Management Alert | type | `MEDICAL_DISEASE_MGMT` |
| Mental Ill Health | type | `MENTAL_ILL_HEALTH` |
| Relationship Abuse | type | `GBV` |
| Trauma Disorder | type | `TRAUMA` |
| Work stress & Anxiety | type | `WORK_STRESS_ANXIETY` |
| ADHD Assessment | diagnosis | `ADHD` / `ADHD_ASSESSMENT` |
| ADHD Coaching | diagnosis | `ADHD` / `ADHD_COACHING` |
| Behavioral | diagnosis | `BEHAVIOURAL_PERSONALITY` / `BEHAVIOURAL_PROBLEM` |
| Burnout | diagnosis | `WORK_STRESS_ANXIETY` / `BURNOUT` |
| Career Improvement | diagnosis | `CAREER_CHALLENGES` / `CAREER_ASSESSMENT` |
| Child Sexual Abuse | diagnosis | `CHILD_TEENAGE` / `CHILD_SEX_ABUSE` |
| Daily habits to build emotional strength | diagnosis | `PERSONAL_GROWTH` / `DAILY_HABITS` |
| Depression Disorder | diagnosis | `MENTAL_ILL_HEALTH` / `DEPRESSION` |
| Emotional Resilience | diagnosis | `PERSONAL_GROWTH` / `EMOTIONAL_RESILIENCE` |
| Personality Issues | diagnosis | `BEHAVIOURAL_PERSONALITY` / `PERSONALITY_ISSUES` |
| Physical Fitness | diagnosis | `HEALTH_PROMOTION` / `PHYSICAL_FITNESS` |
| School related concerns | diagnosis | `CHILD_TEENAGE` / `SCHOOL_ISSUES` |
| Emotional challenges | none | needs a new leaf, see 3.2 |
| Coaching & Mentorship | none | not a diagnosis, see 3.1 |
| No show | none | not a diagnosis, see 3.1 |
| Others | none | needs an explicit bucket, see 3.2 |

The assignments in the lower half of the table are my reading of the labels,
not something the file states. They should be confirmed by whoever owns the
clinical taxonomy before they are seeded.

## 3. Findings

### 3.1 Three classifications are not diagnoses

- `No show` is a scheduling outcome. `SessionStatus.NO_SHOW` already exists at
  `apps/api/app/domain/enums/session.py:18`. Storing it as a diagnosis would
  inflate every prevalence count with rows that had no clinical contact.
- `Coaching & Mentorship` is an intervention. It belongs in the `services`
  catalogue, not the taxonomy.
- `Nurturing mental wellness in the workplace` is mapped to `Mental Ill Health`.
  It reads as a promotional or awareness activity, so it is closer to
  `HEALTH_PROMOTION` or, again, a service.

This is the core structural problem: the single legacy column carried diagnosis,
session outcome, and service delivered at once. Splitting them is the main value
of the migration.

### 3.2 Two gaps in the seeded taxonomy

- `Emotional challenges` has no leaf. Either add one under `MENTAL_ILL_HEALTH`
  or fold it into `PERSONAL_GROWTH`.
- `Others` has no home. An explicit `OTHER` type with a single `UNSPECIFIED`
  diagnosis is preferable to a null, because it separates "clinician chose
  other" from "never recorded". Both are reportable, and they mean different
  things.

### 3.3 The two columns are not disjoint vocabularies

20 strings appear on both sides. `Daily habits to build emotional strength` is a
raw value classified as `Personality Issues`, and is also the classification
assigned to the raw value `personal growth`. `Career improvement` and
`Career Improvement` behave the same way. A lookup keyed on the raw string alone
will therefore give different answers depending on which row was read first.
Normalising keys (trim, casefold, collapse punctuation) before loading is not
optional.

### 3.4 Data quality defects in the file

- Three rows hold clinical narrative in the key column, for example
  "The client presented with heavy grief/ sadness and loss of meaning in life".
  These belong in `issue_topic` or the clinical note, not in a taxonomy key.
- The second of those, "The client presented with symptoms of depression and
  fear about living without any parent", is classified as
  `Work stress & Anxiety`. On its own text it reads as depression or loss.
- `Personality` is classified as `Family &  Relationship`. It reads as
  `BEHAVIOURAL_PERSONALITY`.
- `Change Magement Risks` (typo in source) is classified as
  `Career Improvement` rather than `Change Management`.
- `Family Stress, fatigue, Burnout` goes to `Family &  Relationship` while
  `Work Stress, Fatigue, Burnout` goes to `Work stress & Anxiety`. Burnout is
  handled inconsistently across the two.
- `Family &  Relationship` contains a double space, in both columns.
  `Sexual Abuse ` and two narrative rows have trailing whitespace.
- Five rows are exact duplicates.

I have not corrected any of these. Each is a clinical judgement that needs an
owner, and 3.4 items two through five change what a session is counted as.

### 3.5 Diagnosis prevalence reporting is stubbed

`apps/api/app/infrastructure/services/report_query_runner.py:67` returns
`no_data` for `DIAGNOSIS_PREVALENCE` with the note "Session to diagnosis
association not yet wired in v1". The columns exist on `service_sessions`, so
the association is present in the schema. The report is the reason the taxonomy
needs to be clean before the legacy import runs.

### 3.6 The service catalogue is not connected to the entitlement engine

`services.category` is a free-text `String(100)`
(`apps/api/app/infrastructure/models/service_model.py:41`, schema max_length 100
at `apps/api/app/api/schemas/service_schemas.py:23`). The contract types it
`{"anyOf": [{"type": "string"}, {"type": "null"}]}` with no `$ref`, and
`apps/web/src/types/entities/delivery.ts:22` types it `category?: string | null`.

`ProgrammeSessionCap.service_category`
(`apps/api/app/domain/value_objects/programme.py:18`) and
`AuthorizationModel.service_category`
(`apps/api/app/infrastructure/models/eap_programme_model.py:50`) are the
`ServiceCategory` enum (`apps/api/app/domain/enums/session.py:51`), indexed, and
they drive programme session caps.

Nothing derives one from the other. Two consequences:

- Given a completed session you cannot determine which programme cap it should
  draw down, because the only route from the catalogue to the cap is a
  free-text string a user typed.
- `Authorization.consume_session`
  (`apps/api/app/domain/entities/authorization.py:89`) has no callers other than
  the manual route at `apps/api/app/api/routes/eap_programmes.py:203`.
  Entitlement drawdown is manual today.

Typing the column is the prerequisite for automating drawdown. It needs a data
audit of existing values first; there is no seed for this column, so the current
contents are unknown and unmappable values must be decided rather than
defaulted.

**Two different fields are spelled alike, and the confusion is live.** A
frontend session read `service.category` as the `ServiceCategory` enum and
routed it through a label helper in `9b950c3`, which title-cased what users had
typed (`eap` rendered as `Eap`). Corrected in `166f221`. Before treating a field
as enum-backed, confirm it has a `$ref` in the contract and a CHECK constraint
or enum column in the model; `service.category` has neither.

## 4. Recommendation

### 4.1 Add a `diagnosis_aliases` table

The CSV is exactly a persisted alias table. Model it as one rather than as a
one-off script constant, because new spellings will keep arriving from every
counsellor and every legacy tenant.

```
diagnosis_aliases
  id              String(25)  pk
  raw_value       Text        not null          -- as typed
  normalised_key  String(255) not null, unique  -- trim, casefold, collapse punctuation
  diagnosis_type_id String(25) not null, fk diagnosis_types.id
  diagnosis_id      String(25) null,     fk diagnoses.id
  source          String(50)  not null          -- e.g. 'legacy_csv_2026_09'
  confidence      String(20)  not null          -- 'confirmed' | 'inferred'
  created_at, updated_at
```

`diagnosis_id` is nullable on purpose. It carries the type-only rows from the
table in section 2 without inventing a leaf that nobody agreed to. This matches
`service_sessions`, where both columns are already nullable and independent.

`confidence` keeps the 13 direct name matches separable from the assignments I
inferred, so a reviewer can filter to just the ones needing sign-off.

### 4.2 Resolve at import, store canonical ids

Extend `CanonicalMappings` at
`apps/api/app/application/services/historical_import.py:42` with a
`diagnosis_aliases: dict[str, tuple[str, str | None]]` keyed on the normalised
value. Follow the existing contract in that file: an unmapped value is rejected
with a new `REJECTED_UNMAPPED_DIAGNOSIS` classification rather than silently
bucketed into `Others`. That is what makes a missing alias visible before the
import lands instead of after.

Keep the original string on the session in `issue_topic`. It is the only audit
trail back to what the counsellor actually wrote, and the three narrative rows
need somewhere to go.

### 4.3 Do not link services to diagnoses directly

There is a temptation to add a services to diagnoses join, because both are
reference data and the file is called `services.csv`. Resist it. The file gives
no evidence for such a relationship, and clinically the link is not fixed:
counselling serves most diagnoses. The session is already the correct join, and
it carries the tenant, the date, and the provider that any real analysis needs.

If a "which interventions are appropriate for this diagnosis" feature is wanted
later, add it then as an explicit, editable suggestion table, and keep it out of
the reporting path.

### 4.4 Separate the three non-diagnosis values

- Route `No show` to `SessionStatus.NO_SHOW` during import and leave both
  diagnosis columns null.
- Seed `Coaching & Mentorship` as a row in `services`, and map the legacy value
  to `service_id` rather than to a diagnosis.
- Decide `Nurturing mental wellness in the workplace` with the clinical owner.

### 4.5 Then enable prevalence reporting

Once 4.1 through 4.4 are in place, replace the `no_data` stub in
`apps/api/app/infrastructure/services/report_query_runner.py:67` with a group-by over
`service_sessions.diagnosis_type_id`. Report at type level by default. With 52
leaves over the volumes in this file, leaf-level counts will be too sparse to be
meaningful, and small cell counts in clinical reporting are a privacy exposure
in their own right.

## 5. Open questions for the clinical owner

1. The 16 inferred assignments in section 2. Confirm or correct.
2. `Emotional challenges`: new leaf, or fold into an existing type?
3. `Nurturing mental wellness in the workplace`: health promotion, or a service?
4. Section 3.4 items two through five: which classification is correct?
5. Should `Others` be an explicit type, or stay null?
