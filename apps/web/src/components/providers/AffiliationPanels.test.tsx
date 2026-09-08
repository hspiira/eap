import { fireEvent, screen, waitFor } from "@testing-library/react"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { OrganisationAffiliationsPanel } from "@/components/providers/OrganisationAffiliationsPanel"
import { ProviderCommitmentsPanel } from "@/components/providers/ProviderCommitmentsPanel"
import { renderWithProviders } from "@/test/utils"
import { ApiError } from "@/types/api"
import type { ProviderAffiliation } from "@/types/entities"

const mocks = vi.hoisted(() => ({
  list: vi.fn(),
  create: vi.fn(),
  setValidUntil: vi.fn(),
  getDeliveryStats: vi.fn(),
  listClauses: vi.fn(),
}))
vi.mock("@/api/endpoints/provider-affiliations", () => ({ providerAffiliationsApi: mocks }))
vi.mock("@/api/endpoints/providers", () => ({
  providersApi: { getDeliveryStats: mocks.getDeliveryStats },
}))
vi.mock("@/api/endpoints/non-compete-clauses", () => ({
  nonCompeteClausesApi: { listForProvider: mocks.listClauses },
}))
vi.mock("@/hooks/useCanWrite", () => ({
  useCanWrite: () => true,
  useCurrentRole: () => "Admin",
}))
vi.mock("@tanstack/react-router", () => ({
  Link: ({ children, to: _to, params: _params, ...rest }: Record<string, unknown>) => (
    <a href={_to as string} {...rest}>
      {children as React.ReactNode}
    </a>
  ),
}))
vi.mock("@/components/providers/ProviderNameLink", () => ({
  ProviderNameLink: ({ providerId }: { providerId: string }) => <span>{providerId}</span>,
}))
vi.mock("@/components/common/EntityPicker", () => ({
  ProviderPicker: ({ onChange }: { onChange: (id: string) => void }) => (
    <button type="button" onClick={() => onChange("prv-1")}>
      Pick practitioner
    </button>
  ),
}))

function makeAffiliation(overrides: Partial<ProviderAffiliation> = {}): ProviderAffiliation {
  return {
    id: "aff-1",
    tenant_id: "tenant-1",
    provider_id: "prv-1",
    organisation_id: "org-1",
    valid_from: "2026-01-01",
    valid_until: null,
    organisation_name: "Serenity Counselling Ltd",
    organisation_is_active: true,
    organisation_approval_status: "Approved",
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  } as ProviderAffiliation
}

function page(items: ProviderAffiliation[]) {
  return { items, total: items.length, page: 1, limit: 100, has_more: false }
}

beforeEach(() => {
  vi.clearAllMocks()
  mocks.list.mockResolvedValue(page([makeAffiliation()]))
  mocks.setValidUntil.mockResolvedValue(makeAffiliation())
  mocks.create.mockResolvedValue(makeAffiliation())
  mocks.listClauses.mockResolvedValue([])
  mocks.getDeliveryStats.mockResolvedValue({
    total_sessions: 0,
    first_session_at: null,
    last_session_at: null,
    by_delivery_context: {},
    by_organisation: [],
  })
})

describe("practitioner affiliations", () => {
  it("shows the covered period and still discloses the exclusive end", async () => {
    mocks.list.mockResolvedValue(page([makeAffiliation({ valid_until: "2026-07-01" })]))
    renderWithProviders(<ProviderCommitmentsPanel providerId="prv-1" />)
    // The reader gets the days actually covered; the stored boundary stays
    // visible because attribution depends on it.
    expect(await screen.findByText(/ends before 2026-07-01/)).toBeInTheDocument()
    expect(screen.queryByText(/until 2026-07-01 exclusive/)).not.toBeInTheDocument()
  })

  it("labels an open-ended affiliation as running onwards", async () => {
    mocks.list.mockResolvedValue(page([makeAffiliation({ valid_until: null })]))
    renderWithProviders(<ProviderCommitmentsPanel providerId="prv-1" />)
    expect(await screen.findByText(/onwards/)).toBeInTheDocument()
  })

  it("separates ended affiliations from current ones", async () => {
    mocks.list.mockResolvedValue(
      page([
        makeAffiliation({ id: "aff-past", valid_until: "2024-01-01" }),
        makeAffiliation({ id: "aff-now", valid_until: null }),
      ]),
    )
    renderWithProviders(<ProviderCommitmentsPanel providerId="prv-1" />)
    expect(await screen.findByText("Current")).toBeInTheDocument()
    expect(screen.getByText("Ended")).toBeInTheDocument()
  })

  it("shows what was delivered through an affiliation", async () => {
    mocks.getDeliveryStats.mockResolvedValue({
      total_sessions: 12,
      first_session_at: null,
      last_session_at: null,
      by_delivery_context: {},
      by_organisation: [
        { organisation_id: "org-1", organisation_name: "Serenity Counselling Ltd", session_count: 12 },
      ],
    })
    renderWithProviders(<ProviderCommitmentsPanel providerId="prv-1" />)
    expect(await screen.findByText(/12 sessions attributed to this firm/)).toBeInTheDocument()
  })

  it("keeps non-compete clauses beside affiliations without implying they restrict a booking", async () => {
    renderWithProviders(<ProviderCommitmentsPanel providerId="prv-1" />)
    expect(await screen.findByText("Non-compete clauses")).toBeInTheDocument()
    expect(screen.getByText(/does not currently restrict a booking/)).toBeInTheDocument()
  })

  it("lists concurrent affiliations with different firms without complaint", async () => {
    mocks.list.mockResolvedValue(
      page([
        makeAffiliation({ id: "aff-1", organisation_name: "Serenity Counselling Ltd" }),
        makeAffiliation({
          id: "aff-2",
          organisation_id: "org-2",
          organisation_name: "Kampala Wellness Group",
        }),
      ]),
    )
    renderWithProviders(<ProviderCommitmentsPanel providerId="prv-1" />)
    expect(await screen.findByText("Serenity Counselling Ltd")).toBeInTheDocument()
    expect(screen.getByText("Kampala Wellness Group")).toBeInTheDocument()
  })

  it("warns that an unapproved firm cannot take organisation delivery", async () => {
    mocks.list.mockResolvedValue(
      page([makeAffiliation({ organisation_approval_status: "Suspended" } as never)]),
    )
    renderWithProviders(<ProviderCommitmentsPanel providerId="prv-1" />)
    expect(await screen.findByText(/Supplier approval is Suspended/)).toBeInTheDocument()
  })

  it("includes ended affiliations, because past sessions still refer to them", async () => {
    renderWithProviders(<ProviderCommitmentsPanel providerId="prv-1" />)
    await waitFor(() => expect(mocks.list).toHaveBeenCalled())
    expect(mocks.list).toHaveBeenCalledWith(
      expect.objectContaining({ provider_id: "prv-1", include_ended: true }),
    )
  })

  it("edits only the end of an interval, and records why", async () => {
    renderWithProviders(<ProviderCommitmentsPanel providerId="prv-1" />)
    fireEvent.click(await screen.findByRole("button", { name: /set end/i }))
    fireEvent.change(screen.getByLabelText(/ends before/i), { target: { value: "2026-09-01" } })

    // Moving an end date can affect existing attribution, so it is a
    // correction and the server requires a reason.
    const save = screen.getByRole("button", { name: /^save$/i })
    expect(save).toBeDisabled()

    fireEvent.change(screen.getByLabelText(/reason/i), { target: { value: "Contract ended" } })
    fireEvent.click(save)

    await waitFor(() =>
      expect(mocks.setValidUntil).toHaveBeenCalledWith("aff-1", "2026-09-01", "Contract ended"),
    )
  })
})

describe("organisation affiliations", () => {
  it("shows the server's overlap rejection with the conflicting period", async () => {
    // Wire shape of the corrected overlap error: one entry keyed by the real
    // field, carrying the same sentence as the top-level message.
    mocks.create.mockRejectedValue(
      new ApiError(
        "Overlaps affiliation aff-9 (2026-01-01 to 2026-06-01)",
        "AFFILIATION_OVERLAP",
        409,
        { valid_from: "Overlaps affiliation aff-9 (2026-01-01 to 2026-06-01)" },
        undefined,
        [
          {
            field: "valid_from",
            message: "Overlaps affiliation aff-9 (2026-01-01 to 2026-06-01)",
            code: null,
          },
        ],
      ),
    )
    renderWithProviders(<OrganisationAffiliationsPanel organisationId="org-1" />)

    fireEvent.click(await screen.findByRole("button", { name: /add affiliation/i }))
    fireEvent.click(screen.getByRole("button", { name: /pick practitioner/i }))
    fireEvent.change(screen.getByLabelText(/starts on/i), { target: { value: "2026-03-01" } })
    fireEvent.click(screen.getAllByRole("button", { name: /^add affiliation$/i }).at(-1)!)

    // The server names the conflicting end, so the message lands on that input
    // rather than in a banner detached from the field it is about.
    const message = await screen.findByText(
      /Overlaps affiliation aff-9 \(2026-01-01 to 2026-06-01\)/,
    )
    expect(message).toBeInTheDocument()
    const startsOn = screen.getByLabelText(/starts on/i).closest("div")?.parentElement
    expect(startsOn).toContainElement(message)
  })

  it("falls back to a banner when the rejection names no usable field", async () => {
    mocks.create.mockRejectedValue(
      new ApiError("Overlaps an existing affiliation", "AFFILIATION_OVERLAP", 409),
    )
    renderWithProviders(<OrganisationAffiliationsPanel organisationId="org-1" />)

    fireEvent.click(await screen.findByRole("button", { name: /add affiliation/i }))
    fireEvent.click(screen.getByRole("button", { name: /pick practitioner/i }))
    fireEvent.change(screen.getByLabelText(/starts on/i), { target: { value: "2026-03-01" } })
    fireEvent.click(screen.getAllByRole("button", { name: /^add affiliation$/i }).at(-1)!)

    expect(await screen.findByRole("alert")).toHaveTextContent("Overlaps an existing affiliation")
  })

  it("sends an open-ended affiliation as a null end", async () => {
    renderWithProviders(<OrganisationAffiliationsPanel organisationId="org-1" />)

    fireEvent.click(await screen.findByRole("button", { name: /add affiliation/i }))
    fireEvent.click(screen.getByRole("button", { name: /pick practitioner/i }))
    fireEvent.change(screen.getByLabelText(/starts on/i), { target: { value: "2026-03-01" } })
    fireEvent.click(screen.getAllByRole("button", { name: /^add affiliation$/i }).at(-1)!)

    await waitFor(() => expect(mocks.create).toHaveBeenCalled())
    expect(mocks.create).toHaveBeenCalledWith("org-1", {
      provider_id: "prv-1",
      valid_from: "2026-03-01",
      valid_until: null,
    })
  })
})
