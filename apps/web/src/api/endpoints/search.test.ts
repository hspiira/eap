/**
 * The search term must not reach the URL. It is user-entered text that
 * routinely names a person, and a query string is recorded by the server
 * access log and by every proxy in front of it.
 */
import { beforeEach, describe, expect, it, vi } from "vitest"

const mocks = vi.hoisted(() => ({ post: vi.fn(), get: vi.fn() }))

vi.mock("@/api/client", () => ({ default: { post: mocks.post, get: mocks.get } }))

const { MIN_SEARCH_LENGTH, SEARCH_RESULT_LIMIT, searchApi } = await import("@/api/endpoints/search")

beforeEach(() => {
  vi.clearAllMocks()
  mocks.post.mockResolvedValue({})
})

describe("searchApi.global", () => {
  it("posts the term as a body", async () => {
    await searchApi.global({ q: "nakato", limit: 5 })
    expect(mocks.post).toHaveBeenCalledWith("/search", { q: "nakato", limit: 5 }, undefined)
  })

  it("never issues a GET, which would put the term in a URL", async () => {
    await searchApi.global({ q: "nakato" })
    expect(mocks.get).not.toHaveBeenCalled()
  })

  it("forwards the abort signal for cancellation", async () => {
    const controller = new AbortController()
    await searchApi.global({ q: "nakato" }, { signal: controller.signal })
    expect(mocks.post.mock.calls[0][2]).toEqual({ signal: controller.signal })
  })

  it("agrees with the API on the two-character floor and the page size", () => {
    expect(MIN_SEARCH_LENGTH).toBe(2)
    expect(SEARCH_RESULT_LIMIT).toBe(5)
  })
})
