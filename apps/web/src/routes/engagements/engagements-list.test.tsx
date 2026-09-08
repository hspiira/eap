/**
 * The engagements list against the live adapter, with fixtures off.
 *
 * API-01: the route typed the API's bare JSON array as a paginated envelope and
 * read `data.items` off it, so a live response with records rendered as an
 * empty state, and so did a failed request. These assert the three cases that
 * distinguished those: records render, page two asks the server for the next
 * slice, and a 500 renders an error rather than a successful empty list.
 */

import type * as TanstackRouter from "@tanstack/react-router"
import { screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import type { ReactElement } from "react"
import { beforeEach, describe, expect, it, vi } from "vitest"

import apiClient from "@/api/client"
import { renderWithProviders } from "@/test/utils"
import type { Engagement } from "@/types/entities"
import { EngagementStatus } from "@/types/enums"

vi.mock("@/lib/fixtures", () => ({ useFixtures: () => false }))

type Search = Record<string, unknown>

let search: Search = {}
const navigate = vi.fn((options: { search?: (prev: Search) => Search }) => {
  if (typeof options.search === "function") search = options.search(search)
})

vi.mock("@tanstack/react-router", async () => {
  const actual = await vi.importActual<typeof TanstackRouter>("@tanstack/react-router")
  return {
    ...actual,
    Link: ({ children }: { children: React.ReactNode }) => <a>{children}</a>,
    useSearch: () => search,
    useNavigate: () => navigate,
    createFileRoute: () => (opts: Record<string, unknown>) => ({ options: opts }),
  }
})

vi.mock("@/hooks/useCanWrite", () => ({ useCanWrite: () => true }))

function engagement(id: string, name: string): Engagement {
  return {
    id,
    tenant_id: "tenant-a",
    client_id: "client-a",
    name,
    description: null,
    status: EngagementStatus.ACTIVE,
    period_start: "2026-04-01",
    period_end: "2026-06-15",
    deliverables: [],
    hours_log: [{ id: "te-1", user_id: "u-1", logged_on: "2026-04-02", hours: 4, note: null }],
    created_by: "u-1",
    activated_at: null,
    delivered_at: null,
    invoiced_at: null,
    closed_at: null,
    created_at: "2026-03-25T10:00:00Z",
    updated_at: "2026-03-25T10:00:00Z",
  }
}

async function renderList(): Promise<void> {
  const mod = await import("@/routes/engagements/index")
  const Page = mod.Route.options.component as () => ReactElement
  renderWithProviders(<Page />)
}

beforeEach(() => {
  search = {}
  navigate.mockClear()
  vi.restoreAllMocks()
})

describe("engagements list, fixtures off", () => {
  it("renders the records a real list response carries", async () => {
    vi.spyOn(apiClient, "get").mockResolvedValue({
      items: [engagement("eng-1", "Policy refresh"), engagement("eng-2", "Branch audit")],
      total: 2,
      page: 1,
      limit: 20,
      has_more: false,
    })

    await renderList()

    expect(await screen.findByText("Policy refresh")).toBeInTheDocument()
    expect(screen.getByText("Branch audit")).toBeInTheDocument()
    expect(screen.queryByText(/no engagements yet/i)).not.toBeInTheDocument()
  })

  it("asks the server for page two rather than slicing page one", async () => {
    const get = vi.spyOn(apiClient, "get").mockResolvedValue({
      items: [engagement("eng-1", "Policy refresh")],
      total: 40,
      page: 1,
      limit: 20,
      has_more: true,
    })

    await renderList()
    await screen.findByText("Policy refresh")

    await userEvent.click(screen.getByRole("button", { name: /next/i }))
    await waitFor(() => expect(search.page).toBe(2))

    search = { page: 2 }
    await renderList()
    await waitFor(() =>
      expect(get.mock.calls.some(([, params]) => (params as { page?: number })?.page === 2)).toBe(
        true,
      ),
    )
  })

  it("shows an error, not a successful empty list, when the request fails", async () => {
    vi.spyOn(apiClient, "get").mockRejectedValue(new Error("Internal Server Error"))

    await renderList()

    expect(await screen.findByRole("button", { name: /try again/i })).toBeInTheDocument()
    expect(screen.queryByText(/no engagements yet/i)).not.toBeInTheDocument()
  })

  it("sends the status filter to the server instead of filtering the page", async () => {
    const get = vi.spyOn(apiClient, "get").mockResolvedValue({
      items: [],
      total: 0,
      page: 1,
      limit: 20,
      has_more: false,
    })
    search = { status: EngagementStatus.DRAFT }

    await renderList()

    await waitFor(() =>
      expect(
        get.mock.calls.some(
          ([, params]) => (params as { status?: string })?.status === EngagementStatus.DRAFT,
        ),
      ).toBe(true),
    )
  })
})
