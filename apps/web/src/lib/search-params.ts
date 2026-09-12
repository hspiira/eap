/**
 * Helpers for list-route `validateSearch` and filter option arrays.
 *
 * Replace hand-enumerated enum guards (which break silently when an enum member
 * is added, OCP violation) and per-page `STATUS_OPTIONS` arrays with:
 *
 *   validateSearch: listSearchSchema({ status: enumParam(ContractStatus) })
 *   const STATUS_OPTIONS = enumOptions(ContractStatus, "All statuses")
 */

import { getStatusLabel } from "@/utils/statusColors"

export type SearchParser<T> = (value: unknown) => T | undefined

/** Parser that accepts a value only if it is a member of the given enum. */
export function enumParam<T extends string>(enumObj: Record<string, T>): SearchParser<T> {
  const values = Object.values(enumObj)
  return (value: unknown): T | undefined =>
    typeof value === "string" && values.includes(value as T) ? (value as T) : undefined
}

/**
 * Parser that accepts one enum member or several, for a repeatable filter
 * (`?status=Scheduled&status=Rescheduled`). Returns a single value when only
 * one was given, so a single-value link still round-trips as one rather than
 * a one-element array.
 */
export function enumOrArrayParam<T extends string>(
  enumObj: Record<string, T>,
): SearchParser<T | T[]> {
  const values = Object.values(enumObj)
  const isValid = (v: unknown): v is T => typeof v === "string" && values.includes(v as T)
  return (value: unknown): T | T[] | undefined => {
    if (Array.isArray(value)) {
      const filtered = value.filter(isValid)
      if (filtered.length === 0) return undefined
      return filtered.length === 1 ? filtered[0] : filtered
    }
    return isValid(value) ? value : undefined
  }
}

/**
 * Parser for a boolean flag. Absent means false, so the default state leaves no
 * trace in the query string.
 *
 * The router JSON-decodes search values, so the accepted forms are what a
 * writer can actually produce: a boolean `true` becomes `?flag=true` and
 * decodes back to `true`, while the string `"1"` becomes `?flag=1` and decodes
 * to the *number* 1. Checking only for the string silently failed the second
 * case, so the filter read as off after a reload or on a shared link.
 */
export function boolParam(): SearchParser<true> {
  return (value: unknown): true | undefined =>
    value === true || value === "true" || value === 1 || value === "1" ? true : undefined
}

/** Table state the shared list hooks keep in the URL rather than in React state. */
export interface ListViewSearch {
  new?: boolean
  search?: string
  page?: number
  sort?: string
  desc?: boolean
}

/** Page 1 is the default, so it is left out of the query string entirely. */
function pageParam(value: unknown): number | undefined {
  const page = typeof value === "string" ? Number(value) : value
  return typeof page === "number" && Number.isInteger(page) && page > 1 ? page : undefined
}

/**
 * Build a `validateSearch` function that always handles the shared `new` (sheet
 * open), `search`, `page`, `sort` and `desc` params, plus any entity-specific
 * parsers. The returned type is inferred so `useSearch()` stays fully typed
 * downstream.
 *
 * Page and sort belong here rather than in component state: a sort held in
 * React is lost on every reload and on every return from a detail row.
 */
export function listSearchSchema<E extends Record<string, SearchParser<unknown>>>(fields: E) {
  return (
    search: Record<string, unknown>,
  ): ListViewSearch & {
    [K in keyof E]?: NonNullable<ReturnType<E[K]>>
  } => {
    const out: Record<string, unknown> = {}
    if (search.new === "1" || search.new === true) out.new = true
    if (typeof search.search === "string" && search.search.trim()) out.search = search.search
    const page = pageParam(search.page)
    if (page !== undefined) out.page = page
    if (typeof search.sort === "string" && search.sort.trim()) out.sort = search.sort
    if (boolParam()(search.desc)) out.desc = true
    for (const key in fields) {
      const parsed = fields[key](search[key])
      if (parsed !== undefined) out[key] = parsed
    }
    return out as ListViewSearch & {
      [K in keyof E]?: NonNullable<ReturnType<E[K]>>
    }
  }
}

/**
 * Build a filter-select option list from an enum: an `"all"` option followed by
 * every enum member, labelled via the status-display SSOT.
 */
export function enumOptions<T extends string>(
  enumObj: Record<string, T>,
  allLabel: string,
): ReadonlyArray<{ value: "all" | T; label: string }> {
  return [
    { value: "all", label: allLabel },
    ...Object.values(enumObj).map((value) => ({ value, label: getStatusLabel(value) })),
  ]
}
