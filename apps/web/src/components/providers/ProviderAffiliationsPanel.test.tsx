import { fireEvent, screen, waitFor } from "@testing-library/react"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { OrganisationAffiliationsPanel } from "@/components/providers/OrganisationAffiliationsPanel"
import { ProviderAffiliationsPanel } from "@/components/providers/ProviderAffiliationsPanel"
import { renderWithProviders } from "@/test/utils"
import { ApiError } from "@/types/api"
import type { ProviderAffiliation } from "@/types/entities"

const mocks = vi.hoisted(() => ({
  list: vi.fn(),
  create: vi.fn(),
  setValidUntil: vi.fn(),
}))
vi.mock("@/api/endpoints/provider-affiliations", () => ({ providerAffiliationsApi: mocks }))
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
    valid_until: "2026-07-01",
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
})

describe("practitioner affiliations", () => {
  it("labels the interval as end-exclusive rather than as an end date", async () => {
    renderWithProviders(<ProviderAffiliationsPanel providerId="prv-1" />)
    expect(await screen.findByText(/2026-01-01 until 2026-07-01 exclusive/)).toBeInTheDocument()
  })

  it("labels an open-ended affiliation as open ended", async () => {
    mocks.list.mockResolvedValue(page([makeAffiliation({ valid_until: null })]))
    renderWithProviders(<ProviderAffiliationsPanel providerId="prv-1" />)
    expect(await screen.findByText(/From 2026-01-01, open ended/)).toBeInTheDocument()
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
    renderWithProviders(<ProviderAffiliationsPanel providerId="prv-1" />)
    expect(await screen.findByText("Serenity Counselling Ltd")).toBeInTheDocument()
    expect(screen.getByText("Kampala Wellness Group")).toBeInTheDocument()
  })

  it("warns that an unapproved firm cannot take organisation delivery", async () => {
    mocks.list.mockResolvedValue(
      page([makeAffiliation({ organisation_approval_status: "Suspended" } as never)]),
    )
    renderWithProviders(<ProviderAffiliationsPanel providerId="prv-1" />)
    expect(await screen.findByText(/Supplier approval is Suspended/)).toBeInTheDocument()
  })

  it("includes ended affiliations, because past sessions still refer to them", async () => {
    renderWithProviders(<ProviderAffiliationsPanel providerId="prv-1" />)
    await waitFor(() => expect(mocks.list).toHaveBeenCalled())
    expect(mocks.list).toHaveBeenCalledWith(
      expect.objectContaining({ provider_id: "prv-1", include_ended: true }),
    )
  })

  it("edits only the end of an interval, and records why", async () => {
    renderWithProviders(<ProviderAffiliationsPanel providerId="prv-1" />)
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
    // Shape captured from the running API: the sentence is the top-level
    // message, and `details` carries the field name as a value.
    mocks.create.mockRejectedValue(
      new ApiError(
        "Overlaps affiliation aff-9 (2026-01-01 to 2026-06-01)",
        "AFFILIATION_OVERLAP",
        409,
        undefined,
        undefined,
        [
          { field: "field", message: "valid_from", code: null },
          { field: "conflicting_affiliation_id", message: "aff-9", code: null },
        ],
      ),
    )
    renderWithProviders(<OrganisationAffiliationsPanel organisationId="org-1" />)

    fireEvent.click(await screen.findByRole("button", { name: /add affiliation/i }))
    fireEvent.click(screen.getByRole("button", { name: /pick practitioner/i }))
    fireEvent.change(screen.getByLabelText(/starts on/i), { target: { value: "2026-03-01" } })
    fireEvent.click(screen.getAllByRole("button", { name: /^add affiliation$/i }).at(-1)!)

    expect(
      await screen.findByText(/Overlaps affiliation aff-9 \(2026-01-01 to 2026-06-01\)/),
    ).toBeInTheDocument()
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
