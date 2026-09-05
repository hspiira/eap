# Members module

The Members module represents people covered by a client's wellness programme:
client employees and their beneficiaries/dependants. It is not a general people
directory.

## Boundaries

- A member belongs to exactly one tenant and client.
- A beneficiary may reference an employee member from the same client only.
- A member does not need a User account. Portal access is an independent,
  invite-only workflow.
- Providers and counsellors use the Providers/panel workflow. Today this is
  backed by `/persons` records of type `ServiceProvider` with provider profiles;
  a separate organisation/practitioner persistence model is future work.
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
- Next-of-kin is a separate one-to-many contact workflow, excluded from the
  roster and CSV export. Contacts are scoped to the tenant and member; viewers
  can read but cannot change them. Concurrent primary-contact changes are
  serialized on the member row.

## API

The canonical tenant-facing API is `/members`:

- `GET /members` — tenant-scoped, paginated roster with client, relation,
  status, and search filters
- `POST /members` — create an employee or beneficiary without creating a user
- `GET/PATCH /members/{id}` — view/update current roster data
- `POST /members/{id}/suspend`, `/reinstate`, `/terminate` - roster lifecycle
- `GET /members/{id}/beneficiaries` - same-client employee relationships
- `GET/POST /members/{id}/next-of-kin` - list or add contacts
- `PATCH/DELETE /members/{id}/next-of-kin/{contact_id}` - update or remove contacts
- `GET /members/export` — filtered or selected-ID CSV export

The existing `/eligible-members` endpoints remain for clinical enrolment
compatibility. The older `/persons` API and route are retained temporarily for
existing provider and staff integrations while those boundaries are migrated.

Member mutations commit the member/contact and its audit outbox event in the
same transaction. Audit metadata records actor, resource and operation without
copying profile/contact values. Run the existing outbox worker to deliver those
events into audit logs. An audit write failure rolls back the member change.

Company member IDs must remain unique within a tenant/client. Updates cannot
make a member their own primary employee or convert an employee with linked
beneficiaries into a beneficiary. Reassign those beneficiaries first.

Export traverses all matching pages, deduplicates selected IDs, ignores
foreign-tenant IDs, and escapes spreadsheet formula prefixes.

## Compatibility retirement

Keep `/persons` until Providers/panel, counsellor assignment, the user-detail
person link, and other legacy person consumers have replacement contracts and
verified data migration. A person ID is not a member ID; do not blindly redirect
`/persons/{id}` to `/members/{id}`. Staff accounts continue through Platform Users
and the passwordless invitation option in the user form.

Account linking and clinical service history are not represented as placeholder
panels on the member detail page. Add them only when their real workflows and
authorization boundaries exist. Clinical history stays behind clinical scope.

## Verification

From `apps/api`, run the member route and domain tests with the unit suite. The
focused persistence tests require local PostgreSQL:

```bash
MEMBER_TEST_DATABASE_URL=postgresql+asyncpg://USER@localhost/postgres \
  .venv/bin/pytest tests/integration/test_members_persistence.py -q
```

They create and remove a uniquely named schema, without touching application
tables. They verify persisted writes, audit rollback, concurrent primary
contacts, tenant isolation and beneficiary filtering. Frontend interaction
tests cover the member list, detail page and both roster/contact forms.

## Privacy model

`eligible_members` is the employer-side identity record. Clinical records do
not reference it directly; continuity uses the existing pseudonymous
`eligible_member_clinical_link`. Any future duplicate merge must preserve that
link, emit an auditable reassignment, and prevent cross-tenant or cross-client
merges before it is exposed in the UI.
