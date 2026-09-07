# Forms: review and suggested updates

Reviewed 2026-09-07 against `ae88bc8` on `chore/monorepo`. Scope: every
`*FormSheet` in `apps/web/src/components`, screenshot-driven for the session
form and source-read for the rest. Separates what was applied from what is
suggested, and names the owner where a form is not this stream's to change.

## Applied to the shared components (every form benefits)

- **Entity pickers are dropdowns** (`EntityPicker.tsx`). Each picker rendered
  its search box plus an always-open list of eight rows, so a form with three
  pickers was three screens tall before anything was chosen; the session form
  screenshots showed it plainly. The list now opens on focus, floats over the
  form, closes on selection, and selects on mousedown so the choice lands
  before the input blurs.
- **Help text sits under the control** (`FormField.tsx`). It rendered between
  label and input, so a described field sat lower than its grid partner: Rate
  and Session number in the session form were visibly misaligned. It also now
  yields to the error message instead of stacking with it.

## Applied per form

- **ServiceSessionFormSheet**: section no longer repeats its first field's
  label (Service → Session); practitioner section is Delivery; the
  physical-or-online field is Mode, matching the list column; enum selects say
  what they hold rather than Select…; copy trimmed throughout (see `a4f5b4d`).
- **CaseFormSheet**: intake description halved.
- **ContractFormSheet**: dropped a description that restated the Client label.
- **TenantFormSheet**: branding toggle description trimmed.
- **UserFormSheet**: create description trimmed.
- **TagFormSheet**: question placeholder replaced with the shape of an answer.

## Suggested, not applied

### Live forms, this stream could take them

- ~~**IndustryFormSheet**: "Paste the parent industry's ID"~~ — done: the field
  is an IndustryPicker, and an industry cannot be chosen as its own parent.
- **PersonFormSheet** (734 lines): the largest sheet, no section descriptions at
  all, and `WorkStatus.TERMINATED` in a flat select. Worth the same
  section-and-copy pass the session form got, but it spans several personas
  (staff, dependants, providers) and deserves its own slice.
- **MemberFormSheet**: fine overall; the identification section's "Recorded for
  verification; none of these is the member code" is good copy. No change
  suggested beyond the shared fixes it already inherits.
- **Date inputs** are native `datetime-local` everywhere (`dd/mm/yyyy, --:--`
  in the screenshots). A shared calendar control exists (`ui/calendar.tsx`) but
  no form uses it. Adopting it is a product/design decision; suggested, with no
  urgency.

### Owned elsewhere

- **ProviderFormSheet** (provider worktrees): only one description and it is a
  good one. No changes suggested; noted so the owner knows it was looked at.

### Paused modules (out of scope per MODULES_REPAIR_PLAN.md)

CampaignFormSheet, SurveyFormSheet and EngagementFormSheet carry the wordiest
copy of the set, e.g. the campaign pool description runs two sentences and
thirty words, and SurveyFormSheet still promises a webhook URL and token that
SUR-01 records the API does not return. Trim when those modules reopen, in the
same slice as their contract repairs; polishing the copy of a form that cannot
submit would dress a broken window.

## Verification

659 web tests, lint, typecheck pass after every applied change. Picker-driven
flows (member, practitioner, client selection) are covered by the existing
sheet tests, which now exercise the dropdown behaviour. Browser verification:
the session form screenshots motivated the picker and alignment fixes, but the
fixed forms were not re-screenshotted; a visual pass is the fair next check.
