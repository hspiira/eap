/**
 * Happy path for the sessions list: the service column resolves to the
 * service's name through the lookup, not an id fragment.
 */

import { describe, expect, it, vi } from "vitest"

import { renderWithProviders } from "@/test/utils"

vi.mock("@tanstack/react-router", () => ({
  createFileRoute: () => (opts: Record<string, unknown>) => ({ options: opts }),
  Link: ({ children }: { children?: React.ReactNode }) => <a>{children}</a>,
  useNavigate: () => vi.fn(),
  useSearch: () => ({}),
}))

vi.mock("@/api/endpoints/service-sessions", () => ({
  serviceSessionsApi: {
    list: vi.fn().mockResolvedValue({
      items: [
        {
          id: "ss_1",
          service_id: "sv_1",
          member_id: "p_1",
          client_id: "c_1",
          attendance: "Individual",
          // The list endpoint resolves names server-side since C1; the row is
          // the wire shape, not something the page looks up per id.
          service_name: "Short-term counselling",
          member_display_label: "Janet Nakato",
          client_name: "Acme",
          status: "Scheduled",
          session_type: "Online",
          session_category: "Individual",
          scheduled_at: "2026-08-01T09:00:00Z",
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
vi.mock("@/api/endpoints/services", () => ({
  servicesApi: {
    list: vi.fn().mockResolvedValue({
      items: [
        {
          id: "sv_1",
          name: "Short-term counselling",
          status: "Active",
          created_at: "2026-01-05T00:00:00Z",
          updated_at: "2026-01-05T00:00:00Z",
        },
      ],
      total: 1,
    }),
  },
}))
vi.mock("@/api/endpoints/members", () => ({
  membersApi: {
    getById: vi.fn().mockResolvedValue({
      id: "p_1",
      display_label: "Janet Nakato",
      employer_member_id: "HR-1",
      status: "Active",
    }),
  },
}))
vi.mock("@/api/endpoints/users", () => ({
  usersApi: { getById: vi.fn() },
}))

const { Route } = await import("@/routes/service-sessions/index")
const Page = (Route as unknown as { options: { component: React.ComponentType } }).options.component

describe("sessions list: happy path", () => {
  it("leads with the attendee and resolves the service name", async () => {
    const screen = renderWithProviders(<Page />)
    // A session's name-like value is who it was for, not when it happened.
    const lead = await screen.findByText("Janet Nakato")
    expect(lead.closest("a")).not.toBeNull()
    expect(await screen.findByText("Short-term counselling")).toBeInTheDocument()
    expect(screen.queryByText("sv_1")).not.toBeInTheDocument()
  })

  it("offers no sort the list endpoint refuses", async () => {
    // The endpoint sorts on the session's own columns. Offering member_id or
    // service_id sent a sort_by it rejects, and the page showed the error
    // instead of the list.
    const source = (await import("@/routes/service-sessions/index?raw")).default as string
    const offered = [...source.matchAll(/field="([a-z_]+)"/g)].map((match) => match[1])
    expect(offered).toEqual(expect.arrayContaining(["scheduled_at", "status"]))
    expect(offered.filter((field) => field.endsWith("_id"))).toEqual([])
  })

  it("gates the outcome filter and sort on clinical scope", async () => {
    // Pins that both sit behind the same hasClinicalScope check.
    const source = (await import("@/routes/service-sessions/index?raw")).default as string
    const outcomeFilter = source.match(
      /hasClinicalScope \? \(\s*<FilterTrigger[\s\S]*?clinical_outcome/,
    )
    const outcomeSort = source.match(
      /hasClinicalScope \? \(\s*<SortHeader field="clinical_outcome"/,
    )
    expect(outcomeFilter).not.toBeNull()
    expect(outcomeSort).not.toBeNull()
  })
})
