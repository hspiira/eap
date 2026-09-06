import { fireEvent, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { ServiceSessionFormSheet } from "@/components/ServiceSessionFormSheet"
import { renderWithProviders } from "@/test/utils"
import { ApiError } from "@/types/api"

const createMock = vi.fn()
const listServicesMock = vi.fn().mockResolvedValue({ items: [], total: 0 })
const listMembersMock = vi.fn().mockResolvedValue({ items: [], total: 0 })
const listProvidersMock = vi.fn()
const listAffiliationsMock = vi.fn()

vi.mock("@/api/endpoints/service-sessions", () => ({
  serviceSessionsApi: {
    create: (...args: unknown[]) => createMock(...args),
  },
}))

vi.mock("@/api/endpoints/services", () => ({
  servicesApi: {
    list: (...args: unknown[]) => listServicesMock(...args),
  },
}))

vi.mock("@/api/endpoints/members", () => ({
  membersApi: {
    list: (...args: unknown[]) => listMembersMock(...args),
  },
}))

vi.mock("@/api/endpoints/providers", () => ({
  providersApi: {
    list: (...args: unknown[]) => listProvidersMock(...args),
  },
}))

vi.mock("@/api/endpoints/provider-affiliations", () => ({
  providerAffiliationsApi: {
    list: (...args: unknown[]) => listAffiliationsMock(...args),
  },
}))

beforeEach(() => {
  createMock.mockReset()
  listServicesMock.mockClear()
  listMembersMock.mockClear()
  listProvidersMock.mockClear()
  listAffiliationsMock.mockClear()
  listProvidersMock.mockResolvedValue({
    items: [
      {
        id: "prov-1",
        display_name: "Dr Alice Nakato",
        email: "alice.nakato@example.com",
        phone: null,
        user_id: null,
        status: "Active",
        provider_profile: {
          tier: "T2",
          region: "KampalaMetro",
          accreditation_status: "Accredited",
          panel_status: "Active",
          specialties: [],
        },
      },
    ],
    total: 1,
    page: 1,
    limit: 8,
    has_more: false,
  })
  listAffiliationsMock.mockResolvedValue({
    items: [],
    total: 0,
    page: 1,
    limit: 100,
    has_more: false,
  })
})
afterEach(() => {
  createMock.mockReset()
})

/** A practitioner is required, so every create-path test has to choose one. */
async function choosePractitioner() {
  const search = screen.getByPlaceholderText(/search practitioners/i)
  fireEvent.change(search, { target: { value: "Nakato" } })
  await new Promise((r) => setTimeout(r, 400))

  const option = await screen.findByText("Dr Alice Nakato")
  fireEvent.click(option)
}

/** Delivery context has no default, so a create-path test has to choose one. */
async function chooseDirectDelivery() {
  const user = userEvent.setup()
  await user.click(screen.getByRole("combobox", { name: /delivered through/i }))
  await user.click(await screen.findByRole("option", { name: "Direct" }))
}

describe("ServiceSessionFormSheet: create", () => {
  it("rejects empty submission with field errors", async () => {
    renderWithProviders(<ServiceSessionFormSheet open onOpenChange={() => {}} />)

    fireEvent.click(screen.getByRole("button", { name: /create session/i }))
    expect(await screen.findByText(/service is required/i)).toBeInTheDocument()
    expect(screen.getByText(/member is required/i)).toBeInTheDocument()
    expect(screen.getByText(/scheduled time is required/i)).toBeInTheDocument()
    expect(createMock).not.toHaveBeenCalled()
  })

  it("converts datetime-local input to ISO before submit (with locked subjects)", async () => {
    createMock.mockResolvedValue({ id: "sess-1" })
    const onSaved = vi.fn()
    renderWithProviders(
      <ServiceSessionFormSheet
        open
        onOpenChange={() => {}}
        serviceId="svc-1"
        memberId="p-1"
        service={{ id: "svc-1", name: "Counselling" } as never}
        member={
          {
            id: "p-1",
            first_name: "Ada",
            last_name: "Lovelace",
            relation: "Employee",
            display_label: "Test member",
            employer_member_id: "HR-1",
          } as never
        }
        onSaved={onSaved}
      />,
    )

    fireEvent.change(screen.getByLabelText(/scheduled at/i), {
      target: { value: "2026-06-01T10:30" },
    })
    await choosePractitioner()
    await chooseDirectDelivery()
    fireEvent.click(screen.getByRole("button", { name: /create session/i }))

    await waitFor(() => expect(createMock).toHaveBeenCalled())
    const args = createMock.mock.calls[0][0]
    expect(args.service_id).toBe("svc-1")
    expect(args.member_id).toBe("p-1")
    expect(args.scheduled_at).toMatch(/^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}/)
    await waitFor(() => expect(onSaved).toHaveBeenCalled())
  })

  it("maps server fieldErrors to fields", async () => {
    createMock.mockRejectedValue(
      new ApiError("Bad", "VALIDATION", 422, { service_id: "Service not found" }),
    )
    renderWithProviders(
      <ServiceSessionFormSheet
        open
        onOpenChange={() => {}}
        serviceId="svc-1"
        memberId="p-1"
        service={{ id: "svc-1", name: "Counselling" } as never}
        member={
          {
            id: "p-1",
            first_name: "Ada",
            last_name: "Lovelace",
            relation: "Employee",
            display_label: "Test member",
            employer_member_id: "HR-1",
          } as never
        }
      />,
    )

    fireEvent.change(screen.getByLabelText(/scheduled at/i), {
      target: { value: "2026-06-01T10:30" },
    })
    await choosePractitioner()
    await chooseDirectDelivery()
    fireEvent.click(screen.getByRole("button", { name: /create session/i }))

    expect(await screen.findByText(/service not found/i)).toBeInTheDocument()
  })

  it("refuses to submit without an explicit delivery context", async () => {
    renderWithProviders(
      <ServiceSessionFormSheet
        open
        onOpenChange={() => {}}
        serviceId="svc-1"
        memberId="p-1"
        service={{ id: "svc-1", name: "Counselling" } as never}
        member={{ id: "p-1", display_label: "Test member" } as never}
      />,
    )

    fireEvent.change(screen.getByLabelText(/scheduled at/i), {
      target: { value: "2026-06-01T10:30" },
    })
    await choosePractitioner()
    fireEvent.click(screen.getByRole("button", { name: /create session/i }))

    expect(await screen.findByText(/choose direct or organisation delivery/i)).toBeInTheDocument()
    expect(createMock).not.toHaveBeenCalled()
  })

  it("sends direct delivery with no affiliation", async () => {
    createMock.mockResolvedValue({ id: "sess-1" })
    renderWithProviders(
      <ServiceSessionFormSheet
        open
        onOpenChange={() => {}}
        serviceId="svc-1"
        memberId="p-1"
        service={{ id: "svc-1", name: "Counselling" } as never}
        member={{ id: "p-1", display_label: "Test member" } as never}
      />,
    )

    fireEvent.change(screen.getByLabelText(/scheduled at/i), {
      target: { value: "2026-06-01T10:30" },
    })
    await choosePractitioner()
    await chooseDirectDelivery()
    fireEvent.click(screen.getByRole("button", { name: /create session/i }))

    await waitFor(() => expect(createMock).toHaveBeenCalled())
    const args = createMock.mock.calls[0][0]
    expect(args.delivery_context).toBe("Direct")
    expect(args.provider_affiliation_id).toBeNull()
  })

  it("puts a server field error on the delivery-context select", async () => {
    // The API rejects Unknown delivery with a ValidationException naming
    // delivery_context, so the message belongs on that input.
    createMock.mockRejectedValue(
      new ApiError(
        "A booking must state Direct or Organisation delivery.",
        "VALIDATION_ERROR",
        422,
        { delivery_context: "A booking must state Direct or Organisation delivery." },
        undefined,
        [
          {
            field: "delivery_context",
            message: "A booking must state Direct or Organisation delivery.",
            code: null,
          },
        ],
      ),
    )
    renderWithProviders(
      <ServiceSessionFormSheet
        open
        onOpenChange={() => {}}
        serviceId="svc-1"
        memberId="p-1"
        service={{ id: "svc-1", name: "Counselling" } as never}
        member={{ id: "p-1", display_label: "Test member" } as never}
      />,
    )

    fireEvent.change(screen.getByLabelText(/scheduled at/i), {
      target: { value: "2026-06-01T10:30" },
    })
    await choosePractitioner()
    await chooseDirectDelivery()
    fireEvent.click(screen.getByRole("button", { name: /create session/i }))

    const message = await screen.findByText(/must state Direct or Organisation delivery/i)
    const field = screen.getByLabelText(/delivered through/i).closest("div")?.parentElement
    expect(field).toContainElement(message)
  })

  it("lists every eligibility reason the server returns", async () => {
    createMock.mockRejectedValue(
      new ApiError(
        "Provider is not eligible for this booking",
        "PROVIDER_NOT_ELIGIBLE",
        409,
        undefined,
        undefined,
        [
          { field: "provider_id", message: "prv_1", code: "provider_id" },
          { field: "eligibility", message: "Panel status is Suspended", code: "panel_not_active" },
          {
            field: "eligibility",
            message: "Accreditation expired on 2026-01-01",
            code: "accreditation_expired",
          },
        ],
      ),
    )
    renderWithProviders(
      <ServiceSessionFormSheet
        open
        onOpenChange={() => {}}
        serviceId="svc-1"
        memberId="p-1"
        service={{ id: "svc-1", name: "Counselling" } as never}
        member={{ id: "p-1", display_label: "Test member" } as never}
      />,
    )

    fireEvent.change(screen.getByLabelText(/scheduled at/i), {
      target: { value: "2026-06-01T10:30" },
    })
    await choosePractitioner()
    await chooseDirectDelivery()
    fireEvent.click(screen.getByRole("button", { name: /create session/i }))

    expect(await screen.findByText(/panel status is suspended/i)).toBeInTheDocument()
    expect(screen.getByText(/accreditation expired on 2026-01-01/i)).toBeInTheDocument()
  })
})
