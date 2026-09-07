import { useCallback, useMemo } from "react"

import { nextSort, type SortState } from "@/components/common/SortHeader"

/** Written to `?sort` when the user cycles a column back to unsorted. */
const UNSORTED = "none"

export interface SortSearch {
  sort?: string
  desc?: boolean
}

/** Narrow view of TanStack's navigate, just the search-writing we need. */
export type NavigateFn = (opts: {
  search: (prev: Record<string, unknown>) => Record<string, unknown>
  replace?: boolean
}) => void

/**
 * Read the sort state the URL is carrying, falling back to the page's default.
 *
 * The explicit `none` marker matters: without it a page that has an
 * `initialSort` could never be returned to its unsorted order, because an
 * absent `?sort` is indistinguishable from "never sorted".
 */
export function readSort(params: SortSearch, initialSort?: SortState): SortState {
  if (params.sort === UNSORTED) return { field: undefined, desc: false }
  if (params.sort) return { field: params.sort, desc: params.desc ?? false }
  return initialSort ?? { field: undefined, desc: false }
}

/**
 * Keep a table's sort in the URL so it survives a reload, the back button, and
 * the trip out to a detail page and back. Local state loses all three.
 *
 * Toggling also clears `page`, because a re-sorted list renumbers its pages and
 * a stale page shows the wrong slice.
 */
export function useUrlSort({
  searchParams,
  navigate,
  initialSort,
}: {
  searchParams: SortSearch
  navigate: NavigateFn
  initialSort?: SortState
}) {
  const initialField = initialSort?.field
  const initialDesc = initialSort?.desc ?? false
  const { sort: sortField, desc } = searchParams
  const sort = useMemo(
    () =>
      readSort(
        { sort: sortField, desc },
        initialField ? { field: initialField, desc: initialDesc } : undefined,
      ),
    [sortField, desc, initialField, initialDesc],
  )

  const toggleSort = useCallback(
    (field: string) => {
      const next = nextSort(sort, field)
      navigate({
        search: (prev) => ({
          ...prev,
          sort: next.field ?? (initialField ? UNSORTED : undefined),
          desc: next.desc || undefined,
          page: undefined,
        }),
        replace: true,
      })
    },
    [navigate, sort, initialField],
  )

  return { sort, toggleSort }
}
