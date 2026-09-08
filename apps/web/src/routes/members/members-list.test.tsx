import { screen, waitFor, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { makeMember } from "@/test/members"
import { renderWithProviders } from "@/test/utils"
import { MemberRelation } from "@/types/enums"

const mocks = vi.hoisted(() => ({
  list: vi.fn(),
  exportCsv: vi.fn(),
  getImportTemplate: vi.fn(),
  scanDuplicates: vi.fn(),
  getStats: vi.fn(),
  listClients: vi.fn(),
  canWrite: true,
  role: "Admin",
  search: {} as Record<string, string>,
}))
vi.mock("@/api/endpoints/members", () => ({ membersApi: mocks }))
vi.mock("@/api/endpoints/clients", () => ({ clientsApi: { list: mocks.listClients } }))
vi.mock("@/hooks/useCanWrite", () => ({
  useCanWrite: () => mocks.canWrite,
  useCurrentRole: () => mocks.role,
}))
vi.mock("@/components/MemberMergeDialog", () => ({
  MemberMergeDialog: ({
    open,
    members,
    onMerged,
  }: {
    open: boolean
    members: unknown[] | null
    onMerged: () => void
  }) =>
    open ? (
      <span role="button" tabIndex={0} onClick={onMerged}>
        Confirm merge {members?.length}
      </span>
    ) : null,
}))
vi.mock("@/components/MemberFormSheet", () => ({ MemberFormSheet: () => null }))
vi.mock("@tanstack/react-router", () => ({
  createFileRoute: () => (options: unknown) => ({ options }),
  // Forwards aria-label and className so tests can assert on the rendered
  // anchor the way a user's screen reader would find it.
  Link: ({
    children,
    to: _to,
    params: _params,
    ...rest
  }: {
    children: React.ReactNode
    to?: string
    params?: unknown
  }) => (
    <a href={_to} {...rest}>
      {children}
    </a>
  ),
  useNavigate: () => vi.fn(),
  useSearch: () => mocks.search,
}))

const { Route } = await import("@/routes/members/index")
const Page = (Route as unknown as { options: { component: React.ComponentType } }).options.component

beforeEach(() => {
  vi.clearAllMocks()
  mocks.canWrite = true
  mocks.role = "Admin"
  mocks.search = {}
  mocks.list.mockResolvedValue({
    items: [makeMember()],
    total: 1,
    page: 1,
    limit: 20,
    has_more: false,
  })
  mocks.getStats.mockResolvedValue({
    total: 1,
    active: 1,
    suspended: 0,
    pending: 0,
    terminated: 0,
    with_account: 0,
  })
  mocks.listClients.mockResolvedValue({
    items: [{ id: "client-1", name: "Acme Ltd" }],
    total: 1,
    page: 1,
    limit: 100,
    has_more: false,
  })
  mocks.exportCsv.mockResolvedValue(new Blob(["id\nmember-1"]))
  mocks.getImportTemplate.mockResolvedValue(new Blob(["Company Code,Staff_ID\n"]))
  mocks.scanDuplicates.mockResolvedValue({ items: [], scanned: 1 })
  Object.defineProperty(URL, "createObjectURL", {
    configurable: true,
    value: vi.fn(() => "blob:members"),
  })
  Object.defineProperty(URL, "revokeObjectURL", { configurable: true, value: vi.fn() })
  vi.spyOn(HTMLAnchorElement.prototype, "click").mockImplementation(() => {})
})

describe("member roster", () => {
  it("selects a row and exports only those member IDs", async () => {
    const user = userEvent.setup()
    renderWithProviders(<Page />)
    await user.click(await screen.findByRole("checkbox", { name: "Select Amina Namukasa" }))
    await user.click(screen.getByRole("button", { name: "Export selected" }))
    await waitFor(() => expect(mocks.exportCsv).toHaveBeenCalledWith({ member_ids: ["member-1"] }))
    expect(URL.revokeObjectURL).toHaveBeenCalledWith("blob:members")
  })

  it("passes the active client and relation filters to export", async () => {
    mocks.search = { client_id: "client-1", relation: "Employee" }
    const user = userEvent.setup()
    renderWithProviders(<Page />)
    await user.click(screen.getByRole("button", { name: "Export" }))
    expect(mocks.exportCsv).toHaveBeenCalledWith(
      expect.objectContaining({ client_id: "client-1", relation: "Employee" }),
    )
  })

  it("links the member to their profile and the client to theirs, keeping contact detail plain", async () => {
    mocks.list.mockResolvedValue({
      items: [
        makeMember({
          client_name: "Acme Ltd",
          staff_number: "SN-9",
          work_email: "amina@acme.test",
        }),
      ],
      total: 1,
      page: 1,
      limit: 20,
      has_more: false,
    })
    renderWithProviders(<Page />)

    const name = await screen.findByText("Amina Namukasa")
    expect(name.closest("a")).not.toBeNull()
    // The employer is a destination of its own, reached without a detour.
    expect(screen.getByText("Acme Ltd").closest("a")).not.toBeNull()

    for (const value of ["HR-1", "SN-9", "amina@acme.test"]) {
      expect(screen.getByText(value).closest("a")).toBeNull()
    }
    // The client column shows the name, never the raw id.
    expect(screen.queryByText("client-1")).not.toBeInTheDocument()
  })

  it("drops the near-empty contact columns and shows the staff number instead", async () => {
    mocks.list.mockResolvedValue({
      items: [
        makeMember({
          staff_number: "SN-9",
          personal_email: "amina@personal.test",
          phone: "+256700000000",
        }),
      ],
      total: 1,
      page: 1,
      limit: 20,
      has_more: false,
    })
    renderWithProviders(<Page />)
    await screen.findByText("Amina Namukasa")

    expect(screen.getByRole("columnheader", { name: "Staff number" })).toBeInTheDocument()
    expect(screen.getByText("SN-9")).toBeInTheDocument()
    // Filled on a handful of rows in a roster of thousands: the summary card's job.
    expect(screen.queryByText("amina@personal.test")).not.toBeInTheDocument()
    expect(screen.queryByText("+256700000000")).not.toBeInTheDocument()
  })

  it("humanizes the relationship rather than showing the raw enum", async () => {
    mocks.list.mockResolvedValue({
      items: [makeMember({ relation: MemberRelation.DOMESTIC_PARTNER })],
      total: 1,
      page: 1,
      limit: 20,
      has_more: false,
    })
    renderWithProviders(<Page />)
    expect(await screen.findByText("Domestic Partner")).toBeInTheDocument()
    expect(screen.queryByText("DomesticPartner")).not.toBeInTheDocument()
  })

  it("previews the clicked member without leaving the list", async () => {
    const user = userEvent.setup()
    mocks.list.mockResolvedValue({
      items: [makeMember({ staff_number: "SN-9", phone: "+256700000000" })],
      total: 1,
      page: 1,
      limit: 20,
      has_more: false,
    })
    renderWithProviders(<Page />)
    await user.click(await screen.findByText("HR-1"))

    // The card carries what the table no longer does.
    expect(await screen.findByText("+256700000000")).toBeInTheDocument()
    expect(screen.getByRole("link", { name: /Open full profile/ })).toBeInTheDocument()
  })

  it("shows roster counts for the current filter context", async () => {
    mocks.getStats.mockResolvedValue({
      total: 3305,
      active: 3303,
      suspended: 1,
      pending: 0,
      terminated: 1,
      with_account: 0,
    })
    renderWithProviders(<Page />)
    expect(await screen.findByText("3,305")).toBeInTheDocument()
    expect(screen.getByText("On roster")).toBeInTheDocument()
  })

  it("offers the client filter as a visible control, not a silent URL parameter", async () => {
    mocks.search = { client_id: "client-1" }
    renderWithProviders(<Page />)
    await screen.findByText("Amina Namukasa")
    expect(await screen.findByText("Client: Acme Ltd")).toBeInTheDocument()
  })

  it("shows status as an icon with an accessible label rather than a badge column", async () => {
    renderWithProviders(<Page />)
    // Visually an icon with the label on hover, not badge text in the cell.
    expect(await screen.findByRole("img", { name: "Active" })).toBeInTheDocument()
    expect(within(screen.getByRole("table")).queryByText("Suspended")).not.toBeInTheDocument()
  })

  it("keeps row actions behind the ellipsis and offers a direct open icon", async () => {
    const user = userEvent.setup()
    renderWithProviders(<Page />)
    await screen.findByText("Amina Namukasa")

    expect(screen.getByRole("link", { name: "Open Amina Namukasa" })).toBeInTheDocument()
    expect(screen.queryByRole("menuitem", { name: "Edit" })).not.toBeInTheDocument()

    await user.click(screen.getByRole("button", { name: "More actions for Amina Namukasa" }))

    expect(await screen.findByRole("menuitem", { name: "Edit" })).toBeInTheDocument()
    expect(screen.getByRole("menuitem", { name: "View details" })).toBeInTheDocument()
  })

  it("hides create and edit controls from viewers", async () => {
    mocks.canWrite = false
    renderWithProviders(<Page />)
    await screen.findByText("Amina Namukasa")
    expect(screen.queryByRole("button", { name: "Add member" })).not.toBeInTheDocument()
    expect(screen.queryByRole("button", { name: "Edit" })).not.toBeInTheDocument()
  })

  it("offers manual merge only when an admin selects exactly two members", async () => {
    mocks.list.mockResolvedValue({
      items: [makeMember(), makeMember({ id: "member-2", display_label: "Amina duplicate" })],
      total: 2,
      page: 1,
      limit: 20,
      has_more: false,
    })
    const user = userEvent.setup()
    renderWithProviders(<Page />)
    await user.click(await screen.findByRole("checkbox", { name: "Select Amina Namukasa" }))
    expect(screen.queryByRole("button", { name: "Merge selected" })).not.toBeInTheDocument()
    await user.click(screen.getByRole("checkbox", { name: "Select Amina duplicate" }))
    await user.click(screen.getByRole("button", { name: "Merge selected" }))
    expect(screen.getByRole("button", { name: "Confirm merge 2" })).toBeInTheDocument()
  })
})
