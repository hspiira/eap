import { useCallback, useEffect, useState } from "react"

import type { SortState } from "@/components/common/SortHeader"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import { type NavigateFn, type SortSearch, useUrlSort } from "@/hooks/useUrlSort"

interface ListSearch extends SortSearch {
  search?: string
  new?: boolean
  page?: number
}

/**
 * The state every list page keeps: a debounced search, page and sort, and the
 * `?new=1` handoff that opens the create sheet.
 *
 * Search, page and sort all live in the URL. That is what makes them survive a
 * reload, the back button, and the trip out to a detail row and back; local
 * state silently drops the user's sort the moment they open a record.
 *
 * `searchParams` and `navigate` are passed in rather than looked up here:
 * TanStack types both on the route literal, so a hook that called them itself
 * would need a cast and would throw away each page's typed search params.
 *
 * `setFilter` is the important one; it writes a filter to the URL and resets to
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
  const { sort, toggleSort } = useUrlSort({ searchParams, navigate, initialSort })
  const page = searchParams.page ?? 1

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
      navigate({
        search: (prev) => ({ ...prev, search: activeSearch, page: undefined }),
        replace: true,
      })
    }
  }, [activeSearch, navigate, searchParams.search])

  /** Page 1 leaves no trace in the query string. */
  const setPage = useCallback(
    (next: number) => {
      navigate({
        search: (prev) => ({ ...prev, page: next > 1 ? next : undefined }),
        replace: true,
      })
    },
    [navigate],
  )

  /** Write a filter to the URL and go back to page 1. */
  const setFilter = useCallback(
    (key: string, value: string | undefined) => {
      navigate({ search: (prev) => ({ ...prev, [key]: value, page: undefined }), replace: true })
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
    /** For `useEntityList` params: sort_by/sort_desc are omitted when unsorted. */
    sortParams: {
      sort_by: sort.field,
      sort_desc: sort.field ? sort.desc : undefined,
    },
  }
}
