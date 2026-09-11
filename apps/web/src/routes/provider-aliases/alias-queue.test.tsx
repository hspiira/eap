import { screen, waitFor, within } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"

import type { ProviderAlias } from "@/api/endpoints/provider-aliases"
import { renderWithProviders } from "@/test/utils"

const mocks = vi.hoisted(() => ({
  list: vi.fn(),
  create: vi.fn(),
  resolve: vi.fn(),
  reject: vi.fn(),
  getProvider: vi.fn(),
  listProviders: vi.fn(),
  role: "Admin" as string,
  search: {} as Record<string, unknown>,
  listeners: new Set<() => void>(),
  showSuccess: vi.fn(),
  showError: vi.fn(),
}))

vi.mock("@/api/endpoints/provider-aliases", () => ({
  providerAliasesApi: {
    list: mocks.list,
    create: mocks.create,
    resolve: mocks.resolve,
    reject: mocks.reject,
  },
}))
vi.mock("@/api/endpoints/providers", () => ({
  providersApi: { getById: mocks.getProvider, list: mocks.listProviders },
}))
vi.mock("@/hooks/useCanWrite", () => ({
  useCanWrite: () => true,
  useCurrentRole: () => mocks.role,
}))
// Partial: the test wrapper still renders the real ToastProvider.
vi.mock("@/contexts/ToastContext", async (importOriginal) => ({
  ...(await importOriginal<object>()),
  useToast: () => ({ showSuccess: mocks.showSuccess, showError: mocks.showError }),
}))
vi.mock("@/store/slices/tenantSlice", () => ({
  useTenantStore: (select: (state: { currentTenantId: string }) => unknown) =>
    select({ currentTenantId: "tenant-1" }),
}))
vi.mock("@tanstack/react-router", async () => {
  const { useEffect, useReducer } = await import("react")
  return {
    createFileRoute: () => (options: unknown) => ({ options }),
    Link: ({ children, to, ...rest }: { children: React.ReactNode; to?: string }) => (
      <a href={to} {...rest}>
        {children}
      </a>
    ),
    useNavigate:
      () => (opts: { search: (prev: Record<string, unknown>) => Record<string, unknown> }) => {
        mocks.search = opts.search(mocks.search)
        for (const listener of mocks.listeners) listener()
      },
    useSearch: () => {
      const [, rerender] = useReducer((count: number) => count + 1, 0)
      useEffect(() => {
        mocks.listeners.add(rerender)
        return () => {
          mocks.listeners.delete(rerender)
        }
      }, [])
      return mocks.search
    },
    useRouterState: () => "/provider-aliases",
  }
})

const { Route } = await import("@/routes/provider-aliases/index")
const Page = (Route as unknown as { options: { component: React.ComponentType } }).options.component

function empty() {
  return { items: [], total: 0, page: 1, limit: 20, has_more: false }
}

function makeAlias(overrides: Partial<ProviderAlias> = {}): ProviderAlias {
  return {
    id: "alias-1",
    tenant_id: "tenant-1",
    source_system: "activity-log-workbook",
    source_value: "Dr. Jane N. Achieng",
    normalized_value: "jane n achieng",
    state: "Unmapped",
    provider_id: null,
    candidate_provider_ids: [],
    review_note: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  } as ProviderAlias
}

function page(items: ProviderAlias[], total = items.length) {
  return { items, total, page: 1, limit: 20, has_more: total > items.length }
}

beforeEach(() => {
  vi.clearAllMocks()
  mocks.role = "Admin"
  mocks.search = {}
  mocks.listeners.clear()
  mocks.list.mockResolvedValue(page([makeAlias()]))
  mocks.getProvider.mockResolvedValue({ id: "prv-1", display_name: "Amina Okello" })
  mocks.listProviders.mockResolvedValue(empty())
})

describe("alias review queue", () => {
  it("asks the server only for the source system the importer reads", async () => {
    renderWithProviders(<Page />)
    await waitFor(() => expect(mocks.list).toHaveBeenCalled())
    expect(mocks.list).toHaveBeenCalledWith(
      expect.objectContaining({
        tenant_id: "tenant-1",
        source_system: "activity-log-workbook",
      }),
    )
  })

  it("filters by state on the server rather than narrowing a fetched page", async () => {
    mocks.search = { state: "Ambiguous" }
    renderWithProviders(<Page />)
    await waitFor(() =>
      expect(mocks.list).toHaveBeenCalledWith(expect.objectContaining({ state: "Ambiguous" })),
    )
  })

  it("names the practitioner behind a resolved alias instead of showing its id", async () => {
    mocks.list.mockResolvedValue(page([makeAlias({ state: "Resolved", provider_id: "prv-1" })]))
    renderWithProviders(<Page />)
    expect(await screen.findByText("Amina Okello")).toBeInTheDocument()
  })

  it("offers a rejected alias a way back, because rejecting is not final", async () => {
    mocks.list.mockResolvedValue(page([makeAlias({ state: "Rejected", review_note: "A room" })]))
    renderWithProviders(<Page />)
    expect(await screen.findByRole("button", { name: "Resolve" })).toBeInTheDocument()
    // Already rejected: offering it again would record the same decision twice.
    expect(screen.queryByRole("button", { name: "Reject" })).not.toBeInTheDocument()
  })

  it("counts the candidates an ambiguous alias carries", async () => {
    mocks.list.mockResolvedValue(
      page([makeAlias({ state: "Ambiguous", candidate_provider_ids: ["prv-1", "prv-2"] })]),
    )
    renderWithProviders(<Page />)
    expect(await screen.findByText("2 candidates")).toBeInTheDocument()
  })

  it("preselects no candidate, so resolving stays a decision a person makes", async () => {
    mocks.list.mockResolvedValue(
      page([makeAlias({ state: "Ambiguous", candidate_provider_ids: ["prv-1"] })]),
    )
    const user = userEvent.setup()
    renderWithProviders(<Page />)
    await user.click(await screen.findByRole("button", { name: "Resolve" }))

    const dialog = await screen.findByRole("dialog")
    expect(await within(dialog).findByRole("button", { name: "Amina Okello" })).toBeInTheDocument()
    expect(within(dialog).getByRole("button", { name: "Resolve" })).toBeDisabled()
  })

  it("resolves to the candidate that was clicked", async () => {
    mocks.list.mockResolvedValue(
      page([makeAlias({ state: "Ambiguous", candidate_provider_ids: ["prv-1"] })]),
    )
    mocks.resolve.mockResolvedValue(makeAlias({ state: "Resolved", provider_id: "prv-1" }))
    const user = userEvent.setup()
    renderWithProviders(<Page />)
    await user.click(await screen.findByRole("button", { name: "Resolve" }))

    const dialog = await screen.findByRole("dialog")
    await user.click(await within(dialog).findByRole("button", { name: "Amina Okello" }))
    await user.click(within(dialog).getByRole("button", { name: "Resolve" }))

    await waitFor(() => expect(mocks.resolve).toHaveBeenCalledWith("tenant-1", "alias-1", "prv-1"))
  })

  it("warns before reattributing a name that already names somebody", async () => {
    mocks.list.mockResolvedValue(page([makeAlias({ state: "Resolved", provider_id: "prv-1" })]))
    const user = userEvent.setup()
    renderWithProviders(<Page />)
    await user.click(await screen.findByRole("button", { name: "Reassign" }))

    const dialog = await screen.findByRole("dialog")
    expect(within(dialog).getByText(/reattributes every session already imported/i)).toBeVisible()
  })

  it("sends the note with a rejection, because the API requires one", async () => {
    mocks.reject.mockResolvedValue(makeAlias({ state: "Rejected" }))
    const user = userEvent.setup()
    renderWithProviders(<Page />)
    await user.click(await screen.findByRole("button", { name: "Reject" }))

    const dialog = await screen.findByRole("dialog")
    await user.type(within(dialog).getByRole("textbox"), "Meeting room, not a person")
    await user.click(within(dialog).getByRole("button", { name: "Reject" }))

    await waitFor(() =>
      expect(mocks.reject).toHaveBeenCalledWith(
        "tenant-1",
        "alias-1",
        "Meeting room, not a person",
      ),
    )
  })

  it("keeps the queue dialog open when the write fails, so the typed name survives", async () => {
    mocks.create.mockRejectedValue(new Error("nope"))
    const user = userEvent.setup()
    renderWithProviders(<Page />)
    await user.click(await screen.findByRole("button", { name: /queue a name/i }))

    const dialog = await screen.findByRole("dialog")
    await user.type(within(dialog).getByRole("textbox"), "Dr. Mary Nakato")
    await user.click(within(dialog).getByRole("button", { name: "Queue" }))

    await waitFor(() => expect(mocks.showError).toHaveBeenCalled())
    expect(screen.getByRole("dialog")).toBeInTheDocument()
    expect(screen.getByDisplayValue("Dr. Mary Nakato")).toBeInTheDocument()
  })

  it("hides every write from a non-admin, because the API refuses them anyway", async () => {
    mocks.role = "User"
    renderWithProviders(<Page />)
    expect(await screen.findByText("Dr. Jane N. Achieng")).toBeInTheDocument()
    expect(screen.queryByRole("button", { name: "Resolve" })).not.toBeInTheDocument()
    expect(screen.queryByRole("button", { name: "Reject" })).not.toBeInTheDocument()
    expect(screen.queryByRole("button", { name: /queue a name/i })).not.toBeInTheDocument()
  })
})
