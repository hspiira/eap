/**
 * AUTH-01, reproduced and then held closed.
 *
 * The diagnostic in MODULES_REPAIR_PLAN.md placed a synthetic case in the
 * shared query cache, called `authActions.logout()`, and read the same case
 * back from `queryClient`. Nothing here mocks the query client: these assert
 * against the real cache, so they fail if the teardown stops reaching it.
 */
import { beforeEach, describe, expect, it, vi } from "vitest"

const mocks = vi.hoisted(() => ({
  logout: vi.fn(),
  clearApiAuth: vi.fn(),
  setTenantId: vi.fn(),
  clearAuthState: vi.fn(),
  setTenantState: vi.fn(),
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
    getState: () => ({ setCurrentTenant: vi.fn() }),
    setState: mocks.setTenantState,
  },
}))

const { queryClient } = await import("@/lib/query-client")
const { authActions } = await import("@/lib/auth-store")
const { resetIdentityState } = await import("@/lib/identity-reset")

/** A protected list key, shaped like the real ones: no tenant, no user in it. */
const CASES_KEY = ["cases", "list"]

beforeEach(() => {
  vi.clearAllMocks()
  mocks.logout.mockResolvedValue(undefined)
  queryClient.clear()
})

describe("signing out", () => {
  it("leaves no cached record for the next identity to read", async () => {
    queryClient.setQueryData(CASES_KEY, [{ id: "case-1", subject: "pseudonym-a" }])
    expect(queryClient.getQueryData(CASES_KEY)).toBeDefined()

    await authActions.logout()

    expect(queryClient.getQueryData(CASES_KEY)).toBeUndefined()
  })

  it("clears the cache even when the server logout fails", async () => {
    mocks.logout.mockRejectedValue(new Error("offline"))
    queryClient.setQueryData(CASES_KEY, [{ id: "case-1" }])

    await authActions.logout()

    expect(queryClient.getQueryData(CASES_KEY)).toBeUndefined()
  })

  it("empties the mutation cache too, not only the query cache", async () => {
    queryClient.getMutationCache().build(queryClient, { mutationFn: async () => "done" })
    expect(queryClient.getMutationCache().getAll()).toHaveLength(1)

    await authActions.logout()

    expect(queryClient.getMutationCache().getAll()).toHaveLength(0)
  })
})

describe("a response that arrives after the identity changed", () => {
  it("does not repopulate the next session's cache", async () => {
    let release: (rows: unknown) => void = () => {}
    const slow = new Promise((resolve) => {
      release = resolve
    })

    const inFlight = queryClient
      .fetchQuery({ queryKey: CASES_KEY, queryFn: () => slow })
      .catch(() => undefined)

    await resetIdentityState()

    // The old session's request only now comes back.
    release([{ id: "case-1", subject: "pseudonym-a" }])
    await inFlight

    expect(queryClient.getQueryData(CASES_KEY)).toBeUndefined()
  })
})
