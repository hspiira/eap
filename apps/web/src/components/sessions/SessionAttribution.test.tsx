import { screen } from "@testing-library/react"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { SessionDeliveryLabel } from "@/components/sessions/SessionAttribution"
import { renderWithProviders } from "@/test/utils"
import type { ServiceSession } from "@/types/entities"

const mocks = vi.hoisted(() => ({ getOrganisation: vi.fn() }))
vi.mock("@/api/endpoints/provider-organisations", () => ({
  providerOrganisationsApi: { getById: mocks.getOrganisation },
}))
vi.mock("@tanstack/react-router", () => ({
  Link: ({ children, to: _to, params: _params, ...rest }: Record<string, unknown>) => (
    <a href={_to as string} {...rest}>
      {children as React.ReactNode}
    </a>
  ),
}))

function makeSession(overrides: Partial<ServiceSession> = {}): ServiceSession {
  return {
    id: "sess-1",
    tenant_id: "tenant-1",
    service_id: "svc-1",
    member_id: "mem-1",
    provider_id: "prv-1",
    status: "Completed",
    scheduled_at: "2026-01-01T09:00:00Z",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  } as ServiceSession
}

beforeEach(() => {
  vi.clearAllMocks()
  mocks.getOrganisation.mockResolvedValue({ id: "org-1", name: "Serenity Counselling Ltd" })
})

describe("session delivery attribution", () => {
  it("shows an unknown historical context as unknown, never as direct", () => {
    renderWithProviders(
      <SessionDeliveryLabel session={makeSession({ delivery_context: "Unknown" } as never)} />,
    )
    expect(screen.getByText(/does not say how this session was delivered/i)).toBeInTheDocument()
    expect(screen.queryByText("Direct")).not.toBeInTheDocument()
  })

  it("shows a missing context as not recorded, never as direct", () => {
    renderWithProviders(<SessionDeliveryLabel session={makeSession()} />)
    expect(screen.getByText("Not recorded")).toBeInTheDocument()
    expect(screen.queryByText("Direct")).not.toBeInTheDocument()
  })

  it("shows direct delivery as direct", () => {
    renderWithProviders(
      <SessionDeliveryLabel session={makeSession({ delivery_context: "Direct" } as never)} />,
    )
    expect(screen.getByText("Direct")).toBeInTheDocument()
  })

  it("names the organisation the session itself recorded", async () => {
    renderWithProviders(
      <SessionDeliveryLabel
        session={makeSession({
          delivery_context: "Organisation",
          provider_affiliation_id: "aff-1",
          provider_organisation_id: "org-1",
        } as never)}
      />,
    )
    expect(await screen.findByText("Serenity Counselling Ltd")).toBeInTheDocument()
    // Resolved from the session's own organisation id, not from the practitioner.
    expect(mocks.getOrganisation).toHaveBeenCalledWith("org-1")
  })

  it("flags organisation delivery with no organisation recorded rather than guessing", () => {
    renderWithProviders(
      <SessionDeliveryLabel session={makeSession({ delivery_context: "Organisation" } as never)} />,
    )
    expect(screen.getByText(/no organisation recorded/i)).toBeInTheDocument()
    expect(mocks.getOrganisation).not.toHaveBeenCalled()
  })
})
