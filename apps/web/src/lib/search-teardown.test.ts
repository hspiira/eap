/**
 * The call sites, not just the helper: every identity change must reach
 * `resetIdentityState`, or the previous session's cached results survive into
 * the next one. AUTH-01 was exactly this: logout cleared the auth and tenant
 * stores and left the query cache untouched.
 */
import { beforeEach, describe, expect, it, vi } from "vitest"

const mocks = vi.hoisted(() => ({
  clearGlobalSearch: vi.fn(),
  clearQueryCache: vi.fn(),
  cancelQueries: vi.fn(),
  logout: vi.fn(),
  clearApiAuth: vi.fn(),
  setTenantId: vi.fn(),
  clearAuthState: vi.fn(),
  setCurrentTenant: vi.fn(),
  setTenantState: vi.fn(),
}))

vi.mock("@/lib/search-state", () => ({ clearGlobalSearch: mocks.clearGlobalSearch }))
vi.mock("@/lib/query-client", () => ({
  queryClient: { clear: mocks.clearQueryCache, cancelQueries: mocks.cancelQueries },
}))
vi.mock("@/api/client", () => ({
  default: { clearAuth: mocks.clearApiAuth, setTenantId: mocks.setTenantId },
}))
vi.mock("@/api/endpoints/auth", () => ({ authApi: { logout: mocks.logout } }))
vi.mock("@/api/endpoints/tenants", () => ({ tenantsApi: {} }))
vi.mock("@/store/slices/authSlice", () => ({
  useAuthStore: { getState: () => ({ clearAuth: mocks.clearAuthState }) },
}))
vi.mock("@/store/slices/tenantSlice", () => ({
  useTenantStore: {
    getState: () => ({ setCurrentTenant: mocks.setCurrentTenant }),
    setState: mocks.setTenantState,
  },
}))

const { authActions } = await import("@/lib/auth-store")
const { tenantActions } = await import("@/lib/tenant-actions")

beforeEach(() => {
  vi.clearAllMocks()
  mocks.logout.mockResolvedValue(undefined)
  mocks.clearGlobalSearch.mockResolvedValue(undefined)
  mocks.cancelQueries.mockResolvedValue(undefined)
})

describe("sign out", () => {
  it("clears cached record searches", async () => {
    await authActions.logout()
    expect(mocks.clearGlobalSearch).toHaveBeenCalled()
  })

  it("still clears them when the server logout fails", async () => {
    mocks.logout.mockRejectedValue(new Error("offline"))
    await authActions.logout()
    expect(mocks.clearGlobalSearch).toHaveBeenCalled()
  })
})

describe("workspace switch", () => {
  it("clears cached record searches", () => {
    tenantActions.setCurrentTenant({ id: "t-2", name: "Other" } as never)
    expect(mocks.clearGlobalSearch).toHaveBeenCalled()
  })

  it("also clears them when the workspace is cleared entirely", () => {
    tenantActions.setCurrentTenant(null)
    expect(mocks.clearGlobalSearch).toHaveBeenCalled()
  })
})

describe("identity teardown reaches the query cache, not only the search cache", () => {
  it("sign-out empties the query cache", async () => {
    await authActions.logout()
    expect(mocks.clearQueryCache).toHaveBeenCalled()
  })

  /**
   * A request already in flight for the old session would otherwise resolve
   * after the teardown and write the old tenant's rows into the new session's
   * cache. Both calls sit in one synchronous block, so nothing can land
   * between them.
   */
  it("sign-out also cancels whatever is still in flight", async () => {
    await authActions.logout()
    expect(mocks.cancelQueries).toHaveBeenCalled()
  })

  /**
   * A workspace switch is synchronous and the next render happens immediately,
   * so the cache has to be empty by the time it returns rather than one
   * microtask later.
   */
  it("a workspace switch empties the cache before it returns", () => {
    tenantActions.setCurrentTenant({ id: "t-2", name: "Other" } as never)
    expect(mocks.clearQueryCache).toHaveBeenCalled()
  })

  it("a workspace switch empties the query cache", () => {
    tenantActions.setCurrentTenant({ id: "t-2", name: "Other" } as never)
    expect(mocks.clearQueryCache).toHaveBeenCalled()
  })
})
