/**
 * Dashboard happy path against the DEV fixture: the KPI strip, trend chart,
 * utilisation lists, import health and data-quality queues all render the
 * aggregate's figures.
 */

import { screen, waitFor } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"

import { renderWithProviders } from "@/test/utils"

vi.mock("@tanstack/react-router", () => ({
  Link: ({ children }: { children?: React.ReactNode }) => <a>{children}</a>,
  useNavigate: () => vi.fn(),
}))

const { DashboardMain } = await import("@/components/DashboardMain")

describe("DashboardMain", () => {
  it("renders the aggregate figures", async () => {
    renderWithProviders(<DashboardMain />)

    await waitFor(() => expect(screen.getByText("41")).toBeInTheDocument())

    expect(screen.getByText("Sessions, 90 days")).toBeInTheDocument()
    expect(screen.getByText("7.1k")).toBeInTheDocument()
    expect(screen.getByText("5 of 43 clients have a roster")).toBeInTheDocument()

    expect(screen.getByText("Sessions delivered")).toBeInTheDocument()
    expect(screen.getByText("Vivo Energy")).toBeInTheDocument()
    expect(screen.getByText("Group")).toBeInTheDocument()

    expect(screen.getByText("sessions.csv")).toBeInTheDocument()
    expect(screen.getByText("Members not on a roster")).toBeInTheDocument()
    expect(screen.getByText("6,444")).toBeInTheDocument()

    expect(screen.getByText("Practitioners pending activation")).toBeInTheDocument()
    expect(screen.getByText("112")).toBeInTheDocument()
  })

  it("keeps the onboarding checklist off for a working tenant", async () => {
    renderWithProviders(<DashboardMain />)
    await waitFor(() => expect(screen.getByText("41")).toBeInTheDocument())
    expect(screen.queryByText("Add first client")).not.toBeInTheDocument()
  })
})
