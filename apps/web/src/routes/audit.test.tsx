import { screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { renderWithProviders } from "@/test/utils"

const mocks = vi.hoisted(() => ({
  list: vi.fn(),
  getChanges: vi.fn(),
  getById: vi.fn(),
  navigate: vi.fn(),
  search: {} as Record<string, string | undefined>,
}))

vi.mock("@/api/endpoints/audit", () => ({
  auditApi: { list: mocks.list, getChanges: mocks.getChanges },
}))
vi.mock("@/api/endpoints/users", () => ({
  usersApi: { getById: mocks.getById },
}))
vi.mock("@/components/common/AuthedLayout", () => ({
  AuthedLayout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))
vi.mock("@tanstack/react-router", () => ({
  createFileRoute: () => (options: unknown) => ({
    options,
    useSearch: () => mocks.search,
    useNavigate: () => mocks.navigate,
  }),
  Link: ({ children }: { children?: React.ReactNode }) => <a>{children}</a>,
  useNavigate: () => vi.fn(),
}))

const { Route } = await import("@/routes/audit")
const Page = (Route as unknown as { options: { component: React.ComponentType } }).options.component

const LOG = {
  id: "log_1",
  tenant_id: "t_1",
  user_id: "user_1",
  action_type: "UPDATE",
  resource_type: "ServiceSession",
  resource_id: "sess_12345678",
  description: "Updated status",
  occurred_at: "2026-08-01T09:00:00Z",
}

beforeEach(() => {
  vi.clearAllMocks()
  mocks.search = {}
  mocks.list.mockResolvedValue({ items: [LOG], total: 1, page: 1, limit: 25 })
  mocks.getChanges.mockResolvedValue([])
  mocks.getById.mockResolvedValue({ id: "user_1", email: "reviewer@example.com" })
})

describe("audit console", () => {
  it("lists entries and resolves the actor's email", async () => {
    renderWithProviders(<Page />)
    expect(await screen.findByText("reviewer@example.com")).toBeInTheDocument()
    expect(screen.getByText("Updated status")).toBeInTheDocument()
  })

  it("shows an empty state distinguishing filtered from unfiltered", async () => {
    mocks.list.mockResolvedValue({ items: [], total: 0, page: 1, limit: 25 })
    renderWithProviders(<Page />)
    expect(await screen.findByText("No audit entries yet")).toBeInTheDocument()
  })

  it("names the active filter in the empty state", async () => {
    mocks.search = { action_type: "UPDATE" }
    mocks.list.mockResolvedValue({ items: [], total: 0, page: 1, limit: 25 })
    renderWithProviders(<Page />)
    expect(await screen.findByText("No audit entries match your filters")).toBeInTheDocument()
  })

  it("shows a retry action when the list fails to load", async () => {
    mocks.list.mockRejectedValue(new Error("network error"))
    renderWithProviders(<Page />)
    expect(await screen.findByText("Could not load audit logs.")).toBeInTheDocument()
    const retry = screen.getByRole("button", { name: /try again/i })
    mocks.list.mockResolvedValue({ items: [LOG], total: 1, page: 1, limit: 25 })
    await userEvent.click(retry)
    expect(await screen.findByText("Updated status")).toBeInTheDocument()
  })

  it("shows pagination reflecting the total count", async () => {
    mocks.list.mockResolvedValue({ items: [LOG], total: 40, page: 1, limit: 25 })
    renderWithProviders(<Page />)
    await screen.findByText("Updated status")
    expect(screen.getByRole("navigation", { name: "Pagination" })).toBeInTheDocument()
    expect(screen.getByRole("button", { name: "Page 2" })).toBeInTheDocument()
  })

  it("opens the detail sheet and renders redacted field changes verbatim", async () => {
    mocks.getChanges.mockResolvedValue([
      {
        id: "chg_1",
        audit_log_id: "log_1",
        entity_type: "ServiceSession",
        entity_id: "sess_1",
        field_changes: [
          { field_name: "notes", old_value: "[redacted]", new_value: "[redacted]" },
          { field_name: "status", old_value: "Scheduled", new_value: "Completed" },
        ],
      },
    ])
    renderWithProviders(<Page />)
    const row = await screen.findByRole("button", {
      name: /view changes for update on servicesession/i,
    })
    await userEvent.click(row)

    expect(await screen.findByText("notes")).toBeInTheDocument()
    expect(screen.getAllByText("[redacted]")).toHaveLength(2)
    expect(screen.getByText("Scheduled")).toBeInTheDocument()
    expect(screen.getByText("Completed")).toBeInTheDocument()
  })

  it("reports no field-level changes without inventing any", async () => {
    mocks.getChanges.mockResolvedValue([])
    renderWithProviders(<Page />)
    const row = await screen.findByRole("button", {
      name: /view changes for update on servicesession/i,
    })
    await userEvent.click(row)
    expect(await screen.findByText("No field-level changes recorded.")).toBeInTheDocument()
  })

  it("filters by resource type through the navigate-backed search param", async () => {
    renderWithProviders(<Page />)
    await screen.findByText("Updated status")
    const input = screen.getByLabelText("Filter by resource type")
    await userEvent.type(input, "ServiceSession")
    await userEvent.tab()

    await waitFor(() => expect(mocks.navigate).toHaveBeenCalled())
    const call = mocks.navigate.mock.calls[0][0] as { search: (prev: object) => object }
    expect(call.search({})).toEqual({ resource_type: "ServiceSession" })
  })
})
