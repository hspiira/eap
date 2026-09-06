/**
 * Happy path for the contracts list: the client column shows the client's
 * name resolved from the lookup, not a truncated id, and the term renders
 * from the wire-true period object.
 */

import { describe, expect, it, vi } from "vitest"

import { renderWithProviders } from "@/test/utils"

vi.mock("@tanstack/react-router", () => ({
  createFileRoute: () => (opts: Record<string, unknown>) => ({ options: opts }),
  Link: ({ children }: { children?: React.ReactNode }) => <a>{children}</a>,
  useNavigate: () => vi.fn(),
  useSearch: () => ({}),
}))

vi.mock("@/api/endpoints/contracts", () => ({
  contractsApi: {
    list: vi.fn().mockResolvedValue({
      items: [
        {
          id: "ct_1",
          client_id: "cl_1",
          status: "Active",
          period: {
            start_date: "2026-01-01T00:00:00Z",
            end_date: "2026-12-31T00:00:00Z",
            duration_months: 12,
          },
          billing_rate: { amount: "2500000.00", currency: "KES" },
          payment_frequency: "Monthly",
          payment_status: "Paid",
          is_auto_renew: true,
          is_active: true,
          days_remaining: 200,
          created_at: "2026-01-05T00:00:00Z",
          updated_at: "2026-01-05T00:00:00Z",
        },
      ],
      total: 1,
      page: 1,
      limit: 20,
    }),
  },
}))
vi.mock("@/api/endpoints/clients", () => ({
  clientsApi: {
    list: vi.fn().mockResolvedValue({
      items: [
        {
          id: "cl_1",
          name: "Stanbic Bank Uganda",
          status: "Active",
          created_at: "2026-01-05T00:00:00Z",
          updated_at: "2026-01-05T00:00:00Z",
        },
      ],
      total: 1,
    }),
  },
}))

const { Route } = await import("@/routes/contracts/index")
const Page = (Route as unknown as { options: { component: React.ComponentType } }).options.component

describe("contracts list: happy path", () => {
  /**
   * The limit assertion rides along with this render because the clients
   * endpoint caps limit at 100: asking for more 422s, the lookup resolves to
   * nothing, and every row silently reads "Unknown client" while the detail
   * page resolves the same client fine.
   */
  it("resolves the client name from a lookup the endpoint will accept", async () => {
    const screen = renderWithProviders(<Page />)
    expect(await screen.findByText("Stanbic Bank Uganda")).toBeInTheDocument()
    expect(screen.queryByText("cl_1")).not.toBeInTheDocument()
    expect(screen.queryByText("Unknown client")).not.toBeInTheDocument()

    const { clientsApi } = await import("@/api/endpoints/clients")
    const list = clientsApi.list as unknown as { mock: { calls: [{ limit?: number }][] } }
    expect(list.mock.calls.length).toBeGreaterThan(0)
    for (const [params] of list.mock.calls) {
      expect(params?.limit ?? 0).toBeLessThanOrEqual(100)
    }
  })
})
