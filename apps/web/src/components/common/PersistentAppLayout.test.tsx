import { useEffect } from "react"

import {
  createMemoryHistory,
  createRootRoute,
  createRoute,
  createRouter,
  Link,
  Outlet,
  RouterProvider,
} from "@tanstack/react-router"
import { screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, expect, it, vi } from "vitest"

import { PersistentAppLayout } from "@/components/common/PersistentAppLayout"
import { useSidebar } from "@/components/ui/sidebar"
import { renderWithProviders } from "@/test/utils"

const state = vi.hoisted(() => ({ isAuthenticated: true, mounts: 0 }))

vi.mock("@/store/slices/authSlice", () => ({
  useAuthStore: (selector: (value: typeof state) => unknown) => selector(state),
}))
vi.mock("@/components/AppSidebar", () => ({
  AppSidebar: () => {
    const { open, toggle } = useSidebar()
    useEffect(() => {
      state.mounts += 1
    }, [])
    return (
      <nav aria-label="Main">
        <button onClick={toggle}>{open ? "Collapse" : "Expand"}</button>
        <Link to="/clients">Clients</Link>
        <Link to="/members">Members</Link>
        <Link to="/audit">Audits</Link>
      </nav>
    )
  },
}))
vi.mock("@/components/DashboardHeader", () => ({ DashboardHeader: () => <header>Header</header> }))
vi.mock("@/components/common/FixtureBanner", () => ({ FixtureBanner: () => null }))
vi.mock("@/components/search/GlobalSearch", () => ({ GlobalSearch: () => null }))

function renderRouter(path: string) {
  const root = createRootRoute({
    component: () => (
      <PersistentAppLayout>
        <Outlet />
      </PersistentAppLayout>
    ),
  })
  const routes = ["/clients", "/members", "/audit", "/auth/login", "/"].map((routePath) =>
    createRoute({
      getParentRoute: () => root,
      path: routePath,
      component: () => <h1>{routePath}</h1>,
    }),
  )
  const router = createRouter({
    routeTree: root.addChildren(routes),
    history: createMemoryHistory({ initialEntries: [path] }),
  })
  renderWithProviders(<RouterProvider router={router} />)
}

beforeEach(() => {
  state.isAuthenticated = true
  state.mounts = 0
  localStorage.clear()
})

it("keeps chrome and sidebar state mounted while different sections load", async () => {
  const user = userEvent.setup()
  renderRouter("/clients")
  await screen.findByRole("heading", { name: "/clients" })
  const sidebar = screen.getByRole("navigation", { name: "Main" })
  const header = screen.getByText("Header")
  await user.click(screen.getByRole("button", { name: "Expand" }))
  for (const [label, path] of [
    ["Members", "/members"],
    ["Audits", "/audit"],
  ]) {
    await user.click(screen.getByRole("link", { name: label }))
    await screen.findByRole("heading", { name: path })
    expect(screen.getByRole("navigation", { name: "Main" })).toBe(sidebar)
    expect(screen.getByText("Header")).toBe(header)
    expect(screen.getByRole("button", { name: "Collapse" })).toBeInTheDocument()
  }
  await waitFor(() => expect(state.mounts).toBe(1))
})

it("keeps authentication pages outside the chrome even for a signed-in user", async () => {
  renderRouter("/auth/login")
  await screen.findByRole("heading", { name: "/auth/login" })
  expect(screen.queryByRole("navigation")).not.toBeInTheDocument()
})

it("does not render authenticated chrome for a signed-out visitor", async () => {
  state.isAuthenticated = false
  renderRouter("/")
  await screen.findByRole("heading", { name: "/" })
  expect(screen.queryByRole("navigation")).not.toBeInTheDocument()
})
