/**
 * The call sites, not just the helper: sign-out and a workspace switch must
 * both reach `clearGlobalSearch`, or a previous session's record results
 * survive into the next one.
 */
import { beforeEach, describe, expect, it, vi } from "vitest"

const mocks = vi.hoisted(() => ({
  clearGlobalSearch: vi.fn(),
  clearQueryCache: vi.fn(),
  logout: vi.fn(),
  clearApiAuth: vi.fn(),
  setTenantId: vi.fn(),
  clearAuthState: vi.fn(),
  setCurrentTenant: vi.fn(),
  setTenantState: vi.fn(),
}))

vi.mock("@/lib/search-state", () => ({ clearGlobalSearch: mocks.clearGlobalSearch }))
vi.mock("@/lib/query-client", () => ({ queryClient: { clear: mocks.clearQueryCache } }))
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
