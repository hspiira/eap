/**
 * The shared list-page scaffold. Eight server-paginated pages ride on this
 * hook, so its invariants are theirs: a filter or search change must reset
 * to page 1 (the F1 bug family — a stale page shows the wrong slice), and
 * the ?new=1 handoff must clear itself so a reload doesn't reopen the sheet.
 */

import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { useListPage } from '@/hooks/useListPage'

function makeNavigate() {
  const calls: Array<Record<string, unknown>> = []
  const navigate = vi.fn(
    (opts: { search: (prev: Record<string, unknown>) => Record<string, unknown> }) => {
      calls.push(opts.search({}))
    },
  )
  return { navigate, calls }
}

describe('useListPage', () => {
  beforeEach(() => vi.useFakeTimers())
  afterEach(() => vi.useRealTimers())

  it('debounced search writes the URL and resets to page 1', () => {
    const { navigate, calls } = makeNavigate()
    const { result } = renderHook(() =>
      useListPage({ searchParams: {}, navigate }),
    )

    act(() => result.current.setPage(3))
    act(() => result.current.setSearchInput('jane'))
    act(() => void vi.advanceTimersByTime(350))

    expect(calls.at(-1)).toMatchObject({ search: 'jane' })
    expect(result.current.page).toBe(1)
  })

  it('setFilter writes the URL and resets to page 1', () => {
    const { navigate, calls } = makeNavigate()
    const { result } = renderHook(() =>
      useListPage({ searchParams: {}, navigate }),
    )

    act(() => result.current.setPage(4))
    act(() => result.current.setFilter('status', 'Active'))

    expect(calls.at(-1)).toMatchObject({ status: 'Active' })
    expect(result.current.page).toBe(1)
  })

  it('clearing a filter also resets the page', () => {
    const { navigate } = makeNavigate()
    const { result } = renderHook(() =>
      useListPage({ searchParams: { status: 'Active' } as never, navigate }),
    )

    act(() => result.current.setPage(2))
    act(() => result.current.setFilter('status', undefined))

    expect(result.current.page).toBe(1)
  })

  it('?new=1 opens the create sheet and clears itself from the URL', () => {
    const { navigate, calls } = makeNavigate()
    const { result } = renderHook(() =>
      useListPage({ searchParams: { new: true }, navigate }),
    )

    expect(result.current.addOpen).toBe(true)
    expect(calls.at(-1)).toMatchObject({ new: undefined })
  })

  it('toggleSort resets to page 1 and feeds sortParams', () => {
    const { navigate } = makeNavigate()
    const { result } = renderHook(() =>
      useListPage({ searchParams: {}, navigate }),
    )

    act(() => result.current.setPage(5))
    act(() => result.current.toggleSort('name'))

    expect(result.current.page).toBe(1)
    expect(result.current.sortParams).toEqual({ sort_by: 'name', sort_desc: false })
  })

  it('initialSort seeds the first render', () => {
    const { navigate } = makeNavigate()
    const { result } = renderHook(() =>
      useListPage({
        searchParams: {},
        navigate,
        initialSort: { field: 'scheduled_at', desc: true },
      }),
    )

    expect(result.current.sortParams).toEqual({
      sort_by: 'scheduled_at',
      sort_desc: true,
    })
  })
})
