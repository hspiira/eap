/**
 * The shared list-page scaffold. Ten server-paginated pages ride on this hook,
 * so its invariants are theirs: search, page and sort live in the URL so they
 * survive a reload and the trip out to a detail row, a filter or search change
 * must reset to page 1 (the F1 bug family: a stale page shows the wrong slice),
 * and the ?new=1 handoff must clear itself so a reload doesn't reopen the sheet.
 */

import { act, renderHook } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { useListPage } from "@/hooks/useListPage"

function makeNavigate(current: Record<string, unknown> = {}) {
  const calls: Array<Record<string, unknown>> = []
  const navigate = vi.fn(
    (opts: { search: (prev: Record<string, unknown>) => Record<string, unknown> }) => {
      calls.push(opts.search(current))
    },
  )
  return { navigate, calls }
}

describe("useListPage", () => {
  beforeEach(() => vi.useFakeTimers())
  afterEach(() => vi.useRealTimers())

  it("debounced search writes the URL and resets to page 1", () => {
    const { navigate, calls } = makeNavigate({ page: 3 })
    const { result } = renderHook(() => useListPage({ searchParams: { page: 3 }, navigate }))

    act(() => result.current.setSearchInput("jane"))
    act(() => void vi.advanceTimersByTime(350))

    expect(calls.at(-1)).toMatchObject({ search: "jane", page: undefined })
  })

  it("setFilter writes the URL and resets to page 1", () => {
    const { navigate, calls } = makeNavigate({ page: 4 })
    const { result } = renderHook(() => useListPage({ searchParams: { page: 4 }, navigate }))

    act(() => result.current.setFilter("status", "Active"))

    expect(calls.at(-1)).toMatchObject({ status: "Active", page: undefined })
  })

  it("clearing a filter also resets the page", () => {
    const { navigate, calls } = makeNavigate({ status: "Active", page: 2 })
    const { result } = renderHook(() =>
      useListPage({ searchParams: { status: "Active", page: 2 } as never, navigate }),
    )

    act(() => result.current.setFilter("status", undefined))

    expect(calls.at(-1)).toMatchObject({ status: undefined, page: undefined })
  })

  it("reads the page off the URL and leaves page 1 out of it", () => {
    const { navigate, calls } = makeNavigate()
    const { result } = renderHook(() => useListPage({ searchParams: { page: 3 }, navigate }))

    expect(result.current.page).toBe(3)

    act(() => result.current.setPage(1))
    expect(calls.at(-1)).toMatchObject({ page: undefined })
  })

  it("?new=1 opens the create sheet and clears itself from the URL", () => {
    const { navigate, calls } = makeNavigate()
    const { result } = renderHook(() => useListPage({ searchParams: { new: true }, navigate }))

    expect(result.current.addOpen).toBe(true)
    expect(calls.at(-1)).toMatchObject({ new: undefined })
  })

  it("toggleSort writes the sort to the URL and resets to page 1", () => {
    const { navigate, calls } = makeNavigate({ page: 5 })
    const { result } = renderHook(() => useListPage({ searchParams: { page: 5 }, navigate }))

    act(() => result.current.toggleSort("name"))

    expect(calls.at(-1)).toMatchObject({ sort: "name", desc: undefined, page: undefined })
  })

  it("a sort in the URL feeds sortParams", () => {
    const { navigate } = makeNavigate()
    const { result } = renderHook(() =>
      useListPage({ searchParams: { sort: "name", desc: true }, navigate }),
    )

    expect(result.current.sortParams).toEqual({ sort_by: "name", sort_desc: true })
  })

  it("initialSort applies until the URL says otherwise", () => {
    const { navigate } = makeNavigate()
    const { result, rerender } = renderHook(
      ({ searchParams }) =>
        useListPage({
          searchParams,
          navigate,
          initialSort: { field: "scheduled_at", desc: true },
        }),
      { initialProps: { searchParams: {} as { sort?: string; desc?: boolean } } },
    )

    expect(result.current.sortParams).toEqual({ sort_by: "scheduled_at", sort_desc: true })

    rerender({ searchParams: { sort: "name" } })
    expect(result.current.sortParams).toEqual({ sort_by: "name", sort_desc: false })
  })

  it("cycling a defaulted column off records the unsorted state in the URL", () => {
    const { navigate, calls } = makeNavigate()
    const { result } = renderHook(() =>
      useListPage({
        searchParams: { sort: "name", desc: true },
        navigate,
        initialSort: { field: "name", desc: false },
      }),
    )

    act(() => result.current.toggleSort("name"))

    expect(calls.at(-1)).toMatchObject({ sort: "none", desc: undefined })
  })
})
