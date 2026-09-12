/**
 * The gate every signed-in section sits behind.
 *
 * Each section layout used to inline its own check and render `null` when it
 * failed. A blank page is not a gate: the route still resolved, so signing out
 * and pressing back, or typing the URL, put the user back on it. This pins the
 * three states the gate has to get right, and in particular that a signed-out
 * user is sent to sign-in rather than shown nothing.
 */

import { screen, waitFor } from "@testing-library/react"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { renderWithProviders } from "@/test/utils"

const mocks = vi.hoisted(() => ({
  navigate: vi.fn(),
  isAuthenticated: true,
  isLoading: false,
}))

vi.mock("@tanstack/react-router", () => ({
  useNavigate: () => mocks.navigate,
  Outlet: () => <div>Section content</div>,
}))
vi.mock("@/components/AppLayout", () => ({
  AppLayout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))
vi.mock("@/store/slices/authSlice", () => ({
  useAuthStore: (selector: (s: { isAuthenticated: boolean; isLoading: boolean }) => unknown) =>
    selector({ isAuthenticated: mocks.isAuthenticated, isLoading: mocks.isLoading }),
}))

const { AuthedLayout } = await import("@/components/common/AuthedLayout")

beforeEach(() => {
  vi.clearAllMocks()
  mocks.isAuthenticated = true
  mocks.isLoading = false
  window.history.replaceState({}, "", "/clients?status=Active")
})

describe("AuthedLayout", () => {
  it("renders the section for a signed-in user", () => {
    renderWithProviders(<AuthedLayout />)

    expect(screen.getByText("Section content")).toBeInTheDocument()
    expect(mocks.navigate).not.toHaveBeenCalled()
  })

  it("sends a signed-out user to sign-in instead of showing a blank page", async () => {
    mocks.isAuthenticated = false

    renderWithProviders(<AuthedLayout />)

    await waitFor(() => expect(mocks.navigate).toHaveBeenCalled())
    expect(mocks.navigate.mock.calls[0][0]).toMatchObject({
      to: "/auth/login",
      replace: true,
    })
    expect(screen.queryByText("Section content")).not.toBeInTheDocument()
  })

  it("remembers where the user was so sign-in can return them to it", async () => {
    mocks.isAuthenticated = false

    renderWithProviders(<AuthedLayout />)

    await waitFor(() => expect(mocks.navigate).toHaveBeenCalled())
    expect(mocks.navigate.mock.calls[0][0].search).toMatchObject({
      redirect: "/clients?status=Active",
    })
  })

  it("waits rather than redirecting while the session is still resolving", () => {
    mocks.isLoading = true
    mocks.isAuthenticated = false

    renderWithProviders(<AuthedLayout />)

    expect(mocks.navigate).not.toHaveBeenCalled()
    expect(screen.queryByText("Section content")).not.toBeInTheDocument()
    expect(screen.getByRole("status")).toBeInTheDocument()
  })
})
