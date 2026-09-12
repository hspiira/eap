/**
 * Dashboard happy path against the DEV fixture: the decision panel leads,
 * the analytics cards render the aggregate, and the window control re-scopes
 * them. Chart geometry is not asserted here; jsdom gives Recharts no size, so
 * these cases cover the figures and controls around the marks.
 */

import { screen, waitFor, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"

import { makeDashboard } from "@/test/dashboard"
import { renderWithProviders } from "@/test/utils"

vi.mock("@/api/endpoints/dashboard", () => ({
  dashboardApi: { get: vi.fn(async () => makeDashboard()) },
}))

vi.mock("@/api/endpoints/service-sessions", () => ({
  serviceSessionsApi: {
    list: vi.fn(async () => ({ items: [], total: 0, page: 1, limit: 20, has_more: false })),
  },
}))

vi.mock("@tanstack/react-router", () => ({
  Link: ({ children, to }: { children?: React.ReactNode; to?: string }) => (
    <a href={to ?? "#"}>{children}</a>
  ),
  useNavigate: () => vi.fn(),
}))

const { DashboardMain } = await import("@/components/DashboardMain")
const { dashboardApi } = await import("@/api/endpoints/dashboard")
const { serviceSessionsApi } = await import("@/api/endpoints/service-sessions")

describe("DashboardMain", () => {
  it("leads with the decision panel, ranked by what is blocking", async () => {
    renderWithProviders(<DashboardMain />)

    await screen.findByText(/Activate 112 pending practitioners/)
    const panel = screen.getByRole("heading", { name: "Needs attention" })
    const card = panel.closest("div[class*='rounded-md']") as HTMLElement
    const rows = within(card).getAllByRole("link")

    expect(rows[0]).toHaveTextContent("Activate 112 pending practitioners")
    expect(rows[0]).toHaveTextContent("they cannot take new bookings")
    expect(rows[1]).toHaveTextContent("Import member rosters for 38 clients")
    // The action names the consequence, not just the count.
    expect(rows[1]).toHaveTextContent("unblocks 7,103 import rows")
  })

  it("renders the analytics cards from the aggregate", async () => {
    renderWithProviders(<DashboardMain />)

    expect(await screen.findByText("Stanbic Bank")).toBeInTheDocument()
    expect(screen.getByRole("heading", { name: "Sessions delivered" })).toBeInTheDocument()
    expect(screen.getByRole("heading", { name: "Top clients" })).toBeInTheDocument()
    expect(screen.getByRole("heading", { name: "By category" })).toBeInTheDocument()
    expect(screen.getByRole("heading", { name: "Upcoming sessions" })).toBeInTheDocument()

    // The trending card gave way to the outcome mix; its ranking restated the
    // area chart, and its percentages were noise against tiny denominators.
    expect(screen.queryByRole("heading", { name: "Services in demand" })).not.toBeInTheDocument()
    // Outcomes are clinical: the fixture carries none, so no card either.
    expect(screen.queryByRole("heading", { name: "Clinical outcomes" })).not.toBeInTheDocument()
  })

  it("shows the outcome mix only when the API sent it", async () => {
    vi.mocked(dashboardApi.get).mockResolvedValueOnce(
      makeDashboard({
        outcome_mix: [
          { outcome: "Completed", total: 3 },
          { outcome: null, total: 2 },
        ],
      }),
    )
    renderWithProviders(<DashboardMain />)

    expect(await screen.findByRole("heading", { name: "Clinical outcomes" })).toBeInTheDocument()
    expect(screen.getByText("Not recorded")).toBeInTheDocument()
  })

  it("lists the week's sessions themselves, not day counts", async () => {
    vi.mocked(dashboardApi.get).mockResolvedValueOnce(
      makeDashboard({
        upcoming: {
          total: 2,
          days: [{ bucket: "2026-09-14", label: "Mon 14", total: 2 }],
        },
      }),
    )
    vi.mocked(serviceSessionsApi.list).mockResolvedValueOnce({
      items: [
        {
          id: "ss-up-1",
          scheduled_at: "2026-09-14T09:00:00Z",
          status: "Scheduled",
          service_name: "Individual Counselling",
          client_name: "Minet Uganda",
          member_display_label: "Afimani Joseph",
          provider_display_name: "Moses Mpanga",
        },
        {
          id: "ss-up-2",
          scheduled_at: "2026-09-14T11:00:00Z",
          status: "Cancelled",
          service_name: "Cancelled thing",
        },
      ],
      total: 2,
      page: 1,
      limit: 20,
      has_more: false,
    } as never)
    renderWithProviders(<DashboardMain />)

    expect(await screen.findByText("Individual Counselling")).toBeInTheDocument()
    expect(screen.getByText("Minet Uganda / Afimani Joseph · Moses Mpanga")).toBeInTheDocument()
    // A cancelled future session is not a booking to prepare for.
    expect(screen.queryByText("Cancelled thing")).not.toBeInTheDocument()
  })

  it("no longer carries the import health card", async () => {
    // A staged batch describes file imports only: a session entered on the
    // form records no outcome, so the composition was never the whole picture.
    renderWithProviders(<DashboardMain />)

    await screen.findByText("Stanbic Bank")
    expect(screen.queryByRole("heading", { name: "Import health" })).not.toBeInTheDocument()
    // The backlog itself still has a home: the KPI tile and the attention panel.
    expect(screen.getByText("Import backlog")).toBeInTheDocument()
    expect(screen.getByText(/unblocks 7,103 import rows/)).toBeInTheDocument()
  })

  it("re-scopes the figures when the window changes", async () => {
    const user = userEvent.setup()
    renderWithProviders(<DashboardMain />)

    await screen.findByRole("heading", { name: "Sessions delivered" })
    const ninety = screen.getByRole("button", { name: "90d" })
    expect(ninety).toHaveAttribute("aria-pressed", "true")

    const week = screen.getByRole("button", { name: "Week" })
    await user.click(week)

    await waitFor(() => expect(week).toHaveAttribute("aria-pressed", "true"))
    expect(ninety).toHaveAttribute("aria-pressed", "false")
    expect(screen.getByText("this week")).toBeInTheDocument()
  })

  it("offers this year and all time beside the shorter windows", async () => {
    const user = userEvent.setup()
    renderWithProviders(<DashboardMain />)

    await screen.findByRole("heading", { name: "Sessions delivered" })
    const thisYear = screen.getByRole("button", { name: "This year" })
    await user.click(thisYear)

    await waitFor(() => expect(thisYear).toHaveAttribute("aria-pressed", "true"))
    expect(screen.getByText("this year")).toBeInTheDocument()

    const allTime = screen.getByRole("button", { name: "All time" })
    await user.click(allTime)
    await waitFor(() => expect(allTime).toHaveAttribute("aria-pressed", "true"))
    expect(screen.getByText("all time")).toBeInTheDocument()
  })

  it("offers only the years the API says have sessions, and names the chosen one", async () => {
    const user = userEvent.setup()
    renderWithProviders(<DashboardMain />)

    // The picker only exists once the API has said which years have sessions.
    await screen.findByText("Stanbic Bank")
    await user.click(await screen.findByRole("combobox", { name: "Year" }))

    const offered = (await screen.findAllByRole("option")).map((o) => o.textContent)
    expect(offered).toEqual(["2026", "2025", "2024"])

    await user.click(screen.getByRole("option", { name: "2024" }))

    // The window label names the year rather than a generic "selected year".
    await waitFor(() => expect(screen.getAllByText("2024").length).toBeGreaterThan(0))
    expect(screen.getByRole("button", { name: "90d" })).toHaveAttribute("aria-pressed", "false")
  })

  it("keeps the onboarding checklist off for a working tenant", async () => {
    renderWithProviders(<DashboardMain />)
    await screen.findByText("Stanbic Bank")
    expect(screen.queryByText("Add first client")).not.toBeInTheDocument()
  })
})
