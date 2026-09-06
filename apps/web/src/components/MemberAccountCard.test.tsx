import { screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { MemberAccountCard } from "@/components/MemberAccountCard"
import { makeMember } from "@/test/members"
import { renderWithProviders } from "@/test/utils"

const mocks = vi.hoisted(() => ({
  role: "Admin",
  getUser: vi.fn(),
  link: vi.fn(),
  unlink: vi.fn(),
}))
vi.mock("@/hooks/useCanWrite", () => ({ useCurrentRole: () => mocks.role }))
vi.mock("@/api/endpoints/users", () => ({ usersApi: { getById: mocks.getUser } }))
vi.mock("@/api/endpoints/members", () => ({
  membersApi: { linkAccount: mocks.link, unlinkAccount: mocks.unlink },
}))
vi.mock("@/components/common/EntityPicker", () => ({
  UserPicker: ({ onChange }: { onChange: (id: string) => void }) => (
    <button onClick={() => onChange("user-2")}>Select account</button>
  ),
}))
vi.mock("@tanstack/react-router", () => ({
  Link: ({ children }: { children: React.ReactNode }) => (
    <span role="link" tabIndex={0}>
      {children}
    </span>
  ),
}))

beforeEach(() => vi.clearAllMocks())

describe("member account access", () => {
  it("links an explicitly selected existing user", async () => {
    const user = userEvent.setup()
    const changed = vi.fn()
    const updated = makeMember({ user_id: "user-2" })
    mocks.link.mockResolvedValue(updated)
    renderWithProviders(<MemberAccountCard member={makeMember()} onChanged={changed} />)
    await user.click(screen.getByRole("button", { name: "Select account" }))
    await user.click(screen.getByRole("button", { name: "Link account" }))
    expect(mocks.link).toHaveBeenCalledWith("member-1", "user-2")
    expect(changed).toHaveBeenCalledWith(updated)
  })

  it("shows a linked account by name and lets an admin unlink it", async () => {
    const user = userEvent.setup()
    mocks.getUser.mockResolvedValue({
      id: "user-2",
      email: "member@example.test",
      display_name: "Amina",
      status: "Active",
    })
    mocks.unlink.mockResolvedValue(makeMember())
    renderWithProviders(
      <MemberAccountCard member={makeMember({ user_id: "user-2" })} onChanged={vi.fn()} />,
    )
    expect(await screen.findByRole("link", { name: "Amina" })).toBeInTheDocument()
    await user.click(screen.getByRole("button", { name: "Unlink" }))
    expect(mocks.unlink).toHaveBeenCalledWith("member-1")
  })
})
