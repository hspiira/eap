import { screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"

import { renderWithProviders } from "@/test/utils"

const mocks = vi.hoisted(() => ({ open: true, clinical: true }))

vi.mock("@tanstack/react-router", () => ({
  Link: ({ children, to }: { children: React.ReactNode; to: string }) => (
    <a href={to}>{children}</a>
  ),
  useRouterState: () => "/",
}))
vi.mock("@/hooks/useCanWrite", () => ({
  useIsPlatformAdmin: () => ({ isPlatformAdmin: false, isLoading: false }),
  useHasClinicalScope: () => ({ hasScope: mocks.clinical, isLoading: false }),
}))
vi.mock("@/components/ui/sidebar", async (importOriginal) => ({
  ...(await importOriginal<object>()),
  useSidebar: () => ({ open: mocks.open, setOpen: vi.fn(), toggle: vi.fn() }),
}))

import { AppSidebar } from "./AppSidebar"

/** Modules held back for the MVP: listed, but not reachable. */
const GATED = ["Campaigns", "My Worklist", "Surveys", "Engagements"]

describe("AppSidebar MVP gating", () => {
  it("lists each gated module but leaves it disabled and unlinked", () => {
    mocks.open = true
    renderWithProviders(<AppSidebar />)

    for (const label of GATED) {
      const entry = screen.getByText(label)
      expect(entry).toBeInTheDocument()
      expect(entry.closest("a")).toBeNull()
      expect(entry.closest("button")).toBeDisabled()
    }
  })

  it("keeps the shipped modules navigable", () => {
    mocks.open = true
    renderWithProviders(<AppSidebar />)

    for (const label of ["Clients", "Members", "Sessions", "Contracts", "Services"]) {
      expect(screen.getByText(label).closest("a")).not.toBeNull()
    }
  })

  it("renders gated modules as non-links when collapsed", () => {
    mocks.open = false
    const { container } = renderWithProviders(<AppSidebar />)

    const disabled = container.querySelectorAll('[aria-disabled="true"]')
    expect(disabled.length).toBe(GATED.length)
    for (const el of disabled) {
      expect(el.tagName).not.toBe("A")
    }
  })
})

/**
 * The header owns the workspace label, the search launcher and the expand
 * control. Duplicating any of them here is what the redesign removed.
 */
describe("AppSidebar has no duplicate header controls", () => {
  it("has no search launcher when expanded", () => {
    mocks.open = true
    renderWithProviders(<AppSidebar />)
    expect(screen.queryByLabelText(/search/i)).toBeNull()
  })

  it("has no search launcher when collapsed", () => {
    mocks.open = false
    renderWithProviders(<AppSidebar />)
    expect(screen.queryByLabelText(/search/i)).toBeNull()
  })

  it("does not repeat the workspace name", () => {
    mocks.open = true
    renderWithProviders(<AppSidebar />)
    expect(screen.getByText("Evexía")).toBeInTheDocument()
  })

  it("offers no second expand control when collapsed", () => {
    mocks.open = false
    renderWithProviders(<AppSidebar />)
    expect(screen.queryByLabelText(/expand sidebar/i)).toBeNull()
  })

  it("hides a clinical module without the scope", () => {
    mocks.open = true
    mocks.clinical = false
    renderWithProviders(<AppSidebar />)
    expect(screen.queryByText("Cases")).toBeNull()
    mocks.clinical = true
  })
})
