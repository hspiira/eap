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
    expect(screen.getByRole("heading", { name: "Import health" })).toBeInTheDocument()

    expect(screen.getByText("Group Counselling")).toBeInTheDocument()

    // Import health reads as a composition of the whole batch.
    expect(screen.getByText("Accepted")).toBeInTheDocument()
    expect(screen.getByText("Already held")).toBeInTheDocument()
    expect(screen.getByText("Blocked")).toBeInTheDocument()
    expect(screen.getByText("Member not on a roster")).toBeInTheDocument()
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

  it("keeps the onboarding checklist off for a working tenant", async () => {
    renderWithProviders(<DashboardMain />)
    await screen.findByText("Stanbic Bank")
    expect(screen.queryByText("Add first client")).not.toBeInTheDocument()
  })
})
