import { fireEvent, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { ProviderFormSheet } from "@/components/providers/ProviderFormSheet"
import { renderWithProviders } from "@/test/utils"
import type { Provider } from "@/types/entities"

const mocks = vi.hoisted(() => ({
  create: vi.fn(),
  update: vi.fn(),
  adopt: vi.fn(),
  role: "Admin" as string,
  showSuccess: vi.fn(),
  showError: vi.fn(),
}))
vi.mock("@/api/endpoints/providers", () => ({
  providersApi: { create: mocks.create, update: mocks.update },
}))
vi.mock("@/api/endpoints/provider-aliases", () => ({
  providerAliasesApi: { adopt: mocks.adopt },
}))
vi.mock("@/hooks/useCanWrite", () => ({
  useCanWrite: () => true,
  useCurrentRole: () => mocks.role,
}))
vi.mock("@/store/slices/tenantSlice", () => ({
  useTenantStore: (select: (s: { currentTenantId: string }) => unknown) =>
    select({ currentTenantId: "tenant-1" }),
}))
// Partial: the test wrapper still renders the real ToastProvider.
vi.mock("@/contexts/ToastContext", async (importOriginal) => ({
  ...(await importOriginal<object>()),
  useToast: () => ({ showSuccess: mocks.showSuccess, showError: mocks.showError }),
}))

const PROTECTED_KEYS = [
  "provider_profile",
  "specialties",
  "tier",
  "panel_status",
  "accreditation_status",
  "accreditation_authority",
  "accreditation_expiry",
  "status",
  "user_id",
]

function makeProvider(overrides: Partial<Provider> = {}): Provider {
  return {
    id: "prv-1",
    tenant_id: "tenant-1",
    display_name: "Amina Okello",
    email: "amina@example.test",
    phone: "+256700000000",
    user_id: null,
    status: "Active",
    provider_profile: {
      tier: "T2",
      region: "Central",
      accreditation_status: "Accredited",
      panel_status: "Active",
      specialties: ["Trauma"],
      bio: "Ten years in trauma counselling.",
    },
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  } as Provider
}

beforeEach(() => {
  vi.clearAllMocks()
  mocks.role = "Admin"
  mocks.create.mockResolvedValue(makeProvider())
  mocks.update.mockResolvedValue(makeProvider())
  mocks.adopt.mockResolvedValue({ alias: { id: "alias-1" }, claimed: true })
})

/** Fill the required name and submit the create form. */
function createNamed(name = "Amina Okello") {
  fireEvent.change(screen.getByLabelText(/display name/i), { target: { value: name } })
  fireEvent.click(screen.getByRole("button", { name: /create practitioner/i }))
}

describe("practitioner form", () => {
  it("creates a practitioner with no contact details and no account", async () => {
    renderWithProviders(<ProviderFormSheet open onOpenChange={() => {}} />)

    fireEvent.change(screen.getByLabelText(/display name/i), {
      target: { value: "  Amina Okello  " },
    })
    fireEvent.click(screen.getByRole("button", { name: /create practitioner/i }))

    await waitFor(() => expect(mocks.create).toHaveBeenCalled())
    const body = mocks.create.mock.calls[0][0]
    expect(body.display_name).toBe("Amina Okello")
    expect(body.email).toBeNull()
    expect(body.phone).toBeNull()
    expect(body).not.toHaveProperty("user_id")
  })

  it("does not touch aliases unless the box is ticked", async () => {
    renderWithProviders(<ProviderFormSheet open onOpenChange={() => {}} />)
    createNamed()
    await waitFor(() => expect(mocks.create).toHaveBeenCalled())
    expect(mocks.adopt).not.toHaveBeenCalled()
  })

  it("names the new practitioner for the spelling just typed when asked", async () => {
    renderWithProviders(<ProviderFormSheet open onOpenChange={() => {}} />)
    fireEvent.click(screen.getByLabelText(/match this name in imported activity logs/i))
    createNamed()

    await waitFor(() => expect(mocks.adopt).toHaveBeenCalled())
    expect(mocks.adopt).toHaveBeenCalledWith(
      "tenant-1",
      "activity-log-workbook",
      "Amina Okello",
      "prv-1",
    )
  })

  it("says so rather than silently stealing a name already resolved elsewhere", async () => {
    mocks.adopt.mockResolvedValue({ alias: { id: "alias-1" }, claimed: false })
    renderWithProviders(<ProviderFormSheet open onOpenChange={() => {}} />)
    fireEvent.click(screen.getByLabelText(/match this name in imported activity logs/i))
    createNamed()

    await waitFor(() => expect(mocks.showSuccess).toHaveBeenCalled())
    expect(mocks.showSuccess.mock.calls[0][0]).toMatch(/already resolved to another practitioner/i)
  })

  it("keeps the created practitioner when the alias step fails", async () => {
    mocks.adopt.mockRejectedValue(new Error("403"))
    renderWithProviders(<ProviderFormSheet open onOpenChange={() => {}} />)
    fireEvent.click(screen.getByLabelText(/match this name in imported activity logs/i))
    createNamed()

    await waitFor(() => expect(mocks.showError).toHaveBeenCalled())
    expect(mocks.create).toHaveBeenCalled()
    expect(mocks.showError.mock.calls[0][0]).toMatch(/Practitioner created/i)
  })

  it("hides the option from a non-admin, whom the alias API refuses", async () => {
    mocks.role = "User"
    renderWithProviders(<ProviderFormSheet open onOpenChange={() => {}} />)
    expect(
      screen.queryByLabelText(/match this name in imported activity logs/i),
    ).not.toBeInTheDocument()
  })

  it("does not offer the option when editing, where the typed name may be a rename", async () => {
    renderWithProviders(
      <ProviderFormSheet open onOpenChange={() => {}} provider={makeProvider()} />,
    )
    expect(
      screen.queryByLabelText(/match this name in imported activity logs/i),
    ).not.toBeInTheDocument()
  })

  it("sends the title as its own field, never folded into the name", async () => {
    const user = userEvent.setup()
    renderWithProviders(<ProviderFormSheet open onOpenChange={() => {}} />)

    fireEvent.change(screen.getByLabelText(/display name/i), { target: { value: "Amina Okello" } })
    await user.click(screen.getByLabelText(/^title$/i))
    await user.click(await screen.findByRole("option", { name: "Dr" }))
    fireEvent.click(screen.getByRole("button", { name: /create practitioner/i }))

    await waitFor(() => expect(mocks.create).toHaveBeenCalled())
    const body = mocks.create.mock.calls[0][0]
    expect(body.title).toBe("Dr")
    expect(body.display_name).toBe("Amina Okello")
  })

  it("requires a name", async () => {
    renderWithProviders(<ProviderFormSheet open onOpenChange={() => {}} />)
    fireEvent.click(screen.getByRole("button", { name: /create practitioner/i }))
    expect(await screen.findByText(/a practitioner needs a name/i)).toBeInTheDocument()
    expect(mocks.create).not.toHaveBeenCalled()
  })

  it("clears an optional contact by emptying the field", async () => {
    renderWithProviders(
      <ProviderFormSheet open onOpenChange={() => {}} provider={makeProvider()} />,
    )

    fireEvent.change(await screen.findByLabelText(/contact email/i), { target: { value: "" } })
    fireEvent.change(screen.getByLabelText(/contact phone/i), { target: { value: "" } })
    fireEvent.click(screen.getByRole("button", { name: /save changes/i }))

    await waitFor(() => expect(mocks.update).toHaveBeenCalled())
    const body = mocks.update.mock.calls[0][1]
    expect(body.email).toBeNull()
    expect(body.phone).toBeNull()
  })

  it("sends no lifecycle field on a general edit, not even unchanged", async () => {
    renderWithProviders(
      <ProviderFormSheet open onOpenChange={() => {}} provider={makeProvider()} />,
    )

    fireEvent.change(await screen.findByLabelText(/display name/i), {
      target: { value: "Amina N. Okello" },
    })
    fireEvent.click(screen.getByRole("button", { name: /save changes/i }))

    await waitFor(() => expect(mocks.update).toHaveBeenCalled())
    const body = mocks.update.mock.calls[0][1]
    for (const key of PROTECTED_KEYS) {
      expect(body, `general edit must not send ${key}`).not.toHaveProperty(key)
    }
    expect(Object.keys(body).sort()).toEqual([
      "bio",
      "display_name",
      "email",
      "gender",
      "phone",
      "region",
      "title",
    ])
  })

  it("offers no tier control on edit, because tier is a lifecycle command", async () => {
    renderWithProviders(
      <ProviderFormSheet open onOpenChange={() => {}} provider={makeProvider()} />,
    )
    await screen.findByLabelText(/display name/i)
    expect(screen.queryByLabelText(/^tier$/i)).not.toBeInTheDocument()
  })

  it("rejects a malformed contact email before sending it", async () => {
    renderWithProviders(<ProviderFormSheet open onOpenChange={() => {}} />)
    fireEvent.change(screen.getByLabelText(/display name/i), { target: { value: "Amina" } })
    fireEvent.change(screen.getByLabelText(/contact email/i), { target: { value: "not-an-email" } })
    fireEvent.click(screen.getByRole("button", { name: /create practitioner/i }))
    expect(await screen.findByText(/valid email address/i)).toBeInTheDocument()
    expect(mocks.create).not.toHaveBeenCalled()
  })
})
