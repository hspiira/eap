# Navigation, profile menu, and search

Decision date: 2026-09-07. Baseline: `70e7b4c`, with concurrent frontend edits
present. Status: design decisions recorded; implementation and verification
pending. Do not overwrite those edits when implementing this plan.

## Recommendation

Use a quiet global header with workspace context, one prominent search control,
and a compact account menu. Keep module navigation in the sidebar and page
titles/actions in the page header. Evolve the current page switcher into a
search and command dialog that finds authorised records as well as destinations.

This is a design judgment based on the current implementation and browser
inspection, not a measured usability-study result. The owner delegated design
decisions; the following choices are adopted for implementation.

## Evidence from the current interface

- The running desktop view repeats search and sidebar expansion in the sidebar
  and header. It also repeats Providers context in the global header and the
  page breadcrumb. Inspected at `localhost:3000/providers`; fixture mode was
  visibly enabled. No claim is made about production data or behaviour.
- `apps/web/src/components/DashboardHeader.tsx:273` assembles the sidebar control,
  page title, search, notifications, theme control, user menu, and help.
- `apps/web/src/components/DashboardHeader.tsx:164` identifies the user primarily
  by email. Its account menu contains Profile and Sign out.
- Notifications are a placeholder with a constant unread state and static
  reassurance at `apps/web/src/components/DashboardHeader.tsx:107`.
- Help targets `#help` at `apps/web/src/components/DashboardHeader.tsx:252`.
  This is not evidence of an implemented support destination.
- Search renders a fixed navigation registry at
  `apps/web/src/components/CommandPalette.tsx:47` and groups it at line 134.
  It contains no record queries. The owner's observation that it searches
  sidebar destinations is supported by the implementation.

## Header and sidebar decisions

The desktop header should read left to right as:

**Sidebar control and workspace name → Search clients, providers… → Account**

Keep the existing compact height initially. Improve spacing and hierarchy before
adding height, large icons, or another toolbar. Use existing visual tokens.

1. Keep one sidebar expansion control. Remove the duplicate sidebar search
   launcher when the header launcher is available. On mobile, use a menu button,
   search icon, and account avatar; search opens a usable full-width dialog.
2. Show the current workspace/tenant name persistently. A client organisation is
   not a tenant. If switching is available, show only authorised workspaces and
   clear the previous context's cached/search state on a switch.
3. Remove the global page title when the page already provides its breadcrumb
   and title. Preserve one useful breadcrumb trail within the page. Keep Add,
   Edit, Export, and page-specific filters with that page.
4. Retain a visible desktop search field or field-like launcher and Cmd/Ctrl+K.
   Use a placeholder naming the categories actually supported, rather than
   promising to search everything before it can.
5. Move theme selection into the account menu. Offer explicit Light, Dark, and
   System choices instead of cycling through modes with an unexplained icon.
6. Remove the notification bell until there is a real event source, unread/read
   state, actionable destinations, and failure handling. A static all-clear
   message is not useful operational feedback.
7. Move Help into the account menu only once it has a real destination. Do not
   preserve a decorative link as though support were implemented.
8. Keep the desktop sidebar labelled by default for new users, allow collapsing,
   and respect saved preference. Keep unavailable modules out of routine
   navigation/search; feature previews belong in a deliberate preview area.
9. Follow the adopted Providers grouping in `PROVIDERS_MIGRATION.md`: one module
   with Practitioners and Organisations views. Avoid creating a sidebar entry
   for every table. Broader sidebar regrouping is a separate change.

The stable, visible search placement is consistent with NN/g's intranet-search
guidance. This supports discoverability, not a claim that our exact proposed
layout has been tested with our users.
[NN/g: intranet-search essentials](https://www.nngroup.com/articles/intranet-search/).

## Account menu

Keep the account control at the top right, with initials/avatar, a short display
name where available, and a chevron. Use email as a fallback, not the preferred
visible identity. Do not move it between sidebar and header across desktop pages.

The menu contains:

- Identity block: name, email, role, and current workspace.
- My profile: the existing profile route.
- Appearance: Light, Dark, System, with the current choice marked.
- Help and support: only when a working destination exists.
- Sign out: separated at the bottom.

Workspace switching belongs with the visible workspace control, not a second
switcher inside this menu. Tenant administration and platform user management
remain administration destinations, not personal profile settings. Do not add
password or notification-preference screens unless those capabilities exist.

## What search should do

Use one dialog with clearly labelled groups. It should support three intentions:
finding a record, opening a module, or starting a permitted task.

### Records

First release: clients, practitioners, and provider organisations. Show a small
bounded result group per type, with a label that disambiguates the record and
only the secondary information needed to choose it. Link to its actual detail
page. Provide See all for a category, preserving the query in its list view.

Next release: members, after member-visibility rules are verified. Include client
context and an approved identifier to distinguish same-name members, without
surfacing private clinical information. Sessions and contracts can follow when
their search fields, routes, and permissions have been established.

Do not initially search clinical notes, diagnoses attached to people, document
contents, or survey free text. A search preview can disclose information even
when opening the destination is blocked. Admin status must not be treated as
automatic permission to search clinical material.

### Pages

Keep module navigation as one result group, using the same route registry,
permissions, aliases, and feature availability as the sidebar. For example,
provider, practitioner, and therapist may lead to the Providers destination.
These are navigation synonyms, not rules for merging practitioner identities.

### Actions

Offer a small set of existing permitted tasks, such as Add client, Add
practitioner, or Book session, once their real entry points are verified.
Selecting an action opens the ordinary form with its normal validation. It
must not create, delete, approve, or send anything directly from a search result.
Keep all results in groups even when a user types an action-like phrase.

For the wellness officer, Prepare nugget could become an action after the
workflow in `WELLNESS_NUGGETS_DECISION.md` is implemented. Do not expose it now
as a working command.

### Interaction behaviour

- With no query, show useful permitted pages/actions. Recently opened records
  can be added later; default to session-only, identity/tenant-scoped history.
- Search records after two characters, with a short debounce and cancellation
  of superseded requests. Use a limit of five per category for the initial
  design, with See all. These are tunable defaults, not measured optimums.
- Order each group predictably: exact approved identifier/name match, then
  prefix match, then other supported text matches. Do not present fabricated
  cross-category relevance scores or claim typo tolerance before it exists.
- Distinguish no results, searching, and a failed category. Failed requests must
  not turn into No records found, and old results must not appear under a new
  query. Show category truncation without exposing inaccessible counts.
- Arrow keys navigate results, Enter opens the selected result, Escape closes,
  and focus returns to the launcher. Support keyboard and screen-reader use
  through a correctly implemented dialog/combobox pattern. Avoid duplicating
  competing Cmd/Ctrl+K handlers on page-level search inputs.
- Keep page-specific search and filters. Label them Search practitioners,
  Search clients, and so on. Global search locates records; list search supports
  the user's work within that module.

Follow the WAI-ARIA interaction patterns and verify the actual component
behaviour rather than adding ARIA attributes without matching keyboard support.
[W3C: combobox pattern](https://www.w3.org/WAI/ARIA/apg/patterns/combobox/).

## Existing capabilities and backend work

Searchable list contracts already exist at:

- `apps/api/app/api/routes/clients.py:1035`: client-name search.
- `apps/api/app/api/routes/providers.py:80`: practitioner name/contact-email search.
- `apps/api/app/api/routes/provider_organisations.py:84`: name/registration search.
- `apps/api/app/api/routes/members.py:370`: member list search, requiring a
  separate visibility review before inclusion in global results.

These contracts reduce implementation work but are not proof that a global
search is ready. Client listing also computes list metrics; fetching complete
lists from every module on each keystroke would be unnecessary work and expose
more fields than the search needs.

Adopt one small authenticated search endpoint for record groups, backed by
existing domain/repository queries and minimal result projections. Keep page
and action matching local. No external search service, vector database, or AI
query interpretation in the initial release.

Backend requirements:

- Derive tenant and permissions from authenticated context. Apply tenant,
  role, client, and record visibility constraints before selecting/ranking
  results, not after fetching an unrestricted result set.
- Return stable typed IDs, display labels, approved secondary labels, bounded
  category results, and has-more information. Map types to frontend routes;
  do not accept arbitrary redirect destinations.
- Preserve source module access rules. Reuse predicates/services rather than
  creating a second weaker authorisation policy for search. Detail routes must
  still enforce access independently.
- Bound query length and execution work; use parameterised queries, pagination,
  and indexes justified by measured query plans. Begin with existing supported
  fields and do not claim universal email/phone/reference search.
- Minimise cached payloads and avoid logging raw queries, which may contain
  personal information. Cancel and clear search/history when identity, tenant,
  or permissions change. Do not send queries to analytics providers.
- Keep category failures and unavailable categories explicit. Do not calculate
  or return counts over records the caller cannot access.

Existing list routes may be used in a small prototype with their actual field
limits, but that prototype must not be presented as the completed global-search
contract. The security findings in `MODULES_REPAIR_PLAN.md` must be revalidated
where relevant before expansion.

## Delivery order and acceptance

1. **Header/profile simplification, frontend owner.** Remove duplicate controls,
   move appearance settings, remove placeholder utilities, preserve context and
   page actions, and keep existing navigation working. Verify desktop/mobile,
   both sidebar states, keyboard focus, and all three themes.
2. **Search contract, backend owner.** Publish the result contract for clients
   and both provider types. Verify unauthenticated access, cross-tenant isolation,
   differing roles, result projections, limits, errors, and query behaviour on
   representative data. Search must not expand visibility beyond source modules.
3. **Search experience, frontend owner.** Integrate grouped records, pages, and
   verified actions. Test rapid query changes, cancellation, partial errors,
   no results, See all, role changes, sign out, and workspace switching. Verify
   live API responses in the browser, not only fixture results.
4. **Controlled expansion, reviewer.** Add members only after visibility checks;
   evaluate sessions/contracts separately. Add recent records and operational
   notifications only when their data sources and privacy behaviour are ready.

Measure whether representative staff can find a known client/provider, distinguish
same-name records, start a common task, and find their account settings without
guidance. Record observations before claiming the redesign is faster or easier.

This review changed documentation only. No app behaviour was changed or tested
as part of the proposed redesign. Keep this file updated with separate
implementation, passing-test, browser-verification, and deployment evidence.
