import { fireEvent, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { ProviderFormSheet } from "@/components/providers/ProviderFormSheet"
import { renderWithProviders } from "@/test/utils"
import type { Provider } from "@/types/entities"

const mocks = vi.hoisted(() => ({ create: vi.fn(), update: vi.fn() }))
vi.mock("@/api/endpoints/providers", () => ({
  providersApi: { create: mocks.create, update: mocks.update },
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
  mocks.create.mockResolvedValue(makeProvider())
  mocks.update.mockResolvedValue(makeProvider())
})

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
