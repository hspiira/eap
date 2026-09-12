import { screen, waitFor } from "@testing-library/react"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { renderWithProviders } from "@/test/utils"

const api = vi.hoisted(() => ({ availability: vi.fn() }))
vi.mock("@/api/endpoints/service-sessions", () => ({ serviceSessionsApi: api }))

const { PractitionerAvailabilityNotice } =
  await import("@/components/sessions/PractitionerAvailabilityNotice")

const READY = {
  providerId: "prov-1",
  serviceId: "svc-1",
  scheduledAt: "2026-05-04T10:00",
}

function respond(available: boolean, clashAt: string | null = null) {
  api.availability.mockResolvedValue({
    starts_at: "2026-05-04T10:00:00Z",
    ends_at: "2026-05-04T11:00:00Z",
    assumed_minutes: 60,
    items: [
      {
        provider_id: "prov-1",
        available,
        clashing_session_id: available ? null : "ses-9",
        clashing_scheduled_at: clashAt,
      },
    ],
  })
}

beforeEach(() => vi.clearAllMocks())

describe("PractitionerAvailabilityNotice", () => {
  it("warns when the practitioner already has a booking over the slot", async () => {
    respond(false, "2026-05-04T10:30:00Z")
    renderWithProviders(<PractitionerAvailabilityNotice {...READY} />)

    const alert = await screen.findByRole("alert")
    expect(alert).toHaveTextContent("This practitioner is already booked at this time.")
    expect(alert).toHaveTextContent("Pick a different practitioner or time.")
  })

  it("says what it checked, not that the practitioner is free", async () => {
    // The platform cannot see an external practitioner's own diary, so the
    // clear case must not overclaim.
    respond(true)
    renderWithProviders(<PractitionerAvailabilityNotice {...READY} />)

    await waitFor(() => expect(api.availability).toHaveBeenCalled())
    expect(await screen.findByText(/No other booking for this practitioner/)).toBeInTheDocument()
    expect(screen.getByText(/Their own diary is not visible here/)).toBeInTheDocument()
    expect(screen.queryByRole("alert")).not.toBeInTheDocument()
  })

  it("asks nothing until a practitioner, service and time are all chosen", async () => {
    renderWithProviders(<PractitionerAvailabilityNotice {...READY} providerId="" />)
    renderWithProviders(<PractitionerAvailabilityNotice {...READY} serviceId="" />)
    renderWithProviders(<PractitionerAvailabilityNotice {...READY} scheduledAt="" />)

    await waitFor(() => expect(api.availability).not.toHaveBeenCalled())
  })

  it("does not ask on a date it cannot read", async () => {
    renderWithProviders(<PractitionerAvailabilityNotice {...READY} scheduledAt="not-a-date" />)

    await waitFor(() => expect(api.availability).not.toHaveBeenCalled())
  })
})
