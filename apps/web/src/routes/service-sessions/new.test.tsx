import { fireEvent, screen, waitFor } from "@testing-library/react"
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest"

import { ServiceSessionFormSheet } from "@/components/ServiceSessionFormSheet"
import { renderWithProviders } from "@/test/utils"
import { ApiError } from "@/types/api"

const createMock = vi.fn()
const listServicesMock = vi.fn().mockResolvedValue({ items: [], total: 0 })
const listMembersMock = vi.fn().mockResolvedValue({ items: [], total: 0 })
const listProvidersMock = vi.fn()

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

beforeEach(() => {
  createMock.mockReset()
  listServicesMock.mockClear()
  listMembersMock.mockClear()
  listProvidersMock.mockClear()
  listProvidersMock.mockResolvedValue({
    items: [
      {
        id: "prov-1",
        person_type: "Provider",
        display_name: "Dr Alice Nakato",
        email: "alice.nakato@example.com",
        provider_profile: { tier: "Senior", region: "Kampala" },
      },
    ],
    total: 1,
    page: 1,
    limit: 8,
    has_more: false,
  })
})
afterEach(() => {
  createMock.mockReset()
})

/** Provider is required, so every create-path test has to choose one. */
async function chooseProvider() {
  const search = screen.getByPlaceholderText(/search providers/i)
  fireEvent.change(search, { target: { value: "Nakato" } })
  await new Promise((r) => setTimeout(r, 400))

  const option = await screen.findByText("Dr Alice Nakato")
  fireEvent.click(option)
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
    await chooseProvider()
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
    await chooseProvider()
    fireEvent.click(screen.getByRole("button", { name: /create session/i }))

    expect(await screen.findByText(/service not found/i)).toBeInTheDocument()
  })
})
