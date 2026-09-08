import { screen, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { renderWithProviders } from "@/test/utils"

import { ClientSessionsPanel } from "./ClientSessionsPanel"

const mocks = vi.hoisted(() => ({ list: vi.fn() }))
vi.mock("@/api/endpoints/service-sessions", () => ({
  serviceSessionsApi: { list: mocks.list },
}))
vi.mock("@tanstack/react-router", () => ({
  Link: ({
    children,
    params,
    to,
  }: {
    children: React.ReactNode
    params?: Record<string, string>
    to: string
  }) => <a href={to.replace(/\$(\w+)/g, (_, key: string) => params?.[key] ?? key)}>{children}</a>,
}))

const GROUP_TALK = {
  id: "session-1",
  client_id: "client-1",
  service_name: "Group Counselling",
  provider_display_name: "Daniel Kanamara",
  member_display_label: null,
  attendance: "CompanyWide",
  status: "Completed",
  scheduled_at: "2026-08-28T09:00:00Z",
  rate_ugx: 350000,
  duration: 90,
}
const ONE_TO_ONE = {
  id: "session-2",
  client_id: "client-1",
  service_name: "Individual Counselling",
  provider_display_name: "Sarah Achieng",
  member_display_label: "Test member",
  attendance: "Individual",
  status: "Cancelled",
  scheduled_at: "2026-08-20T09:00:00Z",
  rate_ugx: null,
}

beforeEach(() => {
  vi.clearAllMocks()
  mocks.list.mockResolvedValue({ items: [GROUP_TALK, ONE_TO_ONE], total: 2 })
})

describe("client sessions panel", () => {
  it("asks the server for this client's sessions and names every row", async () => {
    renderWithProviders(<ClientSessionsPanel clientId="client-1" />)
    // Twice: the row, and the summary that opens on the first session.
    expect(await screen.findAllByText("Group Counselling")).toHaveLength(2)
    expect(mocks.list).toHaveBeenCalledWith({
      client_id: "client-1",
      page: 1,
      limit: 20,
      status: undefined,
    })
    expect(screen.getAllByText("Daniel Kanamara").length).toBeGreaterThan(0)
    expect(screen.getAllByText("UGX 350,000").length).toBeGreaterThan(0)
    // A company-wide session names no member: the client attended.
    expect(screen.getAllByText("Company-wide").length).toBeGreaterThan(0)
    expect(screen.getByText("Test member")).toBeInTheDocument()
    expect(screen.queryByText("session-1")).not.toBeInTheDocument()
  })

  it("opens on the first session and follows a click to another", async () => {
    const user = userEvent.setup()
    renderWithProviders(<ClientSessionsPanel clientId="client-1" />)
    const summary = await screen.findByRole("heading", { name: "Group Counselling" })
    expect(summary).toBeInTheDocument()
    expect(screen.getByText(/90 minutes/)).toBeInTheDocument()

    const row = screen
      .getAllByRole("row")
      .find((r) => within(r).queryByText("Individual Counselling"))
    await user.click(row!)
    expect(
      await screen.findByRole("heading", { name: "Individual Counselling" }),
    ).toBeInTheDocument()
    expect(screen.getByRole("link", { name: /Open full session/ })).toHaveAttribute(
      "href",
      "/service-sessions/session-2",
    )
  })

  it("passes the status filter to the server rather than filtering the page", async () => {
    const user = userEvent.setup()
    renderWithProviders(<ClientSessionsPanel clientId="client-1" />)
    await screen.findAllByText("Group Counselling")
    await user.click(screen.getByRole("button", { name: "All statuses" }))
    await user.click(await screen.findByRole("menuitem", { name: "Completed" }))
    expect(mocks.list).toHaveBeenLastCalledWith({
      client_id: "client-1",
      page: 1,
      limit: 20,
      status: "Completed",
    })
  })

  it("says the roster is empty rather than showing a bare table", async () => {
    mocks.list.mockResolvedValue({ items: [], total: 0 })
    renderWithProviders(<ClientSessionsPanel clientId="client-1" />)
    expect(await screen.findByText("No sessions yet")).toBeInTheDocument()
  })
})
