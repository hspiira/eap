# Service catalogue and diagnosis taxonomy

The system's reference data for interventions and clinical vocabulary, with a
description on every row. Written 2026-09-07.

Source of record: `scripts/taxonomy_catalogue.py`. It holds the catalogue and
the descriptions, takes no input file, and rebuilds the payloads on demand.

```
uv run python scripts/taxonomy_catalogue.py
```

| File | Rows | Shape |
| --- | --- | --- |
| `data/taxonomy/diagnosis_types.json` | 16 | `code`, `name`, `description`, `sort_order`, `is_active` |
| `data/taxonomy/diagnoses.json` | 88 | `type_code`, `code`, `name`, `description`, `sort_order`, `is_active` |
| `data/taxonomy/services.json` | 20 | `name`, `description`, `category`, `duration_minutes`, `is_group_service`, `max_participants` |

Verified against the API contract: the service rows validate as `ServiceCreate`,
the type rows as `DiagnosisTypeCreate`, and the diagnosis rows as
`DiagnosisCreate` once `type_code` is resolved to the created type's `type_id`.
`type_code` is carried instead of `type_id` because ids do not exist until the
types are written, so the importer resolves it.

`data/taxonomy/` is gitignored. These three files carry no client data, but the
directory is where workbook extracts land, and a rule that depends on
remembering which file is safe is not a rule.

## Standards basis

Descriptions are written against employee assistance and workplace health
standards rather than composed freehand. Four bodies of source material carry
almost all of it.

**EAPA Core Technology** defines what an employee assistance programme is and
therefore what belongs in the service catalogue: consultation with and training
of organisation leadership, promotion of the service, confidential problem
identification and assessment, short-term intervention, referral with case
monitoring and follow-up, provider relations, benefits consultation, and
evaluation. Service descriptions cite the numbered item they implement. It is
also the reason three things stay out of the diagnosis taxonomy: an
intervention, a session outcome, and a delivery location are not clinical
findings.

**WHO guidelines on mental health at work (2022)** supply the evidence
strength for each intervention type, and they are quoted with their strength
and certainty rather than summarised as approval. Two matter most. Manager
training carries a strong recommendation on moderate-certainty evidence, which
makes it the best-evidenced service in the catalogue. Psychological debriefing
carries a strong recommendation against, which directly constrains how
`Trauma Group Counselling` may be delivered.

**WHO's mental health at work fact sheet** supplies the psychosocial risk
vocabulary. The work stress, career, change management and organisational
leaves are described in its terms, because a taxonomy that names the risk
factor produces reporting an employer can act on, and one that only names the
employee's distress does not.

**ICD-11** supplies the clinical anchor for the leaves that are genuine
disorders, and just as importantly it settles what is not one. Burn-out is an
occupational phenomenon and not a medical condition. Attention deficit disorder
is not a separate entity. Grief becomes a disorder only on duration and
impairment. Personality has one graded entity rather than subtypes.

## Editorial rules

1. **Say which rows are not diagnoses.** Most of this taxonomy records
   presenting problems, not disorders. Career stagnation, workplace politics
   and child bullying are real and reportable and are not conditions. Where a
   row is a presenting problem, the description says so, so nobody reads
   prevalence as clinical morbidity.
2. **Name the boundary with the neighbouring row.** Nearly every description
   states what moves a case to a different leaf or type. Conflict becomes
   abuse when fear and control are present. Career fatigue becomes burnout when
   all three ICD-11 dimensions are there. Family depletion is not burnout,
   because ICD-11 confines burn-out to the occupational context.
3. **Name the safety pathway where one exists.** Child abuse, gender-based
   violence, suicidal ideation and psychosis carry the action, not only the
   definition: protection duty, risk assessment and safety planning, or
   same-day escalation. A description that defines a risk without naming the
   response is not useful at the point of recording.
4. **Attribute every external claim in the row itself.** A counsellor reading
   the row sees where the figure or the recommendation comes from, without
   opening this document.
5. **Do not invent what the source does not carry.** `duration_minutes` and
   `max_participants` are null on all 20 services. No standard fixes them and
   the source data has no session end time, so they are contract or programme
   settings to be entered per tenant, not values to be guessed here.

## Rows that need a decision

Three rows describe something other than a clinical finding and are retained
only so existing records and legacy spellings keep resolving.

| Row | Problem | Recommendation |
| --- | --- | --- |
| `ADHD` / `ADHD_ASSESSMENT` | Names an intervention. The condition is `MENTAL_ILL_HEALTH` / `ADHD_CONDITION` | Add assessment to the service catalogue, then retire this row |
| `ADHD` / `ADHD_COACHING` | Names an intervention | Covered by `Coaching/Mentorship`, then retire this row |
| `TRAUMA` / `EMDR_INDICATED` | Names a treatment decision | Retire once the treatment plan has a field of its own |

One row is already retired in the payload. `MENTAL_ILL_HEALTH` / `PTSD`
duplicated `TRAUMA` / `TRAUMA_PTSD`, which split one condition across two
prevalence buckets. It ships with `is_active: false` rather than deleted,
because the taxonomy is versioned by design and a report rendered earlier must
still resolve the label it was built from.

Thirteen of the twenty services carry `category: null`. `ServiceCategory` has
no value for assessment or for psychoeducation, and category is what selects
the authorization for entitlement drawdown, so those sessions consume nothing.
Extending the enum is a product decision and needs a CHECK constraint change on
both `services.category` and `authorizations.service_category`.

## Verification note on ICD-11 codes

Definitions, classifications and prevalence figures below were read from the
WHO and ILO pages listed. The specific ICD-11 code numbers quoted in
descriptions (for example 6A05 for ADHD, 6B40 for PTSD, 6B42 for prolonged
grief disorder, 6C40 for disorders due to use of alcohol, QD85 for burn-out)
were taken from ICD-11 MMS reference listings rather than from the WHO ICD-11
browser directly. WHO's own burn-out statement, quoted above, does not print
the code. Confirm each code against the WHO ICD-11 browser before it appears
in any clinical document, referral letter or billing record. The classification
statements around them, which is what the descriptions rely on, are WHO-sourced
and were verified.

## References

Employee assistance standards

- EAPA, Standards and Professional Guidelines for Employee Assistance Programs,
  2010 edition: https://cdn.ymaws.com/eapassn.org/resource/resmgr/eapa_standards_and_professio.pdf
  The Core Technology text quoted in the service descriptions was read from the
  DC EAPA chapter's reproduction, since the PDF above did not render as text:
  https://www.dceapa.org/eap-core-technology
- EASNA, EAP terms, on the length of a brief counselling model:
  https://easna.org/pages/eap-terms

Workplace mental health

- WHO, Guidelines on mental health at work (2022), recommendations:
  https://www.ncbi.nlm.nih.gov/books/NBK586355/ and
  https://www.ncbi.nlm.nih.gov/books/NBK586381/
- WHO, Mental health at work, fact sheet:
  https://www.who.int/news-room/fact-sheets/detail/mental-health-at-work
- WHO, Burn-out an occupational phenomenon: International Classification of
  Diseases: https://www.who.int/news/item/28-05-2019-burn-out-an-occupational-phenomenon-international-classification-of-diseases
- ILO, Violence and harassment in the world of work, on Convention No. 190
  (2019): https://www.ilo.org/topics-and-sectors/violence-and-harassment-world-work

Clinical conditions

- WHO, Depressive disorder (depression), fact sheet:
  https://www.who.int/news-room/fact-sheets/detail/depression
- WHO, Suicide, fact sheet:
  https://www.who.int/news-room/fact-sheets/detail/suicide
- WHO, Schizophrenia, fact sheet:
  https://www.who.int/news-room/fact-sheets/detail/schizophrenia
- WHO, Bipolar disorder, fact sheet:
  https://www.who.int/news-room/fact-sheets/detail/bipolar-disorder
- WHO, Violence against women, fact sheet:
  https://www.who.int/news-room/fact-sheets/detail/violence-against-women
- WHO, Child maltreatment, fact sheet:
  https://www.who.int/news-room/fact-sheets/detail/child-maltreatment
- WHO, Guidelines for the management of conditions specifically related to
  stress (2013), on trauma-focused CBT and EMDR:
  https://www.ncbi.nlm.nih.gov/books/NBK159723/
- WHO, ICD-11 chapter 06, mental, behavioural or neurodevelopmental disorders,
  structure and groupings, as described in Reed et al., Mental, behavioral and
  neurodevelopmental disorders in the ICD-11:
  https://bmcmedicine.biomedcentral.com/articles/10.1186/s12916-020-1495-2

Figures quoted in descriptions carry the year WHO attaches to them: 15% of
working-age adults with a mental disorder and 12 billion lost working days at
about US$1 trillion from the mental health at work fact sheet; depression at
5.7% of adults and about 332 million people from 2021 Global Burden of Disease
data; more than 720,000 suicide deaths a year; schizophrenia at about 1 in 345;
bipolar disorder at about 1 in 200 as of 2021; intimate partner and non-partner
sexual violence at about 31.6% of women from WHO's 2023 prevalence estimates.

## Importing

Types first, then diagnoses, then services.

- Types and diagnoses are global reference data written by a platform admin.
  `POST /diagnoses/types` and `POST /diagnoses`, with `PATCH` for a row that
  already exists. Resolve `type_code` to the created `type_id` before posting a
  diagnosis. Deactivate `MENTAL_ILL_HEALTH` / `PTSD` rather than skipping it,
  so an existing row is retired rather than left selectable.
- Services are tenant-scoped, so `services.json` is a template applied once per
  tenant via `POST /services`, matched on `name`.

Dev first, verified against the database rather than the response: 16 types, 88
diagnosis rows with one inactive, and 20 service rows per tenant. Then
production.
