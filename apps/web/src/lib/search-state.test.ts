import { beforeEach, describe, expect, it, vi } from "vitest"

const mocks = vi.hoisted(() => ({
  cancelQueries: vi.fn(),
  removeQueries: vi.fn(),
}))

vi.mock("@/lib/query-client", () => ({
  queryClient: { cancelQueries: mocks.cancelQueries, removeQueries: mocks.removeQueries },
}))

const {
  clearGlobalSearch,
  GLOBAL_SEARCH_KEY,
  globalSearchQueryKey,
  openGlobalSearch,
  onGlobalSearchToggle,
} = await import("@/lib/search-state")

beforeEach(() => {
  vi.clearAllMocks()
  mocks.cancelQueries.mockResolvedValue(undefined)
})

describe("cache scoping", () => {
  it("keys results by identity and tenant, so a new session cannot read them", () => {
    const a = globalSearchQueryKey({ userId: "u-1", tenantId: "t-1" }, "acme", 5)
    const b = globalSearchQueryKey({ userId: "u-2", tenantId: "t-1" }, "acme", 5)
    const c = globalSearchQueryKey({ userId: "u-1", tenantId: "t-2" }, "acme", 5)
    expect(a).not.toEqual(b)
    expect(a).not.toEqual(c)
  })

  it("keys results by the query, so an older query's rows are a different entry", () => {
    const scope = { userId: "u-1", tenantId: "t-1" }
    expect(globalSearchQueryKey(scope, "acme", 5)).not.toEqual(
      globalSearchQueryKey(scope, "acme h", 5),
    )
  })

  it("shares one prefix so the whole set can be dropped at once", () => {
    const key = globalSearchQueryKey({ userId: "u-1", tenantId: "t-1" }, "acme", 5)
    expect(key.slice(0, 2)).toEqual(GLOBAL_SEARCH_KEY)
  })
})

describe("teardown", () => {
  it("cancels in-flight searches before dropping them", async () => {
    await clearGlobalSearch()
    expect(mocks.cancelQueries).toHaveBeenCalledWith({ queryKey: GLOBAL_SEARCH_KEY })
    expect(mocks.removeQueries).toHaveBeenCalledWith({ queryKey: GLOBAL_SEARCH_KEY })
    expect(mocks.cancelQueries.mock.invocationCallOrder[0]).toBeLessThan(
      mocks.removeQueries.mock.invocationCallOrder[0],
    )
  })
})

describe("launcher signal", () => {
  it("notifies a subscriber and stops after unsubscribing", () => {
    const handler = vi.fn()
    const off = onGlobalSearchToggle(handler)
    openGlobalSearch()
    expect(handler).toHaveBeenCalledTimes(1)
    off()
    openGlobalSearch()
    expect(handler).toHaveBeenCalledTimes(1)
  })
})
