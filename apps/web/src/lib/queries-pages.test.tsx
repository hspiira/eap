/**
 * The list that grows as the user scrolls.
 *
 * Two things here are easy to get wrong and expensive when wrong: the next
 * page must be counted from the page that was asked for rather than the one
 * the response echoes back (an endpoint paged by offset has no page number to
 * echo), and appending must be held back while placeholder rows from the
 * previous filter are still on screen, or rows the user just filtered out are
 * spliced back into the table.
 */

import { renderHook, waitFor } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"

import { useEntityListPages } from "@/lib/queries"
import { TestProviders } from "@/test/utils"
import type { ListParams, PaginatedResponse } from "@/types/api"

interface Row {
  id: string
}

/** A fake endpoint over `count` rows, paged the ordinary way. */
function pagedApi(count: number, limit = 2) {
  return vi.fn(async (params: ListParams): Promise<PaginatedResponse<Row>> => {
    const page = params.page ?? 1
    const start = (page - 1) * limit
    const items = Array.from({ length: Math.max(0, Math.min(limit, count - start)) }, (_, i) => ({
      id: `row-${start + i + 1}`,
    }))
    return { items, total: count, page, limit, has_more: start + items.length < count }
  })
}

function render(listFn: ReturnType<typeof pagedApi>, params: ListParams, extra = {}) {
  return renderHook(() => useEntityListPages<Row>({ resource: "rows", params, listFn, ...extra }), {
    wrapper: TestProviders,
  })
}

describe("useEntityListPages", () => {
  it("starts at the anchor page rather than always at page one", async () => {
    const listFn = pagedApi(6)
    const { result } = render(listFn, { page: 3, limit: 2 })

    await waitFor(() => expect(result.current.data?.items).toHaveLength(2))
    expect(result.current.data?.items.map((r) => r.id)).toEqual(["row-5", "row-6"])
  })

  it("appends the next page instead of replacing the rows on screen", async () => {
    const listFn = pagedApi(6)
    const { result } = render(listFn, { page: 1, limit: 2 })

    await waitFor(() => expect(result.current.data?.items).toHaveLength(2))
    result.current.loadMore()

    await waitFor(() => expect(result.current.data?.items).toHaveLength(4))
    expect(result.current.data?.items.map((r) => r.id)).toEqual([
      "row-1",
      "row-2",
      "row-3",
      "row-4",
    ])
  })

  it("stops once the last page has been reached", async () => {
    const listFn = pagedApi(3)
    const { result } = render(listFn, { page: 1, limit: 2 })

    await waitFor(() => expect(result.current.hasMore).toBe(true))
    result.current.loadMore()

    await waitFor(() => expect(result.current.data?.items).toHaveLength(3))
    await waitFor(() => expect(result.current.hasMore).toBe(false))
  })

  it("counts pages from the request when the endpoint pages by offset", async () => {
    const limit = 2
    const listFn = vi.fn(async (params: ListParams): Promise<PaginatedResponse<Row>> => {
      const offset = (params.offset as number | undefined) ?? 0
      const items = Array.from({ length: Math.min(limit, 6 - offset) }, (_, i) => ({
        id: `row-${offset + i + 1}`,
      }))
      // No usable page number in the response, which is the point.
      return { items, total: 6, page: 1, limit, has_more: offset + items.length < 6 }
    })

    const { result } = renderHook(
      () =>
        useEntityListPages<Row>({
          resource: "rows",
          params: { limit, offset: 0 } as ListParams,
          listFn,
          anchorPage: 1,
          pageParams: (next) => ({ offset: (next - 1) * limit }),
        }),
      { wrapper: TestProviders },
    )

    await waitFor(() => expect(result.current.data?.items).toHaveLength(2))
    result.current.loadMore()

    await waitFor(() => expect(result.current.data?.items).toHaveLength(4))
    expect(result.current.data?.items.map((r) => r.id)).toEqual([
      "row-1",
      "row-2",
      "row-3",
      "row-4",
    ])
    expect(listFn.mock.calls.at(-1)?.[0]).toMatchObject({ offset: 2 })
  })

  it("reports the total from the newest page, not the page it started on", async () => {
    const listFn = vi.fn(async (params: ListParams): Promise<PaginatedResponse<Row>> => {
      const page = params.page ?? 1
      // The count moves between requests, as it does on a live list.
      return {
        items: [{ id: `row-${page}` }],
        total: page === 1 ? 90 : 91,
        page,
        limit: 1,
        has_more: true,
      }
    })
    const { result } = render(listFn as ReturnType<typeof pagedApi>, { page: 1, limit: 1 })

    await waitFor(() => expect(result.current.data?.total).toBe(90))
    result.current.loadMore()

    await waitFor(() => expect(result.current.data?.total).toBe(91))
  })
})
