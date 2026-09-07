import { screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { renderWithProviders } from "@/test/utils"

const mocks = vi.hoisted(() => ({
  getById: vi.fn(),
  navigate: vi.fn(),
  sidebarOpen: true,
  setTheme: vi.fn(),
  theme: "system" as "light" | "dark" | "system",
  openSearch: vi.fn(),
  email: "asha.k@example.com" as string | null,
}))

vi.mock("@/api/endpoints/users", () => ({ usersApi: { getById: mocks.getById } }))
vi.mock("@/lib/search-state", () => ({ openGlobalSearch: mocks.openSearch }))
vi.mock("@/lib/auth-store", () => ({ authActions: { logout: vi.fn() } }))
vi.mock("@tanstack/react-router", () => ({
  Link: ({ children, to }: { children: React.ReactNode; to: string }) => (
    <a href={to}>{children}</a>
  ),
  useNavigate: () => mocks.navigate,
}))
vi.mock("@/store/slices/authSlice", () => ({
  useAuthStore: (selector: (s: unknown) => unknown) =>
    selector({ user_id: "u-1", email: mocks.email }),
}))
vi.mock("@/store/slices/tenantSlice", () => ({
  useTenantStore: (selector: (s: unknown) => unknown) =>
    selector({ currentTenant: { id: "t-1", name: "MINET UGANDA" } }),
}))
vi.mock("@/store/slices/uiSlice", () => ({
  useUIStore: (selector: (s: unknown) => unknown) =>
    selector({ theme: mocks.theme, setTheme: mocks.setTheme }),
}))
vi.mock("@/components/ui/sidebar", async (importOriginal) => ({
  ...(await importOriginal<object>()),
  useSidebar: () => ({ open: mocks.sidebarOpen, setOpen: vi.fn(), toggle: vi.fn() }),
}))

const { DashboardHeader } = await import("@/components/DashboardHeader")

beforeEach(() => {
  vi.clearAllMocks()
  mocks.theme = "system"
  mocks.email = "asha.k@example.com"
  mocks.getById.mockResolvedValue({ id: "u-1", display_name: "Asha Kagwa", role: "Admin" })
})

describe("header chrome", () => {
  it("keeps exactly one sidebar control", async () => {
    renderWithProviders(<DashboardHeader />)
    expect(await screen.findByLabelText(/collapse sidebar/i)).toBeInTheDocument()
    expect(screen.queryAllByLabelText(/expand sidebar/i)).toHaveLength(0)
  })

  it("shows the workspace, title-cased", async () => {
    renderWithProviders(<DashboardHeader />)
    expect(await screen.findByText("Minet Uganda")).toBeInTheDocument()
  })

  it("renders no page title of its own", async () => {
    renderWithProviders(<DashboardHeader />)
    await screen.findByText("Minet Uganda")
    expect(screen.queryByRole("heading")).not.toBeInTheDocument()
  })

  it("has no notification bell", async () => {
    renderWithProviders(<DashboardHeader />)
    await screen.findByText("Minet Uganda")
    expect(screen.queryByLabelText(/notification/i)).not.toBeInTheDocument()
  })

  it("has no help link", async () => {
    renderWithProviders(<DashboardHeader />)
    await screen.findByText("Minet Uganda")
    expect(screen.queryByLabelText(/help/i)).not.toBeInTheDocument()
  })

  it("offers a desktop launcher and a mobile launcher for the one dialog", async () => {
    renderWithProviders(<DashboardHeader />)
    const user = userEvent.setup()
    await user.click(await screen.findByLabelText("Search (⌘K)"))
    await user.click(screen.getByLabelText("Search", { selector: "button" }))
    expect(mocks.openSearch).toHaveBeenCalledTimes(2)
  })

  it("advertises the keyboard shortcut on the launcher", async () => {
    renderWithProviders(<DashboardHeader />)
    expect(await screen.findByLabelText("Search (⌘K)")).toHaveAttribute(
      "aria-keyshortcuts",
      "Meta+K Control+K",
    )
  })

  it("names the categories it can actually search", async () => {
    renderWithProviders(<DashboardHeader />)
    expect(await screen.findByText(/search clients, practitioners/i)).toBeInTheDocument()
  })
})

describe("account menu", () => {
  it("shows the display name rather than the email", async () => {
    renderWithProviders(<DashboardHeader />)
    expect(await screen.findByText("Asha Kagwa")).toBeInTheDocument()
    expect(screen.queryByText("asha.k@example.com")).not.toBeInTheDocument()
  })

  it("shows a name built from the email when the account has no display name", async () => {
    mocks.getById.mockResolvedValue({ id: "u-1", display_name: null, role: "Admin" })
    renderWithProviders(<DashboardHeader />)
    // The nav label says who you are, not how you sign in.
    expect(await screen.findByText("Asha K")).toBeInTheDocument()
    expect(screen.queryByText("asha.k@example.com")).not.toBeInTheDocument()
  })

  it("never shows a raw email as the nav label", async () => {
    mocks.getById.mockResolvedValue({ id: "u-1", display_name: null, role: "Admin" })
    renderWithProviders(<DashboardHeader />)
    const trigger = await screen.findByLabelText("Account menu")
    expect(trigger.textContent).not.toContain("@")
  })

  it("shows the email inside the menu, under the name", async () => {
    renderWithProviders(<DashboardHeader />)
    const user = userEvent.setup()
    await user.click(await screen.findByLabelText("Account menu"))
    expect(await screen.findByText("asha.k@example.com")).toBeInTheDocument()
  })

  it("shows the role and workspace in the identity block", async () => {
    renderWithProviders(<DashboardHeader />)
    const user = userEvent.setup()
    await user.click(await screen.findByLabelText("Account menu"))
    expect(await screen.findByText(/Admin · Minet Uganda/)).toBeInTheDocument()
  })

  it("links to the existing profile route", async () => {
    renderWithProviders(<DashboardHeader />)
    const user = userEvent.setup()
    await user.click(await screen.findByLabelText("Account menu"))
    expect((await screen.findByText("My profile")).closest("a")).toHaveAttribute("href", "/me")
  })

  it("offers all three appearance choices explicitly", async () => {
    renderWithProviders(<DashboardHeader />)
    const user = userEvent.setup()
    await user.click(await screen.findByLabelText("Account menu"))
    for (const label of ["Light", "Dark", "System"]) {
      expect(await screen.findByText(label)).toBeInTheDocument()
    }
  })

  it("sets the chosen theme rather than cycling", async () => {
    renderWithProviders(<DashboardHeader />)
    const user = userEvent.setup()
    await user.click(await screen.findByLabelText("Account menu"))
    await user.click(await screen.findByText("Dark"))
    expect(mocks.setTheme).toHaveBeenCalledWith("dark")
  })

  it("keeps the menu open so the theme can be compared", async () => {
    renderWithProviders(<DashboardHeader />)
    const user = userEvent.setup()
    await user.click(await screen.findByLabelText("Account menu"))
    await user.click(await screen.findByText("Dark"))
    expect(screen.getByText("Light")).toBeInTheDocument()
  })

  it("offers sign out", async () => {
    renderWithProviders(<DashboardHeader />)
    const user = userEvent.setup()
    await user.click(await screen.findByLabelText("Account menu"))
    expect(await screen.findByText("Sign out")).toBeInTheDocument()
  })

  it("does not promise a password or notification screen", async () => {
    renderWithProviders(<DashboardHeader />)
    const user = userEvent.setup()
    await user.click(await screen.findByLabelText("Account menu"))
    await screen.findByText("Sign out")
    expect(screen.queryByText(/password/i)).not.toBeInTheDocument()
    expect(screen.queryByText(/notification/i)).not.toBeInTheDocument()
  })
})
