# Members module

The Members module represents people covered by a client's wellness programme:
client employees and their beneficiaries/dependants. It is not a general people
directory.

## Boundaries

- A member belongs to exactly one tenant and client.
- A beneficiary may reference an employee member from the same client only.
- A member does not need a User account. An administrator may explicitly link
  one existing tenant user to one member; the link grants no role or access
  scope and never matches on name or email.
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
- `GET /members/{id}/sessions` - clinical-scope service history
- `PUT/DELETE /members/{id}/account` - admin-only explicit User linkage
- `POST /members/{id}/merge` - admin-only reviewed merge into the path member
- `GET/POST /members/{id}/next-of-kin` - list or add contacts
- `PATCH/DELETE /members/{id}/next-of-kin/{contact_id}` - update or remove contacts
- `GET /members/export` — filtered or selected-ID CSV export

The existing `/eligible-members` endpoints remain for clinical enrolment
compatibility. The `/persons` API remains provider and care-callback
infrastructure. Its product-facing list redirects to Providers, and tenant
staff are managed only through Users & Invitations.

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

Client detail uses the Members roster, including employees and beneficiaries,
with a searchable, paginated roster, relationship/status filters and the full
server count. Contextual creation preselects the client and refreshes the roster
and client list. Viewers have read-only access. Existing `tab=staff` links still
open the renamed Members tab.

The client list's Employees column counts canonical employee members across
all roster statuses, excluding beneficiaries. The response keeps the existing
`staff_count` field for compatibility. Legacy Persons records are not included;
identity migration remains separate work.

Operational `service_sessions` now use `member_id -> eligible_members.id` for
the client subject; `provider_id -> persons.id` remains unchanged. Session
creation checks all referenced records against the current tenant and rejects
non-provider Persons as providers. The session forms, lists, detail view and
history links resolve Members directly, without requiring User accounts.

Migration `a7c9e1f3b5d7` is deliberately an empty-table cutover. Both directions
refuse to run if any service sessions exist. The current environment has no
legacy sessions, so there is no Person/Member bridge or compatibility read to
maintain. Do not run it against a populated deployment without a separately
reviewed, tenant/client-scoped identity mapping and data migration.

Historical import validation accepts `member_code` and produces `member_id`.
Mappings are nested by canonical client ID, then company member code. The CLI
remains validation-only; it neither creates Members nor persists sessions.
Person DSAR exports include sessions in which that Person is the provider,
not sessions belonging to an unrelated Member with a coincidentally equal ID.

The `/persons` API and detail compatibility route can be removed only after two
remaining consumers move: provider records need an independent practitioner
contract, and care callbacks need a canonical Member subject. A person ID is
not a member ID, so the detail route is not redirected blindly. Staff accounts
no longer read or link legacy Person profiles.

Member detail exposes persisted account linkage and service history. Only
administrators can link accounts or merge records, and clinical history stays
behind clinical scope. Merging requires two explicitly selected members in the
same tenant, client and relationship context; it transfers dependent and
clinical continuity references atomically and audits both records.

## Verification

From `apps/api`, run the member route and domain tests with the unit suite. The
focused persistence tests require local PostgreSQL:

```bash
MEMBER_TEST_DATABASE_URL=postgresql+asyncpg://USER@localhost/postgres \
  .venv/bin/pytest tests/integration/test_members_persistence.py -q
```

They create and remove uniquely named schemas, without touching application
tables. They verify persisted writes, audit rollback, concurrent primary
contacts, tenant isolation, beneficiary filtering, and the account-link
migration. Frontend interaction tests cover the member list, detail page,
account workflow, and roster/contact forms.

## Privacy model

`eligible_members` is the employer-side identity record. The operational
`service_sessions` workflow references it directly. The separate clinical
case/session workflow retains pseudonymous continuity through
`eligible_member_clinical_link`. The reviewed merge preserves the surviving
link, reassigns clinical records in one transaction, emits audit events for the
survivor and removed duplicate, and rejects cross-tenant or cross-client input.
