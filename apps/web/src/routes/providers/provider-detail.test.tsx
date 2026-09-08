import { screen, waitFor, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { renderWithProviders } from "@/test/utils"
import type { Provider } from "@/types/entities"
import {
  AccreditationStatus,
  BaseStatus,
  PanelStatus,
  ProviderIdentityProvenance,
} from "@/types/enums"

const mocks = vi.hoisted(() => ({
  getById: vi.fn(),
  getEligibility: vi.fn(),
  listEngagementDocuments: vi.fn(),
  upsertEngagementDocument: vi.fn(),
  getDeliveryStats: vi.fn(),
  listLinks: vi.fn(),
  getEntityHistory: vi.fn(),
  listSessions: vi.fn(),
  role: "Admin",
  search: {} as Record<string, unknown>,
  listeners: new Set<() => void>(),
}))
vi.mock("@/api/endpoints/providers", () => ({ providersApi: mocks }))
vi.mock("@/api/endpoints/provider-specialties", () => ({
  providerSpecialtiesApi: { listLinks: mocks.listLinks, list: vi.fn().mockResolvedValue([]) },
}))
vi.mock("@/api/endpoints/audit", () => ({
  auditApi: { getEntityHistory: mocks.getEntityHistory },
}))
vi.mock("@/hooks/useCanWrite", () => ({
  useCanWrite: () => true,
  useCurrentRole: () => mocks.role,
  useHasClinicalScope: () => ({ hasScope: true, isLoading: false }),
}))
vi.mock("@/components/providers/ProviderFormSheet", () => ({ ProviderFormSheet: () => null }))
vi.mock("@/components/providers/ProviderAffiliationsPanel", () => ({
  ProviderAffiliationsPanel: () => null,
}))
vi.mock("@/components/providers/ProviderNonCompetePanel", () => ({
  ProviderNonCompetePanel: () => null,
}))
vi.mock("@/components/providers/ProviderAccountCard", () => ({ ProviderAccountCard: () => null }))
vi.mock("@/components/providers/ProviderSpecialtiesPanel", () => ({
  ProviderSpecialtiesPanel: () => null,
}))
vi.mock("@/components/common/SessionHistory", () => ({ SessionHistory: () => null }))
// The active tab lives in the URL, so the router stand-in has to store what
// navigate writes and re-render the readers, or every tab click is a no-op.
vi.mock("@tanstack/react-router", async () => {
  const { useEffect, useReducer } = await import("react")
  return {
    createFileRoute: () => (options: unknown) => ({
      options,
      useParams: () => ({ providerId: "prov-1" }),
    }),
    Link: ({ children, to: _to, ...rest }: { children: React.ReactNode; to?: string }) => (
      <a href={_to} {...rest}>
        {children}
      </a>
    ),
    useNavigate:
      () => (opts: { search: (prev: Record<string, unknown>) => Record<string, unknown> }) => {
        mocks.search = opts.search(mocks.search)
        for (const listener of mocks.listeners) listener()
      },
    useSearch: () => {
      const [, rerender] = useReducer((n: number) => n + 1, 0)
      useEffect(() => {
        mocks.listeners.add(rerender)
        return () => void mocks.listeners.delete(rerender)
      }, [])
      return mocks.search
    },
  }
})

const { Route } = await import("@/routes/providers/$providerId")
const Page = (Route as unknown as { options: { component: React.ComponentType } }).options.component

function makeProvider(overrides: Partial<Provider> = {}): Provider {
  return {
    id: "prov-1",
    tenant_id: "tenant-1",
    display_name: "Sheila Kukunda",
    email: null,
    phone: null,
    user_id: null,
    status: BaseStatus.PENDING,
    identity_provenance: ProviderIdentityProvenance.OWNED,
    provider_profile: {
      tier: null,
      region: null,
      accreditation_status: AccreditationStatus.PENDING,
      panel_status: PanelStatus.PENDING,
      accreditation_authority: null,
      accreditation_expiry: null,
      specialties: [],
      bio: null,
      gender: null,
    },
    license_info: null,
    created_at: "2026-09-07T00:00:00Z",
    updated_at: "2026-09-07T00:00:00Z",
    ...overrides,
  } as Provider
}

beforeEach(() => {
  vi.clearAllMocks()
  mocks.role = "Admin"
  mocks.search = {}
  mocks.getById.mockResolvedValue(makeProvider())
  mocks.getEligibility.mockResolvedValue({
    provider_id: "prov-1",
    client_id: null,
    scheduled_at: "2026-09-08T00:00:00Z",
    panel_eligible: false,
    binding_non_compete_count: 0,
    binding_non_compete_ids: [],
    eligible: false,
    reasons: ["Practitioner is not active", "Panel status is not active"],
    failures: [
      { code: "provider_not_active", message: "Practitioner is not active" },
      { code: "panel_not_active", message: "Panel status is not active" },
      { code: "not_accredited", message: "Practitioner is not accredited" },
    ],
  })
  mocks.listEngagementDocuments.mockResolvedValue([])
  mocks.listLinks.mockResolvedValue([])
  mocks.getDeliveryStats.mockResolvedValue({
    total_sessions: 0,
    first_session_at: null,
    last_session_at: null,
    by_delivery_context: {},
    by_organisation: [],
  })
  mocks.getEntityHistory.mockResolvedValue([])
})

describe("practitioner dossier", () => {
  it("reports the booking gate's verdict and what is blocking it", async () => {
    renderWithProviders(<Page />)

    expect(await screen.findByTestId("readiness-verdict")).toHaveTextContent("Not bookable")
    // Each failing check names the command that clears it, not the raw code.
    expect(await screen.findByText("Set the record status to Active.")).toBeInTheDocument()
    expect(screen.getByText("Set the panel status to Active.")).toBeInTheDocument()
    expect(screen.getByText("Record accreditation.")).toBeInTheDocument()
  })

  it("says bookable when the gate passes", async () => {
    mocks.getEligibility.mockResolvedValue({
      provider_id: "prov-1",
      client_id: null,
      scheduled_at: "2026-09-08T00:00:00Z",
      panel_eligible: true,
      binding_non_compete_count: 0,
      binding_non_compete_ids: [],
      eligible: true,
      reasons: [],
      failures: [],
    })
    mocks.getById.mockResolvedValue(
      makeProvider({
        status: BaseStatus.ACTIVE,
        provider_profile: {
          ...makeProvider().provider_profile,
          panel_status: PanelStatus.ACTIVE,
          accreditation_status: AccreditationStatus.ACCREDITED,
        },
      }),
    )
    renderWithProviders(<Page />)
    expect(await screen.findByTestId("readiness-verdict")).toHaveTextContent("Bookable")
  })

  it("keeps profile completeness separate from the booking gate", async () => {
    renderWithProviders(<Page />)
    // Tier and region are not part of the gate, so they must not read as blockers.
    expect(await screen.findByText("Profile completeness")).toBeInTheDocument()
    expect(screen.getByText(/do not block a booking/)).toBeInTheDocument()
    expect(screen.getByText("Tier assessed")).toBeInTheDocument()
    expect(screen.getByText("Region recorded")).toBeInTheDocument()
  })

  it("shows the engagement checklist and distinguishes unrecorded from missing", async () => {
    mocks.listEngagementDocuments.mockResolvedValue([
      {
        id: "d1",
        provider_id: "prov-1",
        document_kind: "Contract",
        state: "Present",
        note: null,
        created_at: "2026-09-07T00:00:00Z",
        updated_at: "2026-09-07T00:00:00Z",
      },
      {
        id: "d2",
        provider_id: "prov-1",
        document_kind: "KYC",
        state: "Missing",
        note: "chased 3 Sep",
        created_at: "2026-09-07T00:00:00Z",
        updated_at: "2026-09-07T00:00:00Z",
      },
    ])
    renderWithProviders(<Page />)

    expect(await screen.findByText("1 of 7 held.")).toBeInTheDocument()
    expect(screen.getByText("chased 3 Sep")).toBeInTheDocument()
    // A kind nobody has answered is not the same as one recorded Missing.
    expect(screen.getAllByText("Not recorded").length).toBe(5)
  })

  it("records a checklist entry through the admin-only control", async () => {
    const user = userEvent.setup()
    mocks.upsertEngagementDocument.mockResolvedValue({})
    renderWithProviders(<Page />)

    await user.click((await screen.findAllByRole("button", { name: "Record" }))[0])
    await user.click(screen.getByRole("button", { name: "Save" }))

    await waitFor(() =>
      expect(mocks.upsertEngagementDocument).toHaveBeenCalledWith("prov-1", "Contract", {
        state: "Present",
        note: null,
      }),
    )
  })

  it("hides the checklist controls from a non-admin", async () => {
    mocks.role = "Manager"
    renderWithProviders(<Page />)
    await screen.findByText("0 of 7 held.")
    expect(screen.queryByRole("button", { name: "Record" })).not.toBeInTheDocument()
  })

  it("reports delivery totals from the server, not the fetched page", async () => {
    const user = userEvent.setup()
    mocks.getDeliveryStats.mockResolvedValue({
      total_sessions: 86,
      first_session_at: "2024-08-18T00:00:00Z",
      last_session_at: "2026-08-28T00:00:00Z",
      by_delivery_context: { Unknown: 85, Direct: 1 },
      by_organisation: [
        { organisation_id: "org-1", organisation_name: "African Retreat Centre", session_count: 12 },
      ],
    })
    renderWithProviders(<Page />)

    await user.click(await screen.findByRole("tab", { name: "Delivery record" }))

    expect(await screen.findByText("86")).toBeInTheDocument()
    expect(screen.getByText("African Retreat Centre")).toBeInTheDocument()
    expect(screen.getByText("Unknown")).toBeInTheDocument()
  })

  it("renders the audit trail on the activity tab", async () => {
    const user = userEvent.setup()
    mocks.getEntityHistory.mockResolvedValue([
      {
        id: "a1",
        action_type: "UPDATE",
        resource_type: "Provider",
        resource_id: "prov-1",
        changes: { panel_status: "Active" },
        created_at: "2026-09-07T10:00:00Z",
      },
    ])
    renderWithProviders(<Page />)

    await user.click(await screen.findByRole("tab", { name: "Activity" }))

    await waitFor(() => expect(mocks.getEntityHistory).toHaveBeenCalledWith("Provider", "prov-1"))
    expect(await screen.findByText("panel_status")).toBeInTheDocument()
  })

  it("names where the record came from", async () => {
    mocks.getById.mockResolvedValue(
      makeProvider({ identity_provenance: ProviderIdentityProvenance.BACKFILLED_FROM_USER }),
    )
    renderWithProviders(<Page />)
    const rail = await screen.findByText("Record origin")
    expect(within(rail.closest("section") as HTMLElement).getByText(/Backfilled from a user/))
      .toBeInTheDocument()
  })
})
