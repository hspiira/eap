# Members module

The Members module represents people covered by a client's wellness programme:
client employees and their beneficiaries/dependants. It is not a general people
directory.

## Boundaries

- A member belongs to exactly one tenant and client.
- A beneficiary may reference an employee member from the same client only.
- A member does not need a User account. Portal access is an independent,
  invite-only workflow.
- Providers and counsellors belong to provider organisation/practitioner
  workflows, even when an individual provider is a person.
- Tenant/platform staff belong to Users & Invitations.
- Employment history is intentionally out of scope. `employer_member_id` is
  the company/client-supplied external member ID; optional contact/display,
  DOB, gender, and phone fields are current-roster profile data.
- Coverage is configured at the client/company or programme level; it is not a
  member form field. The legacy `eligible_members` storage still contains
  coverage columns for compatibility and import flows.
- Government identifiers such as NIN or passport are not represented by a
  generic `external_id`. If they become operationally necessary, add a
  restricted identity model with an explicit identifier type, access policy,
  retention, and audit trail.
- Next-of-kin is intentionally not embedded in the member row. It should be a
  separate one-to-many restricted contact workflow that can support primary
  and alternate contacts and protect those details from ordinary roster views.

## API

The canonical tenant-facing API is `/members`:

- `GET /members` — tenant-scoped, paginated roster with client, relation,
  status, and search filters
- `POST /members` — create an employee or beneficiary without creating a user
- `GET/PATCH /members/{id}` — view/update current roster data
- `POST /members/{id}/suspend` and `/reinstate` — eligibility lifecycle
- `GET /members/export` — filtered or selected-ID CSV export
- `GET /members/duplicates` — read-only duplicate candidates for review

The existing `/eligible-members` endpoints remain for clinical enrolment
compatibility. The older `/persons` API and route are retained temporarily for
existing provider and staff integrations while those boundaries are migrated.

## Privacy model

`eligible_members` is the employer-side identity record. Clinical records do
not reference it directly; continuity uses the existing pseudonymous
`eligible_member_clinical_link`. Any future duplicate merge must preserve that
link, emit an auditable reassignment, and prevent cross-tenant or cross-client
merges before it is exposed in the UI.
