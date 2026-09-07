/**
 * What the search dialog can offer besides records.
 *
 * Every action names an entry point that already exists and already carries
 * its own permission gate and validation. Selecting one opens that ordinary
 * form; nothing here creates, approves, sends or deletes.
 */

import { Building2, Calendar, Plus, UserRound } from "lucide-react"

import type { GlobalSearchResponse, SearchResultItem } from "@/api/generated"

export type RecordCategoryKey = keyof GlobalSearchResponse

export interface RecordCategory {
  key: RecordCategoryKey
  heading: string
  /** Detail page for one record. */
  detailTo: (id: string) => string
  /** List page for the category, which accepts the query as `search`. */
  listTo: string
  icon: React.ElementType
  /** Shown when this category's own request failed. */
  failureLabel: string
}

/**
 * Types map to routes here rather than the API returning a destination, so a
 * response can never redirect the app somewhere it did not choose.
 */
export const RECORD_CATEGORIES: ReadonlyArray<RecordCategory> = [
  {
    key: "clients",
    heading: "Clients",
    detailTo: (id) => `/clients/${id}`,
    listTo: "/clients",
    icon: Building2,
    failureLabel: "Clients could not be searched",
  },
  {
    key: "practitioners",
    heading: "Practitioners",
    detailTo: (id) => `/providers/${id}`,
    listTo: "/providers",
    icon: UserRound,
    failureLabel: "Practitioners could not be searched",
  },
  {
    key: "provider_organisations",
    heading: "Provider organisations",
    detailTo: (id) => `/provider-organisations/${id}`,
    listTo: "/provider-organisations",
    icon: Building2,
    failureLabel: "Provider organisations could not be searched",
  },
]

export interface SearchAction {
  id: string
  label: string
  icon: React.ElementType
  /** The route that opens the ordinary create form. */
  to: string
  /** `?new=true` is the handoff `useListPage` reads to open the create sheet. */
  search?: Record<string, unknown>
  /** Words that should also find this action. */
  aliases?: readonly string[]
  /** Hidden from Viewers, who cannot complete the form the action opens. */
  requiresWrite: boolean
}

/**
 * Labels match the button each action stands in for, so a user who finds the
 * page later recognises the control.
 */
export const SEARCH_ACTIONS: ReadonlyArray<SearchAction> = [
  {
    id: "add-client",
    label: "Add client",
    icon: Plus,
    to: "/clients",
    search: { new: true },
    aliases: ["new client", "create client", "employer"],
    requiresWrite: true,
  },
  {
    id: "add-practitioner",
    label: "Add practitioner",
    icon: Plus,
    to: "/providers",
    search: { new: true },
    aliases: ["new practitioner", "create practitioner", "provider", "therapist"],
    requiresWrite: true,
  },
  {
    id: "add-provider-organisation",
    label: "Add organisation",
    icon: Plus,
    to: "/provider-organisations",
    search: { new: true },
    aliases: ["new organisation", "provider organisation", "supplier", "firm"],
    requiresWrite: true,
  },
  {
    id: "schedule-session",
    label: "Schedule session",
    icon: Calendar,
    to: "/service-sessions",
    search: { new: true },
    aliases: ["book session", "new session", "log session", "appointment"],
    requiresWrite: true,
  },
]

export function matchesActionQuery(action: SearchAction, query: string): boolean {
  const needle = query.trim().toLowerCase()
  if (!needle) return true
  if (action.label.toLowerCase().includes(needle)) return true
  return (action.aliases ?? []).some((alias) => alias.includes(needle))
}

/** Total records across every category, used to pick the empty state. */
export function countRecords(response: GlobalSearchResponse | undefined): number {
  if (!response) return 0
  return RECORD_CATEGORIES.reduce(
    (total, category) => total + response[category.key].items.length,
    0,
  )
}

/** Whether any category reported its own failure. */
export function hasCategoryFailure(response: GlobalSearchResponse | undefined): boolean {
  if (!response) return false
  return RECORD_CATEGORIES.some((category) => response[category.key].failed)
}

export type { SearchResultItem }
