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

vi.mock("@tanstack/react-router", () => ({
  Link: ({ children, to }: { children?: React.ReactNode; to?: string }) => (
    <a href={to ?? "#"}>{children}</a>
  ),
  useNavigate: () => vi.fn(),
}))

const { DashboardMain } = await import("@/components/DashboardMain")

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
    expect(screen.getByRole("heading", { name: "Services in demand" })).toBeInTheDocument()

    expect(screen.getByText("Group Counselling")).toBeInTheDocument()
  })

  it("shows which queues the import backlog is sitting in", async () => {
    // A single blocked count says a batch is stuck without saying on what, and
    // the remedy differs per queue: add a practitioner, import a roster, fix a
    // date. The KPI tile and attention panel keep carrying the total.
    renderWithProviders(<DashboardMain />)

    await screen.findByText("Stanbic Bank")
    expect(screen.getByRole("heading", { name: "Import health" })).toBeInTheDocument()
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
