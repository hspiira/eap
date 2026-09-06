/**
 * The platform gate must fail closed.
 *
 * It used to read VITE_PLATFORM_TENANT_ID and skip its check when that was
 * unset, so in an unconfigured environment every tenant reached the surface
 * and got a 403 from an API that fails closed. The answer now comes from
 * /auth/me, which is the same rule the API enforces with.
 */

import { screen, waitFor } from "@testing-library/react"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { renderWithProviders } from "@/test/utils"

const mocks = vi.hoisted(() => ({
  me: vi.fn(),
  userId: "user-1" as string | null,
}))

vi.mock("@/api/endpoints/auth", () => ({ authApi: { me: mocks.me } }))
vi.mock("@/components/common/RequireAuth", () => ({
  RequireAuth: ({ children }: { children: React.ReactNode }) => <>{children}</>,
}))
vi.mock("@/store/slices/authSlice", () => ({
  useAuthStore: (selector: (s: { user_id: string | null }) => unknown) =>
    selector({ user_id: mocks.userId }),
}))

const { RequirePlatformAdmin } = await import("@/components/common/RequirePlatformAdmin")

beforeEach(() => {
  vi.clearAllMocks()
  mocks.userId = "user-1"
})

function renderGate() {
  renderWithProviders(
    <RequirePlatformAdmin>
      <div>Tenant administration</div>
    </RequirePlatformAdmin>,
  )
}

describe("RequirePlatformAdmin", () => {
  it("shows the surface to a platform admin", async () => {
    mocks.me.mockResolvedValue({ user_id: "user-1", is_platform_admin: true })
    renderGate()
    expect(await screen.findByText("Tenant administration")).toBeInTheDocument()
  })

  it("refuses a tenant that is not the platform tenant", async () => {
    mocks.me.mockResolvedValue({ user_id: "user-1", is_platform_admin: false })
    renderGate()
    expect(await screen.findByText("Platform admin only")).toBeInTheDocument()
    expect(screen.queryByText("Tenant administration")).not.toBeInTheDocument()
  })

  it("fails closed when the server reports no platform admin at all", async () => {
    // PLATFORM_TENANT_ID unset: the API says nobody qualifies, and the old
    // frontend check skipped itself here and let everyone through.
    mocks.me.mockResolvedValue({ user_id: "user-1" })
    renderGate()
    expect(await screen.findByText("Platform admin only")).toBeInTheDocument()
  })

  it("does not flash the forbidden screen while the answer is in flight", async () => {
    let resolve: (value: unknown) => void = () => {}
    mocks.me.mockReturnValue(
      new Promise((r) => {
        resolve = r
      }),
    )
    renderGate()

    expect(screen.queryByText("Platform admin only")).not.toBeInTheDocument()
    expect(screen.queryByText("Tenant administration")).not.toBeInTheDocument()

    resolve({ user_id: "user-1", is_platform_admin: true })
    await waitFor(() => expect(screen.getByText("Tenant administration")).toBeInTheDocument())
  })
})
