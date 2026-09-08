/** Happy path for the services list, and the one-value-per-cell rule. */

import { within } from "@testing-library/react"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { renderWithProviders } from "@/test/utils"

vi.mock("@tanstack/react-router", () => ({
  createFileRoute: () => (opts: Record<string, unknown>) => ({ options: opts }),
  Link: ({ children }: { children?: React.ReactNode }) => <a>{children}</a>,
  useNavigate: () => vi.fn(),
  useSearch: () => ({}),
}))

vi.mock("@/api/endpoints/services", () => ({
  servicesApi: { list: vi.fn() },
}))

import { servicesApi } from "@/api/endpoints/services"

const ITEMS = [
  {
    id: "sv_1",
    name: "Short-term counselling",
    description:
      "Confidential one-to-one counselling for an employee or a covered dependant, " +
      "delivered as a bounded course of sessions rather than open-ended therapy.",
    status: "Active",
    category: "ShortTermCounselling",
    is_group_service: false,
    max_participants: null,
    created_at: "2026-01-05T00:00:00Z",
    updated_at: "2026-01-05T00:00:00Z",
  },
  {
    id: "sv_2",
    name: "Group Counselling",
    description: null,
    status: "Active",
    category: "CISMResponse",
    is_group_service: true,
    max_participants: 12,
    created_at: "2026-01-05T00:00:00Z",
    updated_at: "2026-01-05T00:00:00Z",
  },
]

// setup.ts restores all mocks after each test, which strips an implementation
// set in the factory above. Every test therefore arms the mock itself, so the
// suite does not depend on running first.
beforeEach(() => {
  vi.mocked(servicesApi.list).mockResolvedValue({
    items: ITEMS,
    total: ITEMS.length,
    page: 1,
    limit: 20,
  } as never)
})

const { Route } = await import("@/routes/services/index")
const Page = (Route as unknown as { options: { component: React.ComponentType } }).options.component

describe("services list: happy path", () => {
  it("renders the service by name", async () => {
    const screen = renderWithProviders(<Page />)
    expect(await screen.findByText("Short-term counselling")).toBeInTheDocument()
    expect(screen.getByText("Short term counselling")).toBeInTheDocument()
  })
})

describe("services list: one value per cell", () => {
  /**
   * The name cell used to stack the description underneath the name, and the
   * group cell fused is_group_service with max_participants into strings like
   * "Up to 12". Catalogue descriptions run to a paragraph, so the stacked line
   * overflowed the column. Both facts belong on the detail page, which already
   * carries them as their own rows.
   */
  it("shows the name without the description stacked under it", async () => {
    const screen = renderWithProviders(<Page />)

    expect(await screen.findByText("Short-term counselling")).toBeInTheDocument()
    expect(screen.queryByText(/Confidential one-to-one counselling/)).not.toBeInTheDocument()
  })

  it("shows the group cell as a single value, without the participant count", async () => {
    const screen = renderWithProviders(<Page />)

    // "Group" is also a column header, so assert inside the row itself.
    const row = (await screen.findByText("Group Counselling")).closest("tr")
    if (!row) throw new Error("no row for Group Counselling")

    expect(within(row).getByText("Group")).toBeInTheDocument()
    expect(within(row).queryByText(/Up to 12/)).not.toBeInTheDocument()
    expect(within(row).queryByText("12")).not.toBeInTheDocument()
  })
})
