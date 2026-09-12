import { screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { renderWithProviders } from "@/test/utils"
import type { ServiceSession } from "@/types/entities"
import { SessionAttendance, SessionStatus } from "@/types/enums"

const mocks = vi.hoisted(() => ({
  getById: vi.fn(),
  getTree: vi.fn(),
  getServiceById: vi.fn(),
  getMemberById: vi.fn(),
  getProviderById: vi.fn(),
  getEntityHistory: vi.fn(),
  getEntityFieldChanges: vi.fn(),
  listCases: vi.fn(),
  hasClinicalScope: true,
  search: {} as Record<string, unknown>,
  listeners: new Set<() => void>(),
}))
vi.mock("@/api/endpoints/service-sessions", () => ({ serviceSessionsApi: mocks }))
vi.mock("@/api/endpoints/diagnoses", () => ({ diagnosesApi: { getTree: mocks.getTree } }))
vi.mock("@/api/endpoints/services", () => ({ servicesApi: { getById: mocks.getServiceById } }))
vi.mock("@/api/endpoints/members", () => ({ membersApi: { getById: mocks.getMemberById } }))
vi.mock("@/api/endpoints/providers", () => ({ providersApi: { getById: mocks.getProviderById } }))
vi.mock("@/api/endpoints/cases", () => ({ casesApi: { list: mocks.listCases } }))
vi.mock("@/api/endpoints/audit", () => ({
  auditApi: {
    getEntityHistory: mocks.getEntityHistory,
    getEntityFieldChanges: mocks.getEntityFieldChanges,
  },
}))
vi.mock("@/hooks/useCanWrite", () => ({
  useCanWrite: () => true,
  useCurrentRole: () => "Admin",
  useHasClinicalScope: () => ({ hasScope: mocks.hasClinicalScope, isLoading: false }),
}))
vi.mock("@/components/ServiceSessionFormSheet", () => ({ ServiceSessionFormSheet: () => null }))
vi.mock("@tanstack/react-router", async () => {
  const { useEffect, useReducer } = await import("react")
  return {
    // useBackTo steps back through history; these tests render pages cold, so
    // canGoBack is false and the back control falls through to its list route.
    useRouter: () => ({ history: { back: () => {} } }),
    useCanGoBack: () => false,
    createFileRoute: () => (options: unknown) => ({
      options,
      useParams: () => ({ sessionId: "sess-1" }),
    }),
    Link: ({ children, to: _to, ...rest }: { children: React.ReactNode; to?: string }) => (
      <a href={_to} {...rest}>
        {children}
      </a>
    ),
    useNavigate:
      () => (opts: { search: (prev: Record<string, unknown>) => Record<string, unknown> }) => {
        if (typeof opts?.search === "function") {
          mocks.search = opts.search(mocks.search)
          for (const listener of mocks.listeners) listener()
        }
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

const { Route } = await import("@/routes/service-sessions/$sessionId")
const Page = (Route as unknown as { options: { component: React.ComponentType } }).options.component

function makeSession(overrides: Partial<ServiceSession> = {}): ServiceSession {
  return {
    id: "sess-1",
    tenant_id: "tenant-1",
    service_id: "svc-1",
    client_id: "client-1",
    provider_id: "prov-1",
    attendance: SessionAttendance.COMPANY_WIDE,
    member_id: null,
    status: SessionStatus.COMPLETED,
    scheduled_at: "2026-08-27T09:00:00Z",
    reschedule_count: 0,
    created_at: "2026-08-27T09:00:00Z",
    updated_at: "2026-08-27T09:00:00Z",
    client_name: "Stanbic Bank",
    service_name: "Health Talk",
    provider_display_name: "Daniel Kanamara",
    ...overrides,
  } as ServiceSession
}

beforeEach(() => {
  vi.clearAllMocks()
  mocks.hasClinicalScope = true
  mocks.search = {}
  mocks.getById.mockResolvedValue(makeSession())
  mocks.getTree.mockResolvedValue({ types: [] })
  mocks.getServiceById.mockResolvedValue(null)
  mocks.getMemberById.mockResolvedValue(null)
  mocks.getProviderById.mockResolvedValue(null)
  mocks.getEntityHistory.mockResolvedValue([])
  mocks.getEntityFieldChanges.mockResolvedValue([])
  mocks.listCases.mockResolvedValue({ items: [], total: 0, page: 1, limit: 20, has_more: false })
})

describe("session detail", () => {
  it("identifies a company-wide session by what was delivered and to whom", async () => {
    renderWithProviders(<Page />)
    expect(
      await screen.findByRole("heading", { name: "Health Talk at Stanbic Bank" }),
    ).toBeInTheDocument()
  })

  it("never hunts for a member a company-wide session does not have", async () => {
    renderWithProviders(<Page />)
    await screen.findByRole("heading", { name: "Health Talk at Stanbic Bank" })
    // The old page sat on "Loading member…" forever for these.
    expect(screen.queryByText(/Loading member/)).not.toBeInTheDocument()
    expect(screen.queryByText("Subject")).not.toBeInTheDocument()
    expect(screen.getByText("Engagement")).toBeInTheDocument()
    expect(mocks.getMemberById).not.toHaveBeenCalled()
  })

  it("shows what a company-wide session actually records", async () => {
    mocks.getById.mockResolvedValue(
      makeSession({ headcount: 40, client_type: "Repeat", rate_ugx: 250000 } as never),
    )
    renderWithProviders(<Page />)
    expect(await screen.findByText("40")).toBeInTheDocument()
    expect(screen.getByText("UGX 250,000")).toBeInTheDocument()
  })

  it("gives an individual session a subject instead of an engagement", async () => {
    mocks.getById.mockResolvedValue(
      makeSession({
        attendance: SessionAttendance.INDIVIDUAL,
        member_id: "mem-1",
        member_display_label: "Amina Namukasa",
        session_number: 3,
      }),
    )
    renderWithProviders(<Page />)
    expect(await screen.findByText("Subject")).toBeInTheDocument()
    expect(screen.getByText("Amina Namukasa")).toBeInTheDocument()
    expect(screen.queryByText("Engagement")).not.toBeInTheDocument()
    // The session number is a rail stat, not repeated in the subject card.
    expect(screen.getByText("#3")).toBeInTheDocument()
  })

  it("reports the session's own duration, not the service's nominal one", async () => {
    mocks.getById.mockResolvedValue(makeSession({ duration: 95 }))
    mocks.getServiceById.mockResolvedValue({
      id: "svc-1",
      name: "Health Talk",
      duration_minutes: 60,
    })
    renderWithProviders(<Page />)
    expect(await screen.findByText("95m")).toBeInTheDocument()
    expect(screen.queryByText("60m")).not.toBeInTheDocument()
  })

  it("keeps clinical detail behind the clinical scope", async () => {
    mocks.hasClinicalScope = false
    mocks.getById.mockResolvedValue(
      makeSession({ clinical_outcome: "Completed", issue_topic: "bereavement" } as never),
    )
    renderWithProviders(<Page />)
    expect(await screen.findByText(/needs the clinical access scope/)).toBeInTheDocument()
    expect(screen.queryByText("bereavement")).not.toBeInTheDocument()
  })

  it("renders the audit trail on the history tab rather than a placeholder", async () => {
    const user = userEvent.setup()
    mocks.getEntityHistory.mockResolvedValue([
      {
        id: "a1",
        action_type: "UPDATE",
        resource_type: "ServiceSession",
        resource_id: "sess-1",
        occurred_at: "2026-08-27T10:00:00Z",
      },
    ])
    mocks.getEntityFieldChanges.mockResolvedValue([
      {
        id: "c1",
        audit_log_id: "a1",
        entity_type: "ServiceSession",
        entity_id: "sess-1",
        field_changes: [{ field_name: "notes", old_value: "[redacted]", new_value: "[redacted]" }],
      },
    ])
    renderWithProviders(<Page />)

    await user.click(await screen.findByRole("tab", { name: "History" }))
    await waitFor(() =>
      expect(mocks.getEntityHistory).toHaveBeenCalledWith("ServiceSession", "sess-1"),
    )
    expect(await screen.findByText("notes")).toBeInTheDocument()
    expect(screen.queryByText(/once the audit feed is wired up/)).not.toBeInTheDocument()
  })
})
