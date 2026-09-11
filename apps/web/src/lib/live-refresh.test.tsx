/**
 * Live refresh: tables must come back fresh, without polling everything.
 *
 * Both halves are easy to undo by accident. Turning window-focus refetching
 * off again is a one-word change, and a poll that keeps firing on a screen
 * nobody is looking at costs a request and a database read every interval.
 */

import { QueryClient, QueryClientProvider } from "@tanstack/react-query"
import { renderHook, waitFor } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { useEntityList } from "@/lib/queries"
import { LIVE_REFRESH_MS, queryClient as appQueryClient } from "@/lib/query-client"

interface Item {
  id: string
}

let client: QueryClient

beforeEach(() => {
  client = new QueryClient({
    defaultOptions: { queries: { retry: false, staleTime: 0, gcTime: 0 } },
  })
})
afterEach(() => client.clear())

function wrapper({ children }: { children: React.ReactNode }) {
  return <QueryClientProvider client={client}>{children}</QueryClientProvider>
}

function page(items: Item[]) {
  return { items, total: items.length, page: 1, limit: 25, has_more: false }
}

describe("app query defaults", () => {
  it("refetches on window focus, so a tab returned to is not showing stale rows", () => {
    expect(appQueryClient.getDefaultOptions().queries?.refetchOnWindowFocus).toBe(true)
  })

  it("keeps a stale time, so focus does not refetch everything every time", () => {
    expect(appQueryClient.getDefaultOptions().queries?.staleTime).toBeGreaterThan(0)
  })

  it("does not poll by default", () => {
    expect(appQueryClient.getDefaultOptions().queries?.refetchInterval).toBeUndefined()
  })
})

describe("useEntityList polling", () => {
  it("refetches on the interval it was given", async () => {
    const listFn = vi.fn().mockResolvedValue(page([{ id: "a" }]))

    renderHook(
      () =>
        useEntityList<Item>({ resource: "widgets", params: {}, listFn, refetchInterval: 50 }),
      { wrapper },
    )

    await waitFor(() => expect(listFn.mock.calls.length).toBeGreaterThan(2), { timeout: 2_000 })
  })

  it("does not poll when no interval was given", async () => {
    const listFn = vi.fn().mockResolvedValue(page([{ id: "a" }]))

    renderHook(() => useEntityList<Item>({ resource: "widgets", params: {}, listFn }), {
      wrapper,
    })

    await waitFor(() => expect(listFn).toHaveBeenCalledTimes(1))
    await new Promise((resolve) => setTimeout(resolve, 400))
    expect(listFn).toHaveBeenCalledTimes(1)
  })

  it("offers an interval long enough not to hammer the API", () => {
    expect(LIVE_REFRESH_MS).toBeGreaterThanOrEqual(15_000)
  })
})
