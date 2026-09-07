import { screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { renderWithProviders } from "@/test/utils"
import type { Provider } from "@/types/entities"

const mocks = vi.hoisted(() => ({
  list: vi.fn(),
  canWrite: true,
  search: {} as Record<string, string>,
}))
vi.mock("@/api/endpoints/providers", () => ({ providersApi: mocks }))
vi.mock("@/hooks/useCanWrite", () => ({
  useCanWrite: () => mocks.canWrite,
  useCurrentRole: () => "Admin",
}))
vi.mock("@/components/providers/ProviderFormSheet", () => ({ ProviderFormSheet: () => null }))
vi.mock("@tanstack/react-router", () => ({
  createFileRoute: () => (options: unknown) => ({ options }),
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
  useRouterState: () => "/providers",
}))

const { Route } = await import("@/routes/providers/index")
const Page = (Route as unknown as { options: { component: React.ComponentType } }).options.component

function makeProvider(overrides: Partial<Provider> = {}): Provider {
  return {
    id: "prv-1",
    tenant_id: "tenant-1",
    display_name: "Amina Okello",
    email: null,
    phone: null,
    user_id: null,
    status: "Active",
    provider_profile: {
      tier: "T2",
      region: "KampalaMetro",
      accreditation_status: "Accredited",
      panel_status: "Active",
      specialties: [],
    },
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  } as Provider
}

function page(items: Provider[], total: number) {
  return { items, total, page: 1, limit: 20, has_more: total > items.length }
}

beforeEach(() => {
  vi.clearAllMocks()
  mocks.canWrite = true
  mocks.search = {}
  mocks.list.mockResolvedValue(page([makeProvider()], 1))
})

describe("practitioner directory", () => {
  it("names a practitioner who has no contact email and no account", async () => {
    renderWithProviders(<Page />)
    expect(await screen.findByText("Amina Okello")).toBeInTheDocument()
    expect(screen.getByText("None")).toBeInTheDocument()
  })

  it("sends filters and sort to the server rather than filtering a fetched page", async () => {
    mocks.search = { tier: "T1", region: "Eastern", panel_status: "Suspended" }
    renderWithProviders(<Page />)
    await waitFor(() => expect(mocks.list).toHaveBeenCalled())
    expect(mocks.list).toHaveBeenCalledWith(
      expect.objectContaining({
        tier: ["T1"],
        region: ["Eastern"],
        panel_status: ["Suspended"],
        page: 1,
        sort_by: "display_name",
        sort_desc: false,
      }),
    )
  })

  it("pages through a dataset larger than one page and keeps the full total", async () => {
    const first = Array.from({ length: 20 }, (_, i) =>
      makeProvider({ id: `prv-${i}`, display_name: `Practitioner ${i}` }),
    )
    mocks.list.mockResolvedValue(page(first, 137))
    const user = userEvent.setup()
    renderWithProviders(<Page />)

    // The count is the server's total for the whole matching set, not the page.
    expect(await screen.findByText(/137/)).toBeInTheDocument()

    mocks.list.mockResolvedValue(page([makeProvider({ id: "prv-99" })], 137))
    await user.click(screen.getByRole("button", { name: /next/i }))
    await waitFor(() =>
      expect(mocks.list).toHaveBeenCalledWith(expect.objectContaining({ page: 2 })),
    )
  })

  it("offers no create action to a viewer", async () => {
    mocks.canWrite = false
    renderWithProviders(<Page />)
    await screen.findByText("Amina Okello")
    expect(screen.queryByRole("button", { name: /add practitioner/i })).not.toBeInTheDocument()
  })
})
