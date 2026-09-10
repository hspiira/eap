# Wellness nugget emails: delivery and delegation decision

Research date: 2026-09-07. Repository baseline: `81eb847`.

Status: recommendation and implementation gates documented. No Dynamics tenant
was inspected, integration executed, email sent, or application feature built.
Public documentation establishes feasibility, not availability or successful
operation in our specific Microsoft environment.

## Recommendation

**Adopt the hybrid direction: prepare nuggets, maintain client recipients, and
plan dates in EAP; use Dynamics 365 Customer Insights - Journeys to send and
track them. Fund a bounded integration proof first, then build only the supported
workflow it establishes. The wellness officer, using an Admin account, owns
routine preparation and scheduling.**

I accept bringing content preparation, recipient maintenance, dates, and client
visibility into EAP. I reject building a replacement email delivery
platform for wellness nuggets alone. That would add software and operational
responsibilities before proving that the current problem needs new software.

This is an engineering and workflow judgment, based on the capabilities and
repository evidence below. The programme owner should confirm the operational
fit; the Dynamics administrator must verify environment capabilities and access;
finance must confirm costs. These are separate decisions.

The immediate objective is that the wellness officer can prepare and schedule
the month, and update a client's recipients, without the owner operating
Dynamics or remembering send times. A new screen that leaves the owner doing
those steps would not achieve that objective.

Decision update following the owner's clarification: the initial preference
for Dynamics-only process improvements is replaced by a narrow EAP integration.
The reason is the combined need for email preparation, date management, and
recipient maintenance within client records. Dynamics-only and low-code options
remain interim/fallback choices, not prerequisites for accepting that direction.

## What is known and what remains unknown

The owner reports:

- About 133 recipients across about 40 clients. These are reported operating
  figures, not counts independently verified in Dynamics.
- The tedious steps are setting up emails, setting up journeys, remembering
  times, and updating a client's recipients in the recipient list.
- Sends occur on weekdays selected by the wellness officer and on public
  holidays. This does not establish a daily weekday cadence.
- The wellness officer will be an Admin and should run this work.
- Preparation should happen here while Dynamics remains the sender because
  its sending is experienced as faster and it provides tracking. No comparative
  delivery-speed benchmark was performed in this review.

We still need the exact cadence, content format, whether clients share dates
and content, actual licence costs, and measured monthly effort. We have not established
whether recipients are client HR contacts who forward messages, employees,
distribution lists, or some combination. Their audience and reporting needs
are materially different.

Working assumption for this recommendation: Dynamics remains available and its
existing sender, audience, and consent configuration can continue to be used.
This is not a claim that those configurations have been audited or are correct.

## What Microsoft actually supports

### Simpler scheduling already exists

Customer Insights - Journeys offers a workflow from the email editor that can
schedule a message for later and select a published segment. It creates the
journey in the background. A feature switch may need enabling. It supports
limited scenarios: contact/lead audiences, default recipient addresses, and
restrictions on personalization. Business-unit ownership is not automatically
carried over, and the workflow does not prevent every cross-business-unit
selection. Use the full journey editor when those limitations matter.
[Microsoft: send now and schedule for later](https://learn.microsoft.com/en-us/dynamics365/customer-insights/journeys/email-without-journey).

Repeating segment journeys also exist: segment members enter again at the
configured interval. This is useful for repeated workflows.
[Microsoft: journey start configuration](https://learn.microsoft.com/en-us/dynamics365/customer-insights/journeys/journey-start).

Design implication: recurrence does not itself select a different approved
nugget each week. For changing content or irregular dates, use explicit dated
editions. Do not solve calendar work by repeatedly sending the same email.

### A supported integration is possible

Microsoft documents
`POST /api/data/v9.2/msdynmkt_CreateJourneyFromTemplate`. It can use a template
or existing journey, substitute segment/email references, set future start/end
times, and create in Draft or Publish mode. It returns a journey ID, validation
result, and errors. Required privileges and business-unit access apply. Draft
validation is weaker than publish validation. A timeout can leave a journey
created despite an uncertain response, and the API cannot remove journey
elements. Microsoft also identifies `msdynmkt_PublishJourneyV2` for publishing.
[Microsoft: Create Journey From Template API](https://learn.microsoft.com/en-us/dynamics365/customer-insights/journeys/developer/create-journey-template-api).

This is sufficient public evidence to justify a small integration proof. It is
not evidence that email authoring, every journey edit, stopping a published
journey, or all reporting can be automated with the same API. Verify those
capabilities separately before presenting an end-to-end feature as complete.

### Email preparation is the main unresolved technical gate

EAP can provide a constrained content form and render a reusable branded email.
However, this review did not find a Microsoft-documented end-to-end real-time
email creation and publication API contract equivalent to the journey API.
That is an unresolved support question, not evidence that it is impossible.
Generic Dataverse record access must not be mistaken for validated marketing
email publication.

The integration proof must establish the supported path for creating a draft,
setting content and assets, preserving Dynamics personalization and preference
links, validating it, and making it ready for a journey. Confirm the real-time
email table and actions with environment metadata and Microsoft support where
documentation is insufficient. Do not copy legacy outbound-marketing endpoints
or manipulate status fields to bypass publication.

Microsoft documents HTML snippet import in the real-time email editor, but
custom sections lose compatibility processing and do not support dynamic
content/personalization tokens. This is a possible officer-operated fallback,
not an automatic API handoff or a guarantee of rendering correctness.
[Microsoft: real-time email HTML controls](https://learn.microsoft.com/en-us/dynamics365/customer-insights/journeys/email-creation-with-html-edits).

If automated email publication cannot be supported, EAP preparation plus a
Dynamics finalisation step is an explicitly partial solution. Measure that
remaining work before accepting it. Do not call journey-only automation a
complete fix for the owner's email-setup problem.

### Recipient maintenance has documented building blocks

Dataverse documents contact creation and updates through its Web API. Real-time
Journeys separately documents segment creation, publication, and adding or
removing static members. Those are usable integration building blocks; the
environment's existing contact and audience model still needs mapping.
[Microsoft: contact CRUD](https://learn.microsoft.com/en-us/power-apps/developer/data-platform/webapi/web-api-basic-operations-sample),
[Microsoft: real-time segment API](https://learn.microsoft.com/en-us/dynamics365/customer-insights/journeys/real-time-marketing-api-segment).

Custom triggers are another supported way for external systems to initiate
journeys. They need trigger configuration and integration; the generated
ingestion key requires protection.
[Microsoft: custom triggers](https://learn.microsoft.com/en-us/dynamics365/customer-insights/journeys/real-time-marketing-custom-triggers).

Decision: prefer dated segment journeys for a newsletter schedule. Per-recipient
triggers introduce identity mapping and dispatch work that this requirement
does not yet justify. Reconsider them for event-driven communications later.

### Low-code automation is a legitimate alternative

Power Automate can execute Dataverse unbound actions. The Dataverse connector is
classified Premium. Whether existing licences cover the proposed flow must be
checked against the actual entitlement and use case.
[Microsoft: unbound actions](https://learn.microsoft.com/en-us/power-automate/dataverse/bound-unbound),
[Microsoft: Dataverse connector](https://learn.microsoft.com/en-us/connectors/commondataserviceforapps/).

A team-maintained planning list plus an approval flow calling the journey API
is therefore a candidate to prototype, not a verified ready-made solution in
our tenant. If it removes the work, prefer it over another custom module. Assign
a technical owner and backup so it does not become a flow tied to one employee.

### Retaining Dynamics preserves useful delivery capabilities

Dynamics evaluates contact-point consent for the configured purpose and topic
immediately before sending. Enforcement can be restrictive, nonrestrictive, or
disabled. Tracking has its own consent configuration. A contact record is not
proof of permission to email. Microsoft warns that a missing address or
preference link can produce a warning rather than block sending.
[Microsoft: consent management](https://learn.microsoft.com/en-us/dynamics365/customer-insights/journeys/real-time-marketing-email-text-consent).

It also maintains suppression lists for bounces and complaints, and supports
sender-domain authentication. These are existing platform capabilities we
would continue using, subject to checking our configuration. They do not
guarantee inbox delivery.
[Microsoft: suppression lists](https://learn.microsoft.com/en-us/dynamics365/customer-insights/journeys/suppression-lists),
[Microsoft: domain authentication](https://learn.microsoft.com/en-us/dynamics365/customer-insights/journeys/domain-authentication).

Quiet-time rules can defer messages beyond the requested start time, using a
journey or audience time zone.
[Microsoft: quiet times](https://learn.microsoft.com/en-us/dynamics365/customer-insights/journeys/real-time-marketing-quiet-times).

Operational implication: the calendar should distinguish planned time from
actual delivery. Agree a delivery window, not an exact inbox-arrival promise.

## Options, gains, and costs

### Option A: improve and delegate the existing Dynamics process

**Use as the interim process.** Standardize the template, audience segments, planning
sheet, permissions, and handoff. Trial Schedule for later for simple emails.

Gains: quickest route to removing the owner from routine operation; preserves
current email assets, delivery history, and recipient preferences; no new
application runtime to support.

Costs and limits: staff still learn Dynamics; the interface may remain awkward;
complex approvals and client calendars may still require coordination outside
the sender. Content production remains work for someone.

This can offload work immediately, but does not satisfy the requested EAP-based
recipient and content workflow. Keep it available during integration development.

### Option B: a low-code planning and approval workflow

**Fallback if the custom integration is not worth its cost.** Use an existing team planning
surface and a managed Power Automate flow to prepare approved journey requests.

Gains: can automate repeated setup without adding a new EAP frontend; may suit
the team's existing Microsoft skills.

Costs and limits: licensing needs verification; action availability and error
handling need a sandbox proof; operational ownership, duplicate prevention,
permissions, and change control still require engineering attention. It is not
automatically cheaper merely because it uses a visual flow editor.

### Option C: EAP calendar and approval workflow, Dynamics delivery

**Adopted direction, subject to the technical proof.** EAP manages draft content,
client recipient assignments, dated editions, and scheduling requests. Dynamics
continues to own published sendable assets, consent enforcement, and delivery.

Gains: one client-facing operational context for the team; reusable date rules;
batch planning; visible ownership and missing approvals; audited handoff; less
journey setup once the integration is proven.

Costs and limits: two systems and their permissions must remain aligned; API and
template changes need maintenance; Dynamics charges remain; the content-to-email
API handoff is not yet proven. External edits can invalidate EAP's approval record.
This is a controlled integration, not the disappearance of Dynamics.

### Option D: move to another managed newsletter platform

**Reconsider if Dynamics is retained only for nuggets or its removable cost is
material.** A dedicated newsletter product may already cover the workflow. For
example, Brevo documents campaign scheduling and user permissions. This makes it
a candidate for evaluation, not a selected vendor or verified fit.
[Brevo: campaigns](https://help.brevo.com/hc/en-us/articles/4413566705298-Create-and-send-an-email-campaign),
[Brevo: user permissions](https://help.brevo.com/hc/en-us/articles/360001079439-Add-users-and-assign-permissions-in-Brevo).

Potential gains: less dependence on Dynamics and possibly lower total cost.
Costs: migrate templates and preferences, reconcile suppressions, validate domain
setup and delivery, retrain staff, and accept a different reporting model. Pricing,
data location, required permission granularity, and contractual fit are unverified.
Evaluate buying this capability before building it.

### Option E: EAP owns campaigns and uses an email transport API

**Reject for the current scope.** A managed transport such as Amazon SES can
send email and expose delivery, bounce, complaint, and subscription events.
It does not prove that our team workflow is implemented.
[AWS: event notifications](https://docs.aws.amazon.com/ses/latest/dg/monitor-sending-activity-using-notifications.html),
[AWS: published event data](https://docs.aws.amazon.com/ses/latest/dg/event-publishing-retrieving-sns-contents.html).

Potential gains: control of the experience and less dependence on Dynamics.
Costs: the team must own scheduling, consent integration, preference handling,
event processing, content rendering, suppression behaviour, support, and
operational recovery. Cheap transport does not establish cheap ownership.

Do not substitute a shared Outlook mailbox or Microsoft Graph mailbox sending
loop for a campaign platform. Microsoft directs Exchange Online customers with
bulk commercial newsletters toward specialist providers.
[Microsoft: Exchange Online sending limits](https://learn.microsoft.com/en-us/office365/servicedescriptions/exchange-online-service-description/exchange-online-limits#sending-limits).

## What EAP already provides

The repository has useful foundations, but no verified newsletter feature:

- Client contact records contain tenant/client identity and email information:
  `apps/api/app/domain/entities/contact.py:17`. They do not contain the
  subscription-purpose model needed to establish campaign eligibility.
- Client contact management exists in
  `apps/web/src/components/clients/ClientManagementPanels.tsx:64`.
  The standalone contacts route remains a coming-soon screen at
  `apps/web/src/routes/contacts.tsx:11`.
- A persistent outbox dispatcher has retries:
  `apps/api/app/application/services/outbox_dispatcher.py:44`. The worker
  registers an audit consumer at `apps/api/scripts/outbox_worker.py:47`.
  This establishes a reusable pattern, not a proven email scheduler. Its
  dispatch loop invokes every registered consumer; do not attach external
  sending to it without routing, isolation, and duplicate-delivery analysis.
- Indexed backend searches for Dynamics/Dataverse and common email sender or
  scheduling integrations returned no matches across 672 indexed files.
  This is scoped search evidence, not proof that no external infrastructure
  exists. No deployment configuration or running mail service was audited.

Do not treat member rosters, clinical contacts, client HR contacts, user accounts,
and newsletter subscribers as interchangeable. The existing member/provider
migration identity rules continue to apply.

`docs/reviews/MODULES_REPAIR_PLAN.md` records access-control and frontend
isolation findings against an earlier baseline. Revalidate and close relevant
findings before a new module can schedule external communication. This research
did not rerun that audit or assert which issues remain in today's deployment.

## Team operating model to adopt first

These are recommended operating decisions, not claims about current staffing.

1. Assign the wellness officer as the monthly Admin operator and name a backup.
   Both use individual accounts with appropriate permissions.
2. Assign a content owner to prepare approved nuggets and maintain the content
   library. An appropriate wellness reviewer checks the material before use.
3. Let the wellness officer maintain nugget recipients on each client. A
   client-operations owner confirms list changes where needed, including whether
   each audience is HR distribution, direct employee delivery, or another
   explicitly agreed group.
4. Let the wellness officer review and publish routine batches under the agreed
   policy. Record that action. Do not add a mandatory owner approval to every
   edition. Additional content review can be assigned where it is needed.
5. Agree planning and approval deadlines relative to the first scheduled send.
   Record each edition's content reference, client/audience, date, time zone,
   sender, reviewer, operator, and status in one shared calendar.
6. Have the operator prepare and test the month as a batch. Review changes to
   content, audience, dates, or sender before publishing. The backup demonstrates
   the same procedure without depending on the owner's account.
7. After sends, the operator checks failures and reports exceptions. Do not make
   the owner inspect every normal delivery to know the programme ran.

Recurring date rules can generate draft slots for the next month or quarter.
They must not silently reuse old content when a new edition is missing.
Public holidays are supported sending occasions, not automatic exclusions.
Use an officer-maintained holiday calendar with country/year and source; the
officer confirms dates and times. If a holiday and normal slot coincide, show
the conflict for resolution rather than silently sending twice or skipping both.
The owner should be needed for policy and material exceptions, not mouse clicks.

## Minimum scope if the EAP integration proceeds

The following decisions are adopted for an integration pilot. Reopen them
explicitly before expanding scope.

### Frontend

- A list/calendar of editions with content title, client or audience group,
  requested time and time zone, operator, approver, and external status.
- Generate and edit draft dates in batches; show missing content and conflicting
  slots before approval. Use `Africa/Kampala` only as a proposed default to be
  confirmed, not an assumption about every recipient's location.
- Show an upcoming-send checklist for the wellness officer, including missing
  editions and failed handoffs. Agree a preparation deadline before each send
  and an exception reminder channel with the officer. Once Dynamics confirms
  scheduling, no person should need to remember to click Send at that time.
- Provide a structured nugget form using an approved branded template: subject,
  preview text, heading, body, optional image/alt text, and link. Reuse content
  as a new edition without changing an already scheduled version. No free-form
  drag-and-drop email designer in the first version. Final fields depend on
  the actual nugget format and successful content-handoff proof.
- Preview and prepare a batch, then hand it to Dynamics through the proven
  adapter. Clearly distinguish content saved here from an email ready to send
  there. If officer finalisation in Dynamics remains necessary, label it pending.
- Add a Wellness recipients panel to each client with add, edit, replace, and
  deactivate operations, external sync status, affected upcoming editions, and
  readable failures. Avoid making staff hunt through a global recipient list.
- Review the exact batch before scheduling. Any material edit invalidates the
  previous approval. Display partial batch failures individually.
- Show local approval, Dynamics publication, and delivery evidence separately.
  Never label a successful API request as a delivered email.
- Provide a cancellation request and escalation path. Only display confirmed
  cancellation after the external state has been verified. Previously delivered
  mail cannot be recalled by removing a calendar row.

### Backend and ownership

- Model tenant-scoped editions, approval revisions, and dispatch attempts.
  Use stable external IDs scoped to the Dynamics environment. Do not identify
  audiences by display name or infer subscribers from existing clinical records.
- EAP owns draft content, planning, and intended client recipient assignments.
  Dynamics owns published assets, segment execution, contact-point preferences,
  and sending. A bounded recipient adapter synchronizes only the mapped wellness
  records/fields. Do not add full CRM replication or a second consent authority.
- Validate each allowed tenant/client/environment/business-unit mapping on the
  server. A browser-submitted segment ID must not grant access to another client.
  An EAP tenant is not automatically a Dynamics business unit.
- Use a dedicated server identity with the minimum Dataverse role. Microsoft
  supports server-to-server application users; environment setup still needs
  administrator involvement. Keep credentials outside the browser and logs.
  [Microsoft: server-to-server authentication](https://learn.microsoft.com/en-us/power-apps/developer/data-platform/use-single-tenant-server-server-authentication).
- Persist approved scheduling work before calling Dynamics. Use a separate,
  bounded integration worker so external latency cannot stall audit processing.
  Let Dynamics execute the future send after successful publication; an EAP
  process should not need to wake at each recipient's send time.
- Assign one stable operation identity per edition revision. Reconcile uncertain
  outcomes before retrying; a unique local row alone cannot prevent duplicate
  journeys after a remote timeout. Block blind resubmission while state is unknown.
- Respect Dataverse throttling and its `Retry-After` response, with bounded
  retries and a visible failure queue.
  [Microsoft: API service protection](https://learn.microsoft.com/en-us/power-apps/developer/data-platform/api-limits).
- Publish sufficiently ahead of the requested time to allow validation and
  recovery. If a slot expires before publication, mark it missed and ask the
  officer to reschedule. Do not silently send a backlog late or shift a holiday
  edition to the next working day.
- Freeze approved content versions operationally and detect changes to referenced
  assets before dispatch. Segment approval covers its agreed definition and
  selection policy; an audience preview is not an immutable recipient snapshot.
  Recheck material audience drift. Dynamics still applies final eligibility.
- Treat wellness nuggets as subscription communications for this design. Do not
  relabel them transactional to bypass preferences. A privacy owner must confirm
  the appropriate purpose, audience authority, and retention policy. This is a
  product policy recommendation, not a legal classification of the actual emails.
- Do not use diagnoses, attendance, counselling records, or clinical notes to
  target nuggets. Keep operational communications access separate from clinical
  access. Do not expose individual employee engagement to employer dashboards.

### Recipient changes and synchronization

Adopt these rules to address the owner's recipient-maintenance problem:

- Reconcile the reported 133 recipients to client assignments once, using
  external record IDs and reviewed matches. Email alone is not person identity.
  Record whether an address represents a person, shared mailbox, or distribution
  list. Do not auto-enrol all client contacts or members.
- Default to client-scoped, application-managed static audience membership for
  this small operational list. Reuse compatible existing segments after mapping;
  preserve any externally managed dynamic segment rather than silently changing
  its semantics. Confirm the choice against the real tenant in Phase 1.
- Separate correcting the same recipient's address from replacing a departing
  person. Replacement creates/maps a different recipient assignment and removes
  the old one from the affected audience. Do not rename the old Dynamics person
  into the new person or delete a shared CRM contact to remove a subscription.
- Before changing an email field on a shared Dynamics contact, identify other
  clients and CRM workflows that use it. Agree field ownership with the Dynamics
  administrator; do not present a global contact edit as a client-only change.
  If a dedicated campaign address is needed, prove its audience configuration
  instead of assuming Dynamics will send to an arbitrary local field.
- List eligibility and consent are different. An administrator adding an address
  must not silently opt it in or clear a suppression. Address changes require
  fresh evaluation of the new contact point; do not copy consent from an old
  address or transfer it between people.
- Show pending, synchronized, and failed states. A local save is not evidence
  that Dynamics has stopped using an old recipient. Block new publication for
  affected audiences until membership changes reconcile. Use version checks
  and surface external-edit conflicts instead of overwriting other CRM work.
- Detect recipients shared by clients. Preview overlapping audiences and avoid
  duplicate sends for the same edition where content/sender/purpose are identical.
  Keep distinct client-specific editions separate and do not disclose other
  clients in personalization or recipient headers. Prove the selected audience
  and address deduplication behaviour in Dynamics before relying on it.
- A removal just before a send needs special handling. Removing segment
  membership is not an established recall mechanism for people already in a
  journey. Configure and test exit/suppression behaviour, show impacted active
  journey versions, and escalate urgent removals until external effect is known.

Microsoft distinguishes exclusion at entry from exit-by-segment during a
journey. Stopping requires attention to each version and cannot retract mail
already handed off for delivery. These constraints make near-send removal and
cancellation mandatory proof cases.
[Microsoft: ending and stopping journeys](https://learn.microsoft.com/en-us/dynamics365/customer-insights/journeys/journey-end).

### Reporting boundary

Start with local scheduling evidence and links to Dynamics delivery reports.
Do not promise a live delivery webhook or simple Dataverse query without proving
it. Microsoft documents a Fabric route for interaction analytics, with capacity
requirements and latency, and points to an alternative export route.
[Microsoft: interaction data integration](https://learn.microsoft.com/en-us/dynamics365/customer-insights/journeys/fabric-integration).

An API described as an email API may instead retrieve previously sent content;
Microsoft's exact-message API is such a retrieval API, not a send API.
[Microsoft: exact-message retrieval](https://learn.microsoft.com/en-us/dynamics365/customer-insights/journeys/developer/email-api).

For HR-forwarded or distribution-list mail, report only what the observed
delivery path establishes. A send to HR does not establish delivery to every
employee, and an open is not evidence of a wellness outcome.

## Cost and value decision

No cost saving, implementation duration, or percentage time reduction has been
measured. Recipient/client counts are owner-reported. Do not treat a vendor's list price
as our invoice or count licences that would remain in use as savings.

Microsoft's US public page lists Customer Insights at USD 1,700 per tenant/month
and qualifying Attach at USD 1,000, paid yearly, with unlimited users. These
are reference prices checked on the research date, not Uganda pricing, a quote,
or confirmation of this organisation's entitlement.
[Microsoft: pricing](https://www.microsoft.com/en-us/dynamics-365/products/customer-insights/pricing).

The current licence guidance describes a base allowance of 10,000 interacted
people and monthly interactions of ten times purchased interacted-person
capacity. Actual SKU, usage, other campaigns, and capacity must be checked.
[Microsoft: licence guidance](https://learn.microsoft.com/en-us/dynamics365/customer-insights/journeys/license-setup).

Measure owner time and total team time separately. Delegation can achieve the
owner's goal even when work moves to someone else rather than disappearing.

Compare each option using:

`monthly net benefit = staff time value saved + removable licence cost
                       - added recurring platform and support cost`

`payback months = one-time setup/migration/build cost / positive monthly net benefit`

Record training, content preparation, incident handling, and maintenance in the
comparison. If net benefit is zero or negative, there is no financial payback
under those assumptions. A strategic reason could still justify the work, but
must be stated separately. Do not claim full Dynamics savings from the hybrid.

## Phases and evidence required

### Phase 0: confirm inputs and hand off the existing workflow

Owners: wellness officer, programme owner, Dynamics administrator.

Capture one representative month's steps and actual effort. Confirm audience
type, content variations, time zones, feature availability, privileges, and
licensing. Trial the simplified Dynamics flow where supported. Write a short
operator runbook with a backup operator and escalation path.

Exit evidence: the wellness officer has ownership and access; recipient mappings,
representative content, weekday/holiday rules, and baseline effort are recorded.
The existing process continues while the hybrid's feasibility is tested.

### Phase 1: prove the content, recipient, and scheduling integration

Owners: Dynamics administrator and integration engineer.

Prove the EAP-to-Dynamics direction against a separate environment and a small,
explicitly authorised test audience. Establish three independently recorded
results: content creation/publication; client recipient add/update/replace/remove;
and dated journey publication. Confirm supported APIs, permissions, templates,
preference links, image hosting, status reconciliation, and cancellation.

If content automation is unsupported, record the remaining Dynamics step and
its measured effort. Do not start a large frontend build on the assumption that
the last API will be discovered later. Low-code or a limited manual content
handoff may be a fallback; neither is automatically full acceptance.

The proof must cover invalid content, wrong-client mappings, insufficient
permissions, an opted-out test recipient, duplicate submission, and an ambiguous
timeout. Test new-address consent, shared contacts, conflicting external edits,
and removal after journey entry. Validate weekday and holiday timing, quiet-time
interactions, and a change after approval. Keep evidence
of external results, not only mocked HTTP success.

Exit evidence: supported paths for all three results and agreed operating cost,
or explicit partial outcomes and a revised scope decision. If normal operation
needs private endpoints, browser automation, broad administrator credentials,
or cannot resolve uncertain sends, stop and retain A/B. This is a
new development gate, not an instruction to change the live Dynamics setup now.

### Phase 2: implement only the proven integration

Owners: backend integration engineer; frontend workflow engineer; reviewer and
Dynamics administrator for integration verification. The API proof must settle
contracts before splitting frontend/backend implementation.

Build the minimal scope above. Tests must verify role/tenant/client boundaries,
approval invalidation, recipient synchronization and consent boundaries, durable
retries, restart recovery, duplicate protection, partial batch results, external
edits, weekday/holiday timezone conversions, and explicit
cancellation state. Browser verification must exercise live API responses.

Exit evidence: tests passed, integration results recorded, operator and backup
trained, and production permissions reviewed. Mock tests do not prove delivery.

### Phase 3: controlled adoption and review

Owners: wellness officer and programme owner, supported by the integration engineer.

Pilot with an explicitly approved audience and schedule. Maintain one active
sender path per edition; do not run duplicate Dynamics and EAP schedules.
Reconcile already published journeys before any manual fallback. Disabling the
EAP integration does not automatically stop journeys already published remotely.

Compare owner effort, total team effort, recipient-update turnaround, missed dates, duplicate sends, and
exception handling with Phase 0. Continue only if the workflow delivers the
agreed improvement. Expand analytics or the content designer only with a separate
case for the additional work. About 133 recipients does not justify a general
marketing automation platform; a reliable narrow workflow is the target.

## Clarifications to capture before implementation

- Programme owner: acceptable residual effort and exceptions that require owner
  involvement. Routine preparation and scheduling are assigned to the Admin officer.
- Wellness officer: exact cadence, identical versus client-specific content,
  holiday jurisdictions, dates, languages, sender identities, and content format.
- Client operations: HR forwarding versus direct recipients, authoritative list
  source, who maintains departures, duplicates, and audience permissions.
- Dynamics administrator: environment/version, current journey pattern, template
  availability, business units, consent purposes, suppression configuration,
  API access, cancellation capability, and operator permissions.
- Finance: actual licences, other essential Dynamics uses, contract term, and
  costs that would genuinely disappear if email moved elsewhere.
- Privacy/programme owner: appropriate consent and retention policies, allowable
  reporting, approval responsibility, and acceptable send windows.

These open items refine cost and implementation scope. They do not prevent the
adopted direction: EAP preparation and recipient management with Dynamics
delivery, starting with proof of the email-content handoff. Replacing Dynamics
is outside the chosen scope.

## Handoff and future updates

This file is the decision record for wellness email work. The phase owners above
must add implementation, test, and deployment evidence separately as work occurs.
No phase is marked complete by this research. Record confirmed answers here and
reopen a decision explicitly if they materially change the recommendation.

No repository-wide rule change is needed now. Existing tenant, audit, identity,
and evidence rules already apply; module-specific decisions are contained here.
