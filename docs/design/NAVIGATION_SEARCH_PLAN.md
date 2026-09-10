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
9. Follow the adopted Providers grouping in
   `docs/migrations/PROVIDERS_MIGRATION.md`: one module with Practitioners and
   Organisations views. Avoid creating a sidebar entry for every table. Broader
   sidebar regrouping is a separate change.

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
workflow in `docs/design/WELLNESS_NUGGETS_DECISION.md` is implemented. Do not
expose it now as a working command.

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
contract. The security findings in `docs/reviews/MODULES_REPAIR_PLAN.md` must be
revalidated where relevant before expansion.

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

The original review changed documentation only. Phases 1 to 3 are now
implemented; their separate implementation, test, browser-verification and
deployment evidence is recorded below. Phase 4 is deferred and untouched.

---

# Implementation record, phases 1 to 3

Implemented 2026-09-07 on `chore/monorepo`, base `aa2b327`. Phase 4 deferred.
Nothing is deployed and no shared database was touched. Several agents held
uncommitted work in this tree during the change; what that meant for the
generated contract is recorded under "Concurrent work" below.

## Status separation

| Claim | State |
| --- | --- |
| Implemented | Yes, phases 1 to 3. |
| Unit/component tests passing | Yes. Counts under "Test evidence". |
| Contract regenerated | Yes, and idempotent on re-run. |
| Verified in a real browser against the live API | Yes. 52 of 52 checks. See "Browser verification". |
| Deployed | No. No environment other than a local throwaway database was touched. |

## Phase 1: header and profile menu

`apps/web/src/components/DashboardHeader.tsx` was rewritten and reads
left to right as sidebar control, workspace name, search launcher, account menu.

- One sidebar control. The header trigger is the only one. The collapsed
  sidebar's logo was a second expand control and is now an inert mark with a
  tooltip (`AppSidebar.tsx`, `CollapsedHeader`).
- One search control. The sidebar's two launchers (expanded and collapsed) are
  removed; the header carries a field-like button on desktop and an icon button
  below `md`, both opening the same dialog.
- The global page title is gone. Every route either renders `PageShell`, which
  provides its own breadcrumb trail and heading, renders its own heading
  (`routes/incidents/index.tsx:27`), or is a layout or a redirect. `routeTitle`,
  `ROUTE_TITLES` and `PageTitle` became unreachable and were deleted with their
  test file `routeTitle.test.ts`. Page breadcrumbs and page actions are
  untouched.
- Workspace context is persistent in both sidebar states, in the header. The
  sidebar header now shows the product mark instead, so the workspace name
  appears once. `toProperCase` moved to `lib/display.ts` and is shared, so the
  header and the old sidebar rendering agree.
- The menu shows a name, not an email. `display_name` is written in exactly
  one place in the backend, `auth_azure.py:212`, from the Microsoft profile
  claim; no request schema anywhere accepts it, so for every password-login
  account it is null. Preferring it alone therefore showed the raw email to
  most users. `accountDisplayName` prefers the stored name and otherwise builds
  a label from the email's local part, dropping digit-only fragments. It is a
  derived label rather than asserted identity, so the full email stays visible
  inside the menu beneath the name. The avatar initial follows the same value.
- Appearance is explicit Light / Dark / System with the current choice ticked,
  in the account menu. The unlabelled cycling icon button is gone.
- The notification bell and the `#help` link are removed. Neither had an event
  source or a destination.
- Saved sidebar preference is unchanged: `AppLayout` still reads and writes
  `uiStorage`. Existing routes are unchanged.

### Design decisions taken here

1. **Workspace name in the header, product name in the sidebar.** Keeping the
   workspace in the sidebar would have hidden it whenever the sidebar was
   collapsed, which fails "show the current workspace persistently". Showing it
   in both would have duplicated the label the redesign set out to de-duplicate.
2. **`routeTitle` deleted rather than kept.** Nothing else referenced it once
   the header title went. Keeping a tested but unreachable function would
   overstate coverage.
3. **The collapsed logo is no longer a button.** "Keep one sidebar expansion
   control" is only true if the logo stops being a second one.

## Phase 2: search contract

New: `apps/api/app/api/schemas/search_schemas.py`,
`apps/api/app/api/routes/search.py`, registered in
`apps/api/app/api/routes/__init__.py`.

`POST /search?tenant_id=…` with body `{ q, limit }` returns three categories:
`clients`, `practitioners`, `provider_organisations`. Each carries
`items[{ id, label, secondary, type }]`, `has_more` and `failed`.

- **Authorisation is the source module's, not a second policy.** The route
  depends on `require_same_tenant`, which is exactly what guards
  `clients.py:1035`, `providers.py:80` and `provider_organisations.py:84`.
  Search therefore cannot reach further than the lists it searches, and detail
  routes still authorise their own reads.
- **Tenant and permissions come from the authenticated context.**
  `require_same_tenant` compares the token's tenant against the requested one
  before any query runs; a refusal touches no repository (tested).
- **Admin is not treated as clinical access.** No clinical surface is searched
  at all: no members, cases, notes, diagnoses, documents or survey text. The
  three categories carry no clinical fields.
- **Existing queries reused.** `ClientRepository.list_all`,
  `ProviderRepository.search` and
  `ProviderOrganisationRepository.list_organisations`. No new SQL, no new
  index, and therefore no index claimed without a measured plan. Soft-deleted
  rows are excluded by the base repository; archived clients are excluded by
  `list_all`'s existing default.
- **Bounded, with no count over inaccessible records.** Each category
  over-fetches one row; `has_more` comes from that extra row rather than from a
  `COUNT`. `limit` is 1 to 10, default 5. `q` is 1 to 100 characters, and a
  query shorter than two characters after stripping runs no record query.
- **Minimal projection.** Four fields per hit. Secondary labels are the client
  code, the practitioner's `tier · region`, and the organisation's registration
  number. Practitioner contact email and bio are deliberately not returned:
  they are not needed to choose between two same-name practitioners, and a
  search preview discloses even when the detail route would refuse.
- **Category failures are isolated.** Each category runs inside
  `_run_category`, which marks that category `failed`, rolls back so a failed
  statement cannot poison the next category, and lets the others return.
- **Types map to routes on the frontend**, in `search-registry.ts`. The
  response never names a destination, so it cannot redirect the app.
- No external search engine, vector database or AI query interpretation.

### The query travels in the body, and why

Found during live verification and fixed rather than documented away. With `q`
as a query parameter the handler logged nothing, but the server access log
recorded the term anyway:

    INFO: "GET /search?tenant_id=…&q=nakato HTTP/1.1" 200 OK

A search term routinely names a person, and any proxy in front of the app logs
URLs too. The endpoint is therefore a `POST` whose body carries `q`, and the
access log now shows only `POST /search?tenant_id=…`. `GET` returns 405, and a
`q` appended to the URL is ignored in favour of the body. All three are tested.

Failure logging records the category and the exception class only, never the
exception string: a SQLAlchemy error message embeds its statement and its
parameters, and the parameter here is the search text. A mutation test confirms
the assertion has teeth: replacing `logger.error(...type(exc).__name__)` with
`logger.exception(...)` makes `test_the_raw_query_is_absent_from_the_failure_log`
fail.

## Phase 3: search experience

New `apps/web/src/components/search/GlobalSearch.tsx` replaces
`CommandPalette.tsx`, which is deleted.

- Cmd/Ctrl+K and the header launcher both open it. There is no competing
  Cmd+K handler: the sidebar's shortcut is Cmd+B (`ui/sidebar.tsx:10`) and
  `SheetForm` binds Cmd+Enter.
- Groups are Records (three labelled categories), Pages and Actions.
- **Pages and actions match locally; records come from the API.** cmdk's own
  filtering is switched off (`shouldFilter: false`), so a record matched on a
  field the label does not show, such as a registration number, is not silently
  dropped by a second client-side filter.
- **One navigation registry.** `lib/navigation.ts` holds the items, flags,
  platform-admin and clinical-scope gates, active-state resolution and search
  aliases; `hooks/useNavigation.ts` applies the per-session gates. Both the
  sidebar and the dialog read it, so a label, permission or feature flag cannot
  drift between them. Providers stays one entry owning `/providers` and
  `/provider-organisations`, per this repo's provider navigation decision.
- **Actions have verified entry points.** Add client, Add practitioner, Add
  organisation and Schedule session, each labelled as the button it stands in
  for and each navigating to a list route with `?new=true`, the handoff
  `useListPage` already reads. Selecting one opens the ordinary form with its
  normal validation; nothing mutates from a search result. Viewers do not see
  them. No wellness nugget command, no member action.
- **Interaction.** 250 ms debounce; a two-character floor; requests cancelled
  by consuming TanStack Query's abort signal; five per category; per-category
  failure rows; a whole-request failure row distinct from no results; a
  "Searching records…" state that also covers the debounce window; and
  See all links only where a category is truncated, carrying the query as
  `?search=`.
- **No stale results.** The query key contains the debounced text and there is
  no `placeholderData`, so a previous query's rows cannot render under a newer
  one.
- **State is cleared on identity and workspace change.** The key includes user
  id and tenant id, so a different session structurally cannot read cached
  rows; `clearGlobalSearch` additionally cancels in-flight requests and drops
  the cache, and is called from `authActions.logout` and from
  `tenantActions.setCurrentTenant`.
- **Accessibility.** `CommandDialog` gained a required visually hidden title
  and description; it previously had neither, so the dialog announced as
  unlabelled. Its own close button is hidden because it sat on top of the
  search input; Escape still closes and Radix returns focus to the launcher.
  Arrow keys and Enter come from cmdk's option roles.
- Page-level table search and filters are untouched.

Not added, as instructed: member search, clinical-content search, recent-record
history, wellness commands, real notifications.

## Test evidence

Run in a clean `git worktree` at `aa2b327` carrying only this change set, so no
concurrent agent's uncommitted work influenced the result.

Backend, from `apps/api`:

- `ruff check app tests scripts`: all checks passed.
- `ruff format --check app tests scripts`: 606 files already formatted.
- `lint-imports`: 3 contracts kept, 0 broken.
- `pytest tests/unit`: **1569 passed**.
- `pytest tests/unit/api/test_global_search_routes.py`: **37 passed**, covering
  anonymous refusal, cross-tenant refusal with no repository call, Admin/User/
  Viewer reads, four-field projection, bio and contact-email non-disclosure,
  a practitioner with no profile, truncation and the over-fetch-by-one, absence
  of any count, out-of-range limit and over-long query, the sub-floor query,
  per-category failure with rollback, empty-not-failed, GET returning 405, a URL
  `q` being ignored, and the query's absence from the failure log.

Frontend, from `apps/web`:

- `tsc --noEmit`: clean.
- `eslint .`: clean.
- `prettier --check` on the files in this change set: clean.
- `vitest run`: **617 passed across 75 files**, including the pre-existing
  `types/enums.contract.test.ts`.
- New: `GlobalSearch.test.tsx` (31), `DashboardHeader.test.tsx` (18),
  `navigation.test.ts` (18), `search-registry.test.ts` (13),
  `search-state.test.ts` (5), `search-teardown.test.ts` (4),
  `endpoints/search.test.ts` (4). `AppSidebar.test.tsx` extended to 8.

Contract: `dump_openapi.py` then `openapi-typescript` produces
`+175 / -0` in `openapi.json` and `+133 / -0` in `schema.ts` against
`aa2b327`, and re-running produces the same diff, so `pnpm contracts:check`
would pass for this commit.

## Live API verification

Servers started from this change set's checkout: API on `127.0.0.1:8010`, web
on `localhost:3010`, `VITE_USE_FIXTURES=false`, against a throwaway database
`eap_navsearch` created for this purpose and migrated to head. Records were
created through the real API, not inserted as fixtures: seven clients including
an exact-match "Acme", three practitioners including two both named "Alice
Nakato", two provider organisations.

Observed against the running API:

| Case | Result |
| --- | --- |
| Unauthenticated `POST /search` | 401 |
| Cross-tenant `tenant_id` with a valid token | 403 |
| `GET /search` | 405 |
| `limit=11` | 422 |
| 101-character `q` | 422 |
| One-character `q` | 200, zero records, `failed: false` |
| `q=acme` | 5 clients with `has_more: true` out of 7 matching, 1 practitioner, 1 organisation |
| `q=nakato` | both same-name practitioners, disambiguated `T1 · Central` and `T3 · Eastern` |
| Item keys | exactly `id`, `label`, `secondary`, `type` |
| Access log after POST searches | no search term recorded |

## Browser verification

Driven in a real headless Chromium against both running servers, signed in as
a real user, with `VITE_USE_FIXTURES=false` and live API responses. **52 of 52
checks passed.** Script and screenshots were produced in a throwaway checkout
and are not committed.

Servers: API from this change set's checkout on `:8010`, web dev server from
the same checkout on `:3010`, database `eap_navsearch` migrated to head and
populated through the real API.

Header and account menu:

- Workspace name present in the header; exactly one sidebar control there.
- No notification bell, no help button.
- Desktop launcher visible; the account label carries no `@` and read
  `"Asha Kagwa"`; the email is still reachable inside the menu.
- On `/providers` the page heading, its `nav[aria-label="Breadcrumb"]` and its
  "Add practitioner" action all survive, and the header contains no second
  title. Header text was exactly
  `"Search clients, practitioners…  ⌘K  A  Asha Kagwa"`.
- Light, Dark and System each applied (`html class` observed as `null`, `dark`
  and `""`).
- Sidebar toggles in both directions; no global launcher outside the header,
  while the clients list's own `Search clients…` input survives.
- At 390x844 the field launcher is replaced by the icon launcher, the dialog
  opens 390px wide, and the document does not scroll horizontally.

Search:

- Cmd+K opens a dialog carrying an accessible name.
- One character issues no record request.
- Records arrive over `POST /search?tenant_id=…`, with no search term anywhere
  in the request URL.
- A live client record and its code render; See all appears on truncation and
  navigates to `/clients?search=acme`.
- Pages and Actions are absent for `acme`, which matches neither, and both
  appear for `client`; the synonym `therapist` finds Providers.
- Both practitioners named "Alice Nakato" render, told apart by
  `T1 · Central` and `T3 · Eastern`, and no contact email appears in the
  preview.
- Arrow keys move the selection and Enter opened
  `/clients/rjrcxv47p84225vz1a9nciws`. Escape dismisses the dialog.
- `zzzzqqq` states no records match. With one category forced to `failed`, the
  dialog says clients could not be searched, does not say no records match,
  and still renders the practitioner that succeeded.
- Selecting "Add client" opened the form and issued no mutating request to
  `/clients` (0 before, 0 after).
- Sign out returns to the login page and leaves no record result in local
  storage.
- No unexpected console errors throughout.

Not covered by this run: screen-reader announcement was not verified with an
actual screen reader, and focus restoration was checked only as Escape
dismissing the dialog, not as focus landing back on the launcher element.

## Deployment

Nothing deployed. No shared or target environment was inspected or migrated.
The only database touched is the local throwaway `eap_navsearch`.

## Concurrent work in this tree

Other agents held uncommitted changes here throughout, including a
`ProviderGender` enum added to the provider profile and a narrowing of
`MemberGender` on the frontend. Two consequences, recorded so neither is read
as this change's doing:

1. The generated contract was regenerated in an isolated worktree at
   `aa2b327` plus this change set only, so `openapi.json` and `schema.ts`
   carry the search additions and nothing else. `ProviderGender` is absent from
   the artifacts committed here; the agent who owns it regenerates with their
   own commit.
2. In the shared working tree, `types/enums.contract.test.ts` fails on
   `MemberGender offers every value the API can return`. That is their
   uncommitted frontend narrowing meeting a contract generated from `aa2b327`.
   It passes in this change set's isolated worktree, and resolves when they
   commit their backend change with a regenerated contract. Every other test
   passes in the shared tree: 629 of 630.

## Recorded finding, not fixed here

`users.display_name` is read-only across the whole API. `UserResponse` returns
it (`users.py:86`) and `UserEntity.update_display_name` exists
(`entities/user.py:273`), but the only caller is the Azure SSO callback
(`auth_azure.py:212`); no request schema accepts it and there is no route to
set it. A password-login account therefore has no name of its own, which is
why the account menu now derives a label from the email rather than showing
one that is always null.

**Owner: the users module.** Decide whether a display name is self-service or
Admin-set, add it to a request schema and a route, and surface it on `/me`.
Until then the derived label stands in for it. Recorded rather than fixed: it
changes the users module's write surface, which this task does not own.
