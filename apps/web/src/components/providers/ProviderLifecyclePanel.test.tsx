import { fireEvent, screen, waitFor } from "@testing-library/react"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { ProviderAccountCard } from "@/components/providers/ProviderAccountCard"
import { ProviderLifecyclePanel } from "@/components/providers/ProviderLifecyclePanel"
import { renderWithProviders } from "@/test/utils"
import type { Provider } from "@/types/entities"

const mocks = vi.hoisted(() => ({
  changeTier: vi.fn(),
  changePanelStatus: vi.fn(),
  changeAccreditation: vi.fn(),
  changeStatus: vi.fn(),
  linkAccount: vi.fn(),
  unlinkAccount: vi.fn(),
  getUser: vi.fn(),
  role: "Admin",
}))
vi.mock("@/api/endpoints/providers", () => ({ providersApi: mocks }))
vi.mock("@/api/endpoints/users", () => ({ usersApi: { getById: mocks.getUser } }))
vi.mock("@/hooks/useCanWrite", () => ({
  useCanWrite: () => mocks.role !== "Viewer",
  useCurrentRole: () => mocks.role,
}))
vi.mock("@tanstack/react-router", () => ({
  Link: ({ children, to: _to, params: _params, ...rest }: Record<string, unknown>) => (
    <a href={_to as string} {...rest}>
      {children as React.ReactNode}
    </a>
  ),
}))
vi.mock("@/components/common/EntityPicker", () => ({
  UserPicker: ({ onChange }: { onChange: (id: string) => void }) => (
    <button type="button" onClick={() => onChange("usr-1")}>
      Pick account
    </button>
  ),
}))

function makeProvider(overrides: Partial<Provider> = {}): Provider {
  return {
    id: "prv-1",
    tenant_id: "tenant-1",
    display_name: "Amina Okello",
    email: null,
    phone: null,
    user_id: null,
    status: "Active",
    provider_profile: {
      tier: "T2",
      region: "Central",
      accreditation_status: "Accredited",
      panel_status: "Active",
      specialties: [],
    },
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  } as Provider
}

beforeEach(() => {
  vi.clearAllMocks()
  mocks.role = "Admin"
  mocks.changePanelStatus.mockResolvedValue(makeProvider())
  mocks.linkAccount.mockResolvedValue(makeProvider({ user_id: "usr-1" }))
  mocks.unlinkAccount.mockResolvedValue(makeProvider())
  mocks.getUser.mockResolvedValue({
    id: "usr-1",
    display_name: "Amina",
    email: "amina@example.test",
    status: "Active",
  })
})

describe("practitioner lifecycle commands", () => {
  it("will not send a command until a reason is given", async () => {
    renderWithProviders(<ProviderLifecyclePanel provider={makeProvider()} onChanged={() => {}} />)
    fireEvent.click(screen.getByRole("button", { name: /change panel status/i }))

    const confirm = await screen.findByRole("button", { name: /^change panel status$/i })
    expect(confirm).toBeDisabled()

    fireEvent.change(screen.getByLabelText(/reason/i), { target: { value: "   " } })
    expect(confirm).toBeDisabled()
    expect(mocks.changePanelStatus).not.toHaveBeenCalled()
  })

  it("sends the reason with the command", async () => {
    renderWithProviders(<ProviderLifecyclePanel provider={makeProvider()} onChanged={() => {}} />)
    fireEvent.click(screen.getByRole("button", { name: /change panel status/i }))
    fireEvent.change(await screen.findByLabelText(/reason/i), {
      target: { value: "Complaint under review" },
    })
    fireEvent.click(screen.getByRole("button", { name: /^change panel status$/i }))

    await waitFor(() => expect(mocks.changePanelStatus).toHaveBeenCalled())
    expect(mocks.changePanelStatus).toHaveBeenCalledWith("prv-1", {
      panel_status: "Active",
      reason: "Complaint under review",
    })
  })

  it("shows no command buttons to a non-admin", async () => {
    mocks.role = "User"
    renderWithProviders(<ProviderLifecyclePanel provider={makeProvider()} onChanged={() => {}} />)
    expect(screen.queryByRole("button", { name: /change panel status/i })).not.toBeInTheDocument()
    expect(screen.getByText(/changed by a tenant admin/i)).toBeInTheDocument()
  })

  it("says an absent accreditation expiry is not on record", () => {
    renderWithProviders(<ProviderLifecyclePanel provider={makeProvider()} onChanged={() => {}} />)
    expect(screen.getByText("No expiry on record")).toBeInTheDocument()
  })
})

describe("practitioner account link", () => {
  it("links an account with a reason, as an admin", async () => {
    renderWithProviders(<ProviderAccountCard provider={makeProvider()} onChanged={() => {}} />)

    fireEvent.click(screen.getByRole("button", { name: /pick account/i }))
    fireEvent.click(screen.getByRole("button", { name: /^link account$/i }))
    fireEvent.change(await screen.findByLabelText(/reason/i), {
      target: { value: "Verified with HR" },
    })
    fireEvent.click(screen.getAllByRole("button", { name: /^link account$/i }).at(-1)!)

    await waitFor(() => expect(mocks.linkAccount).toHaveBeenCalled())
    expect(mocks.linkAccount).toHaveBeenCalledWith("prv-1", {
      user_id: "usr-1",
      reason: "Verified with HR",
    })
  })

  it("gives a non-admin no way to link or unlink", () => {
    mocks.role = "User"
    renderWithProviders(<ProviderAccountCard provider={makeProvider()} onChanged={() => {}} />)
    expect(screen.queryByRole("button", { name: /pick account/i })).not.toBeInTheDocument()
    expect(screen.getByText(/a tenant admin can link one/i)).toBeInTheDocument()
  })

  it("keeps the practitioner visible when the linked account cannot be read", async () => {
    mocks.getUser.mockRejectedValue(new Error("gone"))
    renderWithProviders(
      <ProviderAccountCard provider={makeProvider({ user_id: "usr-1" })} onChanged={() => {}} />,
    )
    expect(
      await screen.findByText(/practitioner and their sessions are unaffected/i),
    ).toBeInTheDocument()
  })
})
