/**
 * Server-side list semantics, applied to an in-memory fixture store.
 *
 * A fixture that returns its whole store as one page teaches the page nothing
 * about paging, and a page that filters in the browser shows a filtered slice
 * with an unfiltered total. Both modes go through this, so a fixture run
 * exercises the same envelope, filters, sort and paging as the API
 * (MODULES_REPAIR_PLAN API-01).
 */

export interface FixturePageEnvelope<T> {
  items: T[]
  total: number
  page: number
  limit: number
  has_more: boolean
}

export interface FixturePageOptions<T> {
  /** Fields matched case-insensitively against `search`. */
  search: Array<keyof T>
  /** Fields matched for equality against the like-named request param. */
  equals: Array<keyof T & string>
  defaultSort: keyof T & string
}

/**
 * The request params the pager reads. Declared as a type alias, not an
 * interface: an interface has no implicit index signature, so no `*ListParams`
 * interface would satisfy it without a cast at every call site.
 */
export type FixturePageParams = {
  page?: number
  limit?: number
  search?: string
  sort_by?: string
  sort_desc?: boolean
}

const DEFAULT_LIMIT = 20

function matchesSearch<T>(row: T, term: string, fields: Array<keyof T>): boolean {
  return fields.some((field) =>
    String(row[field] ?? "")
      .toLowerCase()
      .includes(term),
  )
}

function compare(a: unknown, b: unknown): number {
  if (typeof a === "number" && typeof b === "number") return a - b
  const left = a == null ? "" : String(a)
  const right = b == null ? "" : String(b)
  return left < right ? -1 : left > right ? 1 : 0
}

export function fixturePage<T>(
  rows: T[],
  params: FixturePageParams | undefined,
  options: FixturePageOptions<T>,
): FixturePageEnvelope<T> {
  const { page = 1, limit = DEFAULT_LIMIT, search, sort_by, sort_desc = true } = params ?? {}
  const filters = (params ?? {}) as Record<string, unknown>

  let matched = rows
  for (const field of options.equals) {
    const wanted = filters[field]
    if (wanted !== undefined && wanted !== null && wanted !== "") {
      matched = matched.filter((row) => row[field] === wanted)
    }
  }
  const term = search?.trim().toLowerCase()
  if (term) matched = matched.filter((row) => matchesSearch(row, term, options.search))

  const sortField = (sort_by ?? options.defaultSort) as keyof T
  const direction = sort_desc ? -1 : 1
  const sorted = [...matched].sort((a, b) => compare(a[sortField], b[sortField]) * direction)

  const offset = (page - 1) * limit
  return {
    items: sorted.slice(offset, offset + limit),
    total: sorted.length,
    page,
    limit,
    has_more: offset + limit < sorted.length,
  }
}
