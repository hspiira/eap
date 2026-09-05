import { screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { makeMember } from "@/test/members"
import { renderWithProviders } from "@/test/utils"

const mocks = vi.hoisted(() => ({
  list: vi.fn(),
  exportCsv: vi.fn(),
  canWrite: true,
  search: {} as Record<string, string>,
}))
vi.mock("@/api/endpoints/members", () => ({ membersApi: mocks }))
vi.mock("@/hooks/useCanWrite", () => ({ useCanWrite: () => mocks.canWrite }))
vi.mock("@/components/MemberFormSheet", () => ({ MemberFormSheet: () => null }))
vi.mock("@tanstack/react-router", () => ({
  createFileRoute: () => (options: unknown) => ({ options }),
  Link: ({ children }: { children: React.ReactNode }) => <a>{children}</a>,
  useNavigate: () => vi.fn(),
  useSearch: () => mocks.search,
}))

const { Route } = await import("@/routes/members/index")
const Page = (Route as unknown as { options: { component: React.ComponentType } }).options.component

beforeEach(() => {
  vi.clearAllMocks()
  mocks.canWrite = true
  mocks.search = {}
  mocks.list.mockResolvedValue({
    items: [makeMember()],
    total: 1,
    page: 1,
    limit: 20,
    has_more: false,
  })
  mocks.exportCsv.mockResolvedValue(new Blob(["id\nmember-1"]))
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
    await user.click(screen.getByRole("button", { name: "Export members" }))
    expect(mocks.exportCsv).toHaveBeenCalledWith(
      expect.objectContaining({ client_id: "client-1", relation: "Employee" }),
    )
  })

  it("hides create and edit controls from viewers", async () => {
    mocks.canWrite = false
    renderWithProviders(<Page />)
    await screen.findByText("Amina Namukasa")
    expect(screen.queryByRole("button", { name: "Add member" })).not.toBeInTheDocument()
    expect(screen.queryByRole("button", { name: "Edit" })).not.toBeInTheDocument()
  })
})
