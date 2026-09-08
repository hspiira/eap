# Members, practitioners and session pages: review and redesign proposal

Date: 2026-09-08. Scope: the standalone `/members` pages, the `/providers`
pages, and the `/service-sessions/$sessionId` detail page (with the list where
it constrains the detail). Method: code review of `apps/web` and `apps/api`
plus direct sampling of the dev database `evexia_db` (tenant
`jfj783wwafdgpvoz48snol6q`), which holds the client's real imported data per
`DEV_DATA_LOAD.md`.

Everything under "What exists" and "What the data shows" is verified against
code or the database, with citations. Everything under "Proposal" is design
judgement informed by that evidence; the product owner should confirm
terminology and priorities before implementation.

A deliberate goal of this proposal is that the three pages stop looking like
the same page three times. Today all three are near-identical flat tables
feeding near-identical two-column card grids. The data shapes are different
enough to justify three different treatments:

- Members is a high-volume roster (3,305 rows, thin per row): a directory
  with a master-detail split.
- Providers is a low-volume network in mid-onboarding (113 rows, most of the
  interesting state is readiness): a readiness-graded directory and a
  credentialing dossier.
- A session is a single event record with two very different shapes
  (company-wide event vs individual clinical session): an adaptive record
  page, not a fixed card grid.

## Data snapshot (dev DB, 2026-09-08)

| Fact | Value |
| --- | --- |
| `eligible_members` | 3,305 (3,303 Active, 1 Suspended, 1 Terminated; all relation Employee) |
| Member field fill | staff_number 3,301; gender 3,259; work_email 565; DOB 4; phone 2; personal_email 1; national_id 0; user_id 0; coverage dates 0 |
| Rosters | 5 clients only (Stanbic 2,043, DTB 679, I&M 329, KPMG 194, Minet 60); the activity log names 23 clients |
| `providers` | 113 (112 Pending, 1 Active); tier, region and gender set on exactly 1; specialty links 0; contact email or phone on roughly half |
| Provider affiliations | 43 providers affiliated across 13 organisations |
| `service_sessions` | 369, all Completed; 368 CompanyWide with no member, 1 Individual; delivery_context Unknown on 368 |
| Session field fill | client_type 365; session_number 364; rate_ugx 208; clinical_outcome 183; notes, duration, member, diagnosis 1 each; issue_topic, headcount, location 0 |
| Session mix | Group 286, Family 39, Couples 23, Individual 21; Physical 218, Online 151; Health Talk is 231 of 369 |
| Session spread | 35 clients, 33 providers (max 86 sessions for one provider, median 6); Aug 2024 to Aug 2026 |
| Waiting in staging | 6,444 session rows on member rosters, 637 with no counselor, 142 unmapped provider aliases, 109 NeedsReview practitioner rows |

The dev numbers matter because they are the client's own data. The pages will
launch looking like this, not like the fully populated ideal.

---

## 1. Members

### 1.1 What exists

List (`apps/web/src/routes/members/index.tsx`): a flat table of Member,
status icon, member code, relationship, client (plain text), work email,
personal email, phone. Filters for relationship and status, search, CSV
export, import, duplicate scan, bulk suspend/reinstate/terminate, admin merge
of exactly two rows. `client_id` is accepted as a URL filter but has no
visible control and no chip (`index.tsx:65,171,189`), so a deep link filters
silently.

Detail (`apps/web/src/routes/members/$memberId.tsx`): three tabs (Overview,
Service history behind clinical scope, Account access), four detail cards
(Membership, Personal details, Contact, Next of kin), a rail with beneficiary
links and lifecycle actions. Loading is a bare text line, not a skeleton
(`$memberId.tsx:46`). There is no at-a-glance rail, although the pattern
exists at `apps/web/src/components/clients/ClientDetailWidgets.tsx:361-414`.

The client detail page already contains a better members UI: the roster tab's
master-detail split (`apps/web/src/components/clients/ClientManagementPanels.tsx:214-321`)
with a row-click summary card, humanized labels via `getStatusLabel()`, and a
clear-filters button. The standalone `/members` page got none of that pass
(`MEMBERS_MIGRATION.md:143-145`) and still renders raw enum values such as
`DomesticPartner` (`index.tsx:502`).

### 1.2 What the data shows

- Columns for phone (2 of 3,305), personal email (1) and DOB (4) spend prime
  list real estate on empty cells. Work email is filled on 17 percent.
- `staff_number` is filled on 3,301 of 3,305 and is the identifier HR teams
  quote, yet it appears nowhere on the list or detail, only inside the edit
  form, and list search does not match it
  (`eligible_member_repository.py:150-161` searches five other columns).
- The API returns `staff_number`, `national_id`, `passport_number`,
  `last_imported_at`, `suspended_at`, `terminated_at`, `created_at`,
  `user_id` (`member_schemas.py:138-163`); none is rendered on list or
  detail. The CSV export shows more member data than the screen does
  (`members.py:501-518`).
- Relation breakdown counts already exist server-side per client
  (`GET /clients/{id}/stats`, `client_schemas.py:339-353`) but nothing
  tenant-wide exists for the members workspace.
- `is_currently_eligible()` (`eligible_member.py:189-197`) is computed on the
  entity and never serialized anywhere.

### 1.3 Proposal: roster directory with a master-detail split

Implemented on 2026-09-08 in commits `911201b` (API) and `54c456b` (web).
What shipped differs from the proposal below in two places: the summary strip
hides status counts that are zero, and the client link in the table was added
despite a prior test asserting the row carried a single link, because reaching
the employer without a detour is worth the second target. Both are noted where
the tests were updated.

List. Promote the proven `ClientRosterPanel` split to the standalone page: the
table on the left, a row-click summary card on the right, "Open full profile"
to navigate. Re-rank columns by actual data density: Member, status icon,
member code, staff number, client (as a link, and as a visible filter chip
with a client picker control), relationship (humanized). Drop phone, personal
email and DOB from the table into the summary card and detail page; keep work
email as the single contact column. Add a summary strip above the filter bar:
total, active, suspended, pending, terminated, and members per client. That
strip needs one small backend addition (a `GET /members/stats` rollup); until
then the strip can show the filtered `total` only.

Keep the settled interaction decisions the tests encode
(`members-list.test.tsx`): status stays an icon with an accessible label, row
actions stay behind the ellipsis, merge stays admin-only at exactly two
selected.

Detail. Give the page the at-a-glance rail the client page already has:
member since (`created_at`), last roster import (`last_imported_at`), account
linked yes/no, beneficiary count. Add an Identification card (company ID
number, national ID, passport number) so what the form collects can be read
back without opening the edit sheet. Add a small status history block from
`suspended_at` and `terminated_at`. Replace the bare loading text with the
`DetailSkeleton` used elsewhere. Coverage dates stay off the page per the
recorded policy (`MEMBERS_MODULE.md`), but see open question Q1.

Backend touches needed: search over `staff_number`, a tenant-level member
stats rollup, nothing else. Everything else is frontend.

### 1.4 Quick fixes independent of the redesign

- Humanize relation values on the list with `getStatusLabel()`.
- Give the `client_id` filter a visible control and chip.
- Skeleton on detail loading.

---

## 2. Providers

### 2.1 What exists

List (`apps/web/src/routes/providers/index.tsx`): a flat table of
Practitioner, Tier, Region, Panel, Accreditation, Email, Phone, Account, with
four single-value filters (tier, region, panel, accreditation), search, and
admin bulk activate/deactivate/suspend/reactivate. Region renders the raw
enum (`KampalaMetro`), and the tier badge falls back to the text
"Unassessed".

Detail (`apps/web/src/routes/providers/$providerId.tsx`): a status chip row,
then tabs Overview (practitioner card, panel and accreditation panel with
admin commands, specialties panel, linked account, conditional licence card),
Affiliations, Non-compete, Sessions (a four-column recent list with no
totals).

### 2.2 What the data shows

- 112 of 113 providers are Pending with null tier, null region, no
  specialties and Pending panel and accreditation. The current list therefore
  renders three of its eight columns as "Unassessed", blank, and two Pending
  hourglasses on nearly every row. The columns describe a steady state the
  network is not in.
- The interesting per-provider state right now is readiness: what blocks each
  practitioner from being bookable. A complete, shared rule for that already
  exists with stable failure codes (`provider_eligibility.py`, exposed at
  `GET /panel/{id}/eligibility`), and the frontend never calls it.
- The engagement-document checklist (7 kinds, Present/Missing/Open plus note,
  `provider_engagement_document_model.py:16-40`) was built for exactly this
  onboarding phase and has no UI at all.
- The API returns `identity_provenance`, `created_at`/`updated_at`, supports
  a record-status filter, a `has_account` filter, repeatable multi-value
  filters, and a bulk panel-status endpoint; the UI uses none of them
  (providers report, section 3.3).
- No per-provider aggregate exists anywhere: the Sessions tab prints the
  fetched page length as "{n} recent sessions" (`SessionHistory.tsx:94`),
  which is wrong the moment a provider passes 20 sessions (the busiest has
  86).
- 33 of 113 providers have delivered sessions; attribution is stored on the
  session (`delivery_context`, `provider_affiliation_id`) and shown nowhere
  on the provider's own pages.
- `ProviderPicker` renders "null · null" as the secondary line for the 112
  unassessed practitioners (`EntityPicker.tsx:376-409`).

### 2.3 Proposal: readiness-graded directory and a credentialing dossier

List. Reframe the page around bookability rather than a uniform table.
A segmented header splits the network into Bookable, In onboarding, and
Blocked (suspended or removed panel, inactive record), with counts; selecting
a segment filters the table. Replace the Tier and Region columns (null on
112 of 113) with a Readiness column driven by the eligibility failure codes
(for example "3 of 5 checks passing"), and a Sessions delivered column once a
small aggregate endpoint exists. Move tier and region into the row's detail
where they remain as facts to complete. Add the record-status and
has-account filters the API already supports, and let each filter take
multiple values, matching the API. Fix region label rendering with
`getStatusLabel()`. Switch bulk panel actions to the existing
`PATCH /panel/bulk-panel-status` endpoint instead of looping per id.

Detail. Turn the page into a credentialing dossier, since that is the work
the team actually has (53 practitioners need a profession, tier and region
before any can be booked, per `DEV_DATA_LOAD.md`):

- A readiness rail, top right: the live result of
  `GET /panel/{id}/eligibility`, each failing check named in plain language
  with a link to the command that clears it (change tier, record
  accreditation, set region, and so on). This replaces the current
  undifferentiated chip row.
- An engagement documents card: the seven document kinds as a checklist with
  Present/Missing/Open and the note, admin-editable through the existing
  PUT endpoint. New UI, zero new backend.
- A delivery record tab replacing the bare Sessions tab: total delivered,
  first and last session date, split by delivery context and organisation,
  then the recent list. Needs one aggregate endpoint
  (`GET /providers/{id}/delivery-stats` or equivalent).
- Provenance shown quietly: `identity_provenance` and, where the provider
  came from an import batch, a link to the batch row (data exists in
  `practitioner_import_rows.imported_provider_id`).
- An activity tab using `auditApi.getEntityHistory`, which exists and has
  zero call sites; every provider mutation is already audited with a reason.

Backend touches needed: one delivery-stats aggregate. The readiness rail,
documents card, provenance and activity tab are all existing endpoints.

### 2.4 Quick fixes independent of the redesign

- `getStatusLabel()` for region on list and picker; stop rendering
  "null · null" in `ProviderPicker` (fall back to "Unassessed").
- Expose the record-status filter.
- The alias review queue and practitioner import remain deliberately without
  UI (`PROVIDERS_FRONTEND.md:301-316`); this proposal does not reopen that
  decision, but the 142 unmapped aliases and 109 NeedsReview rows recorded in
  `IMPORT_REVIEW_UI_GAP.md` will eventually force it.

---

## 3. Session details

### 3.1 What exists

Detail (`apps/web/src/routes/service-sessions/$sessionId.tsx`): a hero band
(date, service, member, status, an "Encrypted record" chip), tabs Overview,
Feedback, History, and a rail with two stats (Duration, Feedback), linked
tiles, and lifecycle actions. Overview shows five cards: Schedule, Notes,
Subject, Service and practitioner, Clinical (a single diagnosis row).

### 3.2 What the data shows

- 368 of the 369 real sessions are company-wide events with no member. For
  every one of them the Subject card renders "Loading member…" forever
  (`$sessionId.tsx:313-315`); the acceptance criterion that the detail page
  renders member-less sessions properly (`SESSIONS_IMPLEMENTATION.md:163-164`)
  is unmet.
- The page hides most of what the record holds. Returned by the API and
  typed on the frontend but absent from the detail page: `attendance`,
  `client_name`, `session_type`, `category`, `client_type`, `rate_ugx`,
  `issue_topic`, `headcount`, `session_number`, `clinical_outcome`,
  `cancellation_reason`, `reschedule_count`, `partner_name`,
  `partner_relationship`, and the session's own `duration`. The rail's
  Duration stat reads `service.duration_minutes` instead of
  `session.duration` (`SessionDetailWidgets.tsx:117-120`).
- In the real data those hidden fields are the filled ones: client_type on
  365, session_number on 364, rate on 208, clinical_outcome on 183, while
  notes, diagnosis and member (the fields the page is built around) are
  filled on 1 each.
- The History tab is a hard-coded empty state (`$sessionId.tsx:405-410`)
  although every session mutation is audited with clinical values redacted
  (`audit_event_handler.py:49-83`) and `auditApi.getEntityHistory` exists
  unused. Cancellation reasons and status transitions are already in the
  audit stream.
- The detail endpoint returns null display names (`_one` skips the name
  reader, `service_sessions.py:250-254`), which is why the page issues three
  extra queries.
- `GET /service-sessions/{id}` requires tenant membership only; no session
  read requires the clinical scope, and no read event is logged
  (`authorization.py:425-445`). The hero's "PHI, access logged" copy is not
  backed by a read-logging mechanism. Notes, issue topic and partner name
  are encrypted at rest, so the chip's encryption half is true.

### 3.3 Proposal: an adaptive event record

One page, two shapes, switched on `attendance`. This is the clearest
opportunity to stop being monotonous, because the record itself is not one
kind of thing.

Company-wide shape (the dominant one in the data):

- Hero: service name and client as the identity ("Health Talk at Stanbic
  Bank"), date, mode badge (Physical/Online), category badge, status.
  No Subject card at all.
- An engagement card: headcount (currently never captured; Phase D of
  `SESSIONS_IMPLEMENTATION.md` already proposes requiring it), session
  number, client type (new or repeat engagement), rate.
- Delivery card: practitioner, delivery context, organisation when
  attributed, location.
- Outcome card: clinical_outcome (filled on half the real rows today),
  service, feedback.

Individual shape:

- Hero keeps the member as the subject.
- The clinical card grows into what the model supports: outcome, issue
  topic, diagnosis type and diagnosis, partner name and relationship for
  couples and family sessions, the case drawdown result. Clinical fields
  should be gated on the clinical scope in the UI, and see Q2 on the API.
- Notes and feedback as today, but notes edited in a textarea, not the
  single-line input the form sheet currently uses
  (`ServiceSessionFormSheet.tsx:614`).

Both shapes:

- Rail stats that reflect the record: the session's own duration, reschedule
  count, session number, rate.
- History tab wired to `auditApi.getEntityHistory("ServiceSession", id)`,
  rendering field names, actors and timestamps; values arrive already
  redacted, so nothing clinical leaks. Show the cancellation reason and
  reschedule history here.
- Hydrate names on the detail endpoint by passing the existing
  `SessionNameReader` to `_one`, removing three client-side queries.
- Import provenance line for imported sessions once the row link is exposed
  (the only durable link is `session_import_rows.imported_session_id`; a
  small read endpoint would be needed, or the provenance columns proposed in
  `DEV_DATA_LOAD.md` before a production load).

### 3.4 Quick fixes independent of the redesign

- List Export button and row-menu Cancel item have no handlers
  (`index.tsx:212`, `:571-573`): wire or remove.
- The list search box sends a `search` param the server ignores; either
  implement it or remove the box until it works.
- Add the counsellor filter the API already supports (`provider_id`).
- Fix the rail Duration source and the reschedule handler defects
  (`$sessionId.tsx:104-118`).
- Reconcile the "PHI, access logged" chip with reality: either implement
  read logging or soften the copy to "Encrypted at rest".

---

## 4. Cross-cutting

Small backend work the redesigns depend on, in priority order:

1. Session detail name hydration (pass the name reader in `_one`). Trivial.
2. Member search over `staff_number`. Trivial.
3. Tenant-level member stats rollup for the roster summary strip.
4. Per-provider delivery stats (total, first/last date, by context).
5. Session list free-text search, or removal of the search box.

Existing but unused endpoints the redesigns consume with no backend change:
`GET /panel/{id}/eligibility`, `GET /providers/{id}/engagement-documents`,
`GET /audit/entity/{type}/{id}`, `PATCH /panel/bulk-panel-status`,
multi-value and status filters on `GET /providers`.

## 5. Product owner answers, 2026-09-08

The four open questions were answered by the product owner. Recorded here as
decisions, with what each one changes.

**Q1, coverage windows: reopened.** The closed policy that coverage is
invisible in the member API is withdrawn. `coverage_start`, `coverage_end` and
the computed `is_currently_eligible` are now on `MemberResponse` and shown in
the member profile's at-a-glance rail. Coverage stays read-only in the member
API: it is still set at the client or programme level and by `terminate()`,
and it is not a member form field. Implemented in commit `911201b`, recorded
in `MEMBERS_MIGRATION.md` and `apps/api/docs/MEMBERS_MODULE.md`.

Consequence with the current data: no member carries a `coverage_start` and
one carries a `coverage_end`, so `is_currently_eligible` reduces to "status is
Active" for the whole roster. That is correct behaviour, not a defect, because
the domain method skips a bound that is not set.

**Q2, session read access: gate and log clinical reads.** The owner's answer
was to encrypt the clinical fields. Note that `notes`, `feedback`,
`issue_topic` and `partner_name` are already encrypted at rest with a
tenant-keyed cipher (`service_session_mapper.py:77-90`), so encryption is not
the open half of this question. What remains open, and what the answer is
taken to mean, is that clinical session content should not be readable by any
same-tenant user: `GET /service-sessions/{id}` and the list should require the
clinical scope for the clinical fields, and reads should be logged so the
"PHI, access logged" chip is true. Scope: the sessions track, not this one.
This restatement should be confirmed by the product owner before it is built.

**Q3, vocabulary: confirmed with corrections.** These are the counselling
team's words, with the mapping made explicit: "Intervention" is the service,
"Mode" is mode of delivery (Online or Physical), "Counsellor" is the
practitioner. The session pages should use "Service", "Mode of delivery" and
"Practitioner" where they currently echo the workbook, and `SESSIONS_REVIEW.md`
can close its open vocabulary question against this. Scope: the sessions
track.

**Q4, provider onboarding duration: no decision needed yet.** The question was
whether the readiness framing should be permanent. It does not need answering
before the provider work starts: the readiness segmentation is correct for the
current network (112 of 113 practitioners are Pending with no tier or region)
and stays useful afterwards. Revisit whether tier and region earn their table
columns back once most practitioners are bookable; nothing blocks on it now.

Findings recorded here that belong to other tracks and are not expanded on:
the taxonomy admin gap (`TAXONOMY_MANAGEMENT_GAP.md`), the per-row session
import review gap (`IMPORT_REVIEW_UI_GAP.md`), and the 93 remaining silent
mutators (`AUDIT_COVERAGE.md`).
