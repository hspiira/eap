import { useCallback, useEffect, useState } from "react"

import { nextSort, type SortState } from "@/components/common/SortHeader"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"

interface ListSearch {
  search?: string
  new?: boolean
}

/** Narrow view of TanStack's navigate — just the search-writing we need. */
type NavigateFn = (opts: {
  search: (prev: Record<string, unknown>) => Record<string, unknown>
  replace?: boolean
}) => void

/**
 * The state every list page keeps: a debounced search synced to the URL, page
 * and sort, and the `?new=1` handoff that opens the create sheet.
 *
 * `searchParams` and `navigate` are passed in rather than looked up here:
 * TanStack types both on the route literal, so a hook that called them itself
 * would need a cast and would throw away each page's typed search params.
 *
 * `setFilter` is the important one — it writes a filter to the URL and resets to
 * page 1. A filter that doesn't reset the page silently shows the wrong slice.
 */
export function useListPage<S extends ListSearch>({
  searchParams,
  navigate,
  limit = 20,
  initialSort,
}: {
  searchParams: S
  navigate: NavigateFn
  limit?: number
  initialSort?: SortState
}) {
  const [searchInput, setSearchInput] = useState(searchParams.search ?? "")
  const [addOpen, setAddOpen] = useState(false)
  const [page, setPage] = useState(1)
  const [sort, setSort] = useState<SortState>(
    initialSort ?? { field: undefined, desc: false },
  )

  const debounced = useDebouncedValue(searchInput.trim(), 300)
  const activeSearch = debounced || undefined

  // `?new=1` opens the create sheet, then clears itself so a reload doesn't reopen it.
  useEffect(() => {
    if (searchParams.new) {
      setAddOpen(true)
      navigate({ search: (prev) => ({ ...prev, new: undefined }), replace: true })
    }
  }, [searchParams.new, navigate])

  useEffect(() => {
    if (activeSearch !== searchParams.search) {
      navigate({ search: (prev) => ({ ...prev, search: activeSearch }), replace: true })
      setPage(1)
    }
  }, [activeSearch, navigate, searchParams.search])

  const toggleSort = useCallback((field: string) => {
    setSort((prev) => nextSort(prev, field))
    setPage(1)
  }, [])

  /** Write a filter to the URL and go back to page 1. */
  const setFilter = useCallback(
    (key: string, value: string | undefined) => {
      navigate({ search: (prev) => ({ ...prev, [key]: value }), replace: true })
      setPage(1)
    },
    [navigate],
  )

  return {
    searchInput,
    setSearchInput,
    activeSearch,
    addOpen,
    setAddOpen,
    page,
    setPage,
    limit,
    sort,
    toggleSort,
    setFilter,
    /** For `useEntityList` params — sort_by/sort_desc are omitted when unsorted. */
    sortParams: {
      sort_by: sort.field,
      sort_desc: sort.field ? sort.desc : undefined,
    },
  }
}
