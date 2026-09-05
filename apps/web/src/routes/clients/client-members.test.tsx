import { screen, waitFor, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { Input } from "@/components/ui/input"
import { makeMember } from "@/test/members"
import { makeTestQueryClient, renderWithProviders } from "@/test/utils"
import { MemberRelation } from "@/types/enums"

const mocks = vi.hoisted(() => ({
  getClient: vi.fn(),
  listMembers: vi.fn(),
  createMember: vi.fn(),
  canWrite: true,
}))

vi.mock("@/api/endpoints/clients", () => ({
  clientsApi: {
    getById: mocks.getClient,
    getStats: async () => ({}),
    getChildren: async () => ({ items: [], total: 0 }),
    getTags: async () => [],
  },
}))
vi.mock("@/api/endpoints/members", () => ({
  membersApi: { list: mocks.listMembers, create: mocks.createMember },
}))
vi.mock("@/api/endpoints/contacts", () => ({ contactsApi: { byClient: async () => [] } }))
vi.mock("@/api/endpoints/contracts", () => ({
  contractsApi: { list: async () => ({ items: [], total: 0 }) },
}))
vi.mock("@/hooks/useCanWrite", () => ({ useCanWrite: () => mocks.canWrite }))
vi.mock("@/hooks/useTabSearchParam", async () => {
  const { useState } = await import("react")
  return { useTabSearchParam: () => useState("staff") }
})
vi.mock("@tanstack/react-router", () => ({
  createFileRoute: () => (options: unknown) => ({
    options,
    useParams: () => ({ clientId: "client-1" }),
  }),
  useNavigate: () => vi.fn(),
  Link: ({
    children,
    to,
    params,
    search,
    ...props
  }: {
    children: React.ReactNode
    to: string
    params?: Record<string, string>
    search?: Record<string, string>
  }) => (
    <a
      href={
        to.replace(/\$(\w+)/g, (_, key: string) => params?.[key] ?? key) +
        (search ? `?${new URLSearchParams(search)}` : "")
      }
      {...props}
    >
      {children}
    </a>
  ),
}))
vi.mock("@/components/common/EntityPicker", () => ({
  ClientPicker: ({ value }: { value: string }) => (
    <Input aria-label="Client" value={value} readOnly />
  ),
  EntityPicker: () => null,
  PickerRow: () => null,
}))
vi.mock("@/components/clients/ClientFormSheet", () => ({ ClientFormSheet: () => null }))
vi.mock("@/components/ContractFormSheet", () => ({ ContractFormSheet: () => null }))
vi.mock("@/components/clients/ClientDetailWidgets", () => ({
  Hero: () => null,
  DetailRail: () => null,
  ContractsPanel: () => null,
}))

const { Route } = await import("@/routes/clients/$clientId")
const Page = (Route as unknown as { options: { component: React.ComponentType } }).options.component

const emptyRoster = { items: [], total: 0, page: 1, limit: 20, has_more: false }

beforeEach(() => {
  vi.clearAllMocks()
  mocks.canWrite = true
  mocks.getClient.mockResolvedValue({ id: "client-1", name: "Acme", aliases: [] })
  mocks.listMembers.mockResolvedValue(emptyRoster)
  mocks.createMember.mockResolvedValue(makeMember())
})

describe("client members integration", () => {
  it("shows the canonical roster, total and member links with the legacy staff tab", async () => {
    mocks.listMembers.mockResolvedValue({
      ...emptyRoster,
      items: [
        makeMember(),
        makeMember({
          id: "child-1",
          display_label: "Grace Namukasa",
          relation: MemberRelation.CHILD,
          primary_employee_member_id: "member-1",
        }),
      ],
      total: 125,
      has_more: true,
    })
    renderWithProviders(<Page />)
    const employee = await screen.findByRole("link", { name: /Amina Namukasa/ })
    expect(employee).toHaveAttribute("href", "/members/member-1")
    expect(screen.getByRole("link", { name: /Grace Namukasa/ })).toHaveAttribute(
      "href",
      "/members/child-1",
    )
    expect(screen.getByRole("tab", { name: /^Members\s*125$/ })).toHaveAttribute(
      "aria-selected",
      "true",
    )
    expect(screen.getByText(/Showing 2 of 125 members/)).toBeInTheDocument()
    expect(screen.getByRole("link", { name: "View all members" })).toHaveAttribute(
      "href",
      "/members?client_id=client-1",
    )
    expect(mocks.listMembers).toHaveBeenCalledExactlyOnceWith({ client_id: "client-1", limit: 20 })
  })

  it("creates through the member form with the client selected and refreshes roster and count", async () => {
    const user = userEvent.setup()
    const queryClient = makeTestQueryClient()
    queryClient.setQueryDefaults(["clients", "list"], { gcTime: Infinity })
    queryClient.setQueryData(["clients", "list"], { items: [], total: 0 })
    renderWithProviders(<Page />, { queryClient })
    await screen.findByText("No members yet.")
    await user.click(screen.getByRole("button", { name: "Add member" }))
    const form = within(screen.getByRole("dialog"))
    expect(form.getByRole("textbox", { name: "Client" })).toHaveValue("client-1")
    await user.type(form.getByRole("textbox", { name: "Company member ID" }), "HR-1")
    await user.type(form.getByRole("textbox", { name: "Name" }), "Amina Namukasa")
    mocks.listMembers.mockResolvedValue({ ...emptyRoster, items: [makeMember()], total: 1 })
    await user.click(form.getByRole("button", { name: "Add member" }))
    expect(await screen.findByRole("link", { name: /Amina Namukasa/ })).toBeInTheDocument()
    expect(screen.getByRole("tab", { name: /^Members\s*1$/ })).toBeInTheDocument()
    expect(mocks.createMember).toHaveBeenCalledWith(
      expect.objectContaining({
        client_id: "client-1",
        employer_member_id: "HR-1",
        display_label: "Amina Namukasa",
        relation: "Employee",
      }),
    )
    await waitFor(() => expect(screen.queryByRole("dialog")).not.toBeInTheDocument())
    expect(queryClient.getQueryState(["clients", "list"])?.isInvalidated).toBe(true)
    await user.click(screen.getByRole("tab", { name: "Overview" }))
    expect(screen.getByText("✓ Roster started")).toBeInTheDocument()
  })

  it("distinguishes loading and failure from an empty roster and supports retry", async () => {
    let rejectRoster!: (error: Error) => void
    mocks.listMembers.mockReturnValue(
      new Promise((_, reject) => {
        rejectRoster = reject
      }),
    )
    const user = userEvent.setup()
    renderWithProviders(<Page />)
    expect(await screen.findByText("Loading members…")).toBeInTheDocument()
    expect(screen.queryByText("No members yet.")).not.toBeInTheDocument()
    rejectRoster(new Error("Roster unavailable"))
    expect(await screen.findByRole("alert")).toHaveTextContent("Roster unavailable")
    expect(screen.queryByText("No members yet.")).not.toBeInTheDocument()
    mocks.listMembers.mockResolvedValue(emptyRoster)
    await user.click(screen.getByRole("button", { name: "Retry" }))
    expect(await screen.findByText("No members yet.")).toBeInTheDocument()
  })

  it("keeps the roster readable for viewers without a create action", async () => {
    mocks.canWrite = false
    mocks.listMembers.mockResolvedValue({ ...emptyRoster, items: [makeMember()], total: 1 })
    renderWithProviders(<Page />)
    expect(await screen.findByRole("link", { name: /Amina Namukasa/ })).toBeInTheDocument()
    expect(screen.queryByRole("button", { name: "Add member" })).not.toBeInTheDocument()
  })

  it("does not fetch a roster for a client that cannot be loaded", async () => {
    mocks.getClient.mockRejectedValue(new Error("Client unavailable"))
    renderWithProviders(<Page />)
    await screen.findByText("Back to clients")
    expect(mocks.listMembers).not.toHaveBeenCalled()
  })
})
