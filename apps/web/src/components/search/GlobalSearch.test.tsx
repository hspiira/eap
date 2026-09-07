import { act, screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"

import type { GlobalSearchResponse, SearchCategoryResult } from "@/api/generated"
import { renderWithProviders } from "@/test/utils"

const mocks = vi.hoisted(() => ({
  global: vi.fn(),
  navigate: vi.fn(),
  canWrite: true,
  isPlatformAdmin: false,
  hasClinicalScope: true,
}))

vi.mock("@/api/endpoints/search", async (importOriginal) => ({
  ...(await importOriginal<object>()),
  searchApi: { global: mocks.global },
}))
vi.mock("@/hooks/useCanWrite", () => ({
  useCanWrite: () => mocks.canWrite,
  useCurrentRole: () => "Admin",
  useIsPlatformAdmin: () => ({ isPlatformAdmin: mocks.isPlatformAdmin, isLoading: false }),
  useHasClinicalScope: () => ({ hasScope: mocks.hasClinicalScope, isLoading: false }),
}))
vi.mock("@tanstack/react-router", () => ({
  useNavigate: () => mocks.navigate,
}))
vi.mock("@/store/slices/authSlice", () => ({
  useAuthStore: (selector: (s: unknown) => unknown) =>
    selector({ user_id: "u-1", email: "u@example.com" }),
}))
vi.mock("@/store/slices/tenantSlice", () => ({
  useTenantStore: (selector: (s: unknown) => unknown) =>
    selector({ currentTenant: { id: "t-1", name: "acme" } }),
}))

const { GlobalSearch } = await import("@/components/search/GlobalSearch")

function category(overrides: Partial<SearchCategoryResult> = {}): SearchCategoryResult {
  return { items: [], has_more: false, failed: false, ...overrides }
}

function response(overrides: Partial<GlobalSearchResponse> = {}): GlobalSearchResponse {
  return {
    clients: category(),
    practitioners: category(),
    provider_organisations: category(),
    ...overrides,
  }
}

const CLIENT_HIT = { id: "cl-1", label: "Acme Holdings", secondary: "ACM", type: "client" as const }

async function open(user: ReturnType<typeof userEvent.setup>) {
  renderWithProviders(<GlobalSearch />)
  await user.keyboard("{Meta>}k{/Meta}")
  return screen.findByPlaceholderText(/search clients, practitioners/i)
}

beforeEach(() => {
  vi.clearAllMocks()
  mocks.canWrite = true
  mocks.hasClinicalScope = true
  mocks.global.mockResolvedValue(response())
})

describe("opening and dismissing", () => {
  it("opens on Cmd+K", async () => {
    const user = userEvent.setup()
    expect(await open(user)).toBeInTheDocument()
  })

  it("opens on Ctrl+K", async () => {
    const user = userEvent.setup()
    renderWithProviders(<GlobalSearch />)
    await user.keyboard("{Control>}k{/Control}")
    expect(await screen.findByPlaceholderText(/search clients/i)).toBeInTheDocument()
  })

  it("closes on Escape", async () => {
    const user = userEvent.setup()
    const input = await open(user)
    await user.keyboard("{Escape}")
    await waitFor(() => expect(input).not.toBeInTheDocument())
  })

  it("names the dialog for assistive technology", async () => {
    const user = userEvent.setup()
    await open(user)
    expect(screen.getByRole("dialog", { name: "Search" })).toBeInTheDocument()
  })
})

describe("records", () => {
  it("runs no record query below the two-character floor", async () => {
    const user = userEvent.setup()
    const input = await open(user)
    await user.type(input, "a")
    await act(async () => {
      await new Promise((r) => setTimeout(r, 400))
    })
    expect(mocks.global).not.toHaveBeenCalled()
  })

  it("queries the backend once the query is long enough", async () => {
    const user = userEvent.setup()
    const input = await open(user)
    await user.type(input, "acme")
    await waitFor(() => expect(mocks.global).toHaveBeenCalled())
    expect(mocks.global.mock.calls[0][0]).toMatchObject({ q: "acme", limit: 5 })
  })

  it("renders a record with its disambiguating label", async () => {
    mocks.global.mockResolvedValue(response({ clients: category({ items: [CLIENT_HIT] }) }))
    const user = userEvent.setup()
    const input = await open(user)
    await user.type(input, "acme")
    expect(await screen.findByText("Acme Holdings")).toBeInTheDocument()
    expect(screen.getByText("ACM")).toBeInTheDocument()
  })

  it("opens the record's detail route on selection", async () => {
    mocks.global.mockResolvedValue(response({ clients: category({ items: [CLIENT_HIT] }) }))
    const user = userEvent.setup()
    const input = await open(user)
    await user.type(input, "acme")
    await user.click(await screen.findByText("Acme Holdings"))
    expect(mocks.navigate).toHaveBeenCalledWith({ to: "/clients/cl-1", search: undefined })
  })

  it("debounces rapid typing into a single request", async () => {
    const user = userEvent.setup()
    const input = await open(user)
    await user.type(input, "acme holdings")
    await waitFor(() => expect(mocks.global).toHaveBeenCalled())
    await act(async () => {
      await new Promise((r) => setTimeout(r, 400))
    })
    expect(mocks.global).toHaveBeenCalledTimes(1)
    expect(mocks.global.mock.calls[0][0].q).toBe("acme holdings")
  })

  it("passes an abort signal so a superseded request is cancelled", async () => {
    const user = userEvent.setup()
    const input = await open(user)
    await user.type(input, "acme")
    await waitFor(() => expect(mocks.global).toHaveBeenCalled())
    expect(mocks.global.mock.calls[0][1]?.signal).toBeInstanceOf(AbortSignal)
  })

  it("sends the term in the request body, never in the URL", async () => {
    const user = userEvent.setup()
    const input = await open(user)
    await user.type(input, "nakato")
    await waitFor(() => expect(mocks.global).toHaveBeenCalled())
    // searchApi.global POSTs its first argument as the body; a query string
    // would put a person's name into every access log on the path.
    expect(mocks.global.mock.calls[0][0]).toEqual({ q: "nakato", limit: 5 })
  })

  it("does not show a previous query's results under a newer query", async () => {
    mocks.global.mockImplementation(async ({ q }: { q: string }) =>
      q === "acme" ? response({ clients: category({ items: [CLIENT_HIT] }) }) : response(),
    )
    const user = userEvent.setup()
    const input = await open(user)
    await user.type(input, "acme")
    expect(await screen.findByText("Acme Holdings")).toBeInTheDocument()
    await user.clear(input)
    await user.type(input, "zzzz")
    await waitFor(() => expect(screen.queryByText("Acme Holdings")).not.toBeInTheDocument())
  })

  it("offers See all only when the category is truncated", async () => {
    mocks.global.mockResolvedValue(
      response({ clients: category({ items: [CLIENT_HIT], has_more: true }) }),
    )
    const user = userEvent.setup()
    const input = await open(user)
    await user.type(input, "acme")
    expect(await screen.findByText("See all clients")).toBeInTheDocument()
  })

  it("hides See all when nothing is truncated", async () => {
    mocks.global.mockResolvedValue(
      response({ clients: category({ items: [CLIENT_HIT], has_more: false }) }),
    )
    const user = userEvent.setup()
    const input = await open(user)
    await user.type(input, "acme")
    await screen.findByText("Acme Holdings")
    expect(screen.queryByText("See all clients")).not.toBeInTheDocument()
  })

  it("preserves the query when following See all", async () => {
    mocks.global.mockResolvedValue(
      response({ clients: category({ items: [CLIENT_HIT], has_more: true }) }),
    )
    const user = userEvent.setup()
    const input = await open(user)
    await user.type(input, "acme")
    await user.click(await screen.findByText("See all clients"))
    expect(mocks.navigate).toHaveBeenCalledWith({
      to: "/clients",
      search: { search: "acme" },
    })
  })

  it("promotes an exact match above a longer one", async () => {
    mocks.global.mockResolvedValue(
      response({
        clients: category({
          items: [
            { id: "cl-2", label: "Acme Holdings", secondary: null, type: "client" },
            { id: "cl-1", label: "Acme", secondary: null, type: "client" },
          ],
        }),
      }),
    )
    const user = userEvent.setup()
    const input = await open(user)
    await user.type(input, "acme")
    await screen.findByText("Acme")
    const rendered = screen.getAllByRole("option").map((el) => el.textContent)
    expect(rendered.indexOf("Acme")).toBeLessThan(rendered.indexOf("Acme Holdings"))
  })
})

describe("error and empty states", () => {
  it("reports a failed category rather than no results", async () => {
    mocks.global.mockResolvedValue(response({ clients: category({ failed: true }) }))
    const user = userEvent.setup()
    const input = await open(user)
    await user.type(input, "acme")
    expect(await screen.findByText(/clients could not be searched/i)).toBeInTheDocument()
    expect(screen.queryByText(/no records match/i)).not.toBeInTheDocument()
  })

  it("still shows the categories that succeeded", async () => {
    mocks.global.mockResolvedValue(
      response({
        clients: category({ failed: true }),
        practitioners: category({
          items: [
            { id: "pr-1", label: "Alice Nakato", secondary: "T1 · Central", type: "practitioner" },
          ],
        }),
      }),
    )
    const user = userEvent.setup()
    const input = await open(user)
    await user.type(input, "a c")
    expect(await screen.findByText("Alice Nakato")).toBeInTheDocument()
    expect(screen.getByText(/clients could not be searched/i)).toBeInTheDocument()
  })

  it("distinguishes a whole-request failure from an empty result", async () => {
    mocks.global.mockRejectedValue(new Error("network"))
    const user = userEvent.setup()
    const input = await open(user)
    await user.type(input, "acme")
    expect(await screen.findByText(/records could not be searched/i)).toBeInTheDocument()
    expect(screen.queryByText(/no records match/i)).not.toBeInTheDocument()
  })

  it("reports no records when every category is genuinely empty", async () => {
    const user = userEvent.setup()
    const input = await open(user)
    await user.type(input, "zzzz")
    expect(await screen.findByText(/no records match/i)).toBeInTheDocument()
  })
})

describe("pages", () => {
  it("lists destinations before any query", async () => {
    const user = userEvent.setup()
    await open(user)
    expect(screen.getByText("Clients")).toBeInTheDocument()
    expect(screen.getByText("Providers")).toBeInTheDocument()
  })

  it("finds Providers by a navigation synonym", async () => {
    const user = userEvent.setup()
    const input = await open(user)
    await user.type(input, "therapist")
    expect(screen.getByText("Providers")).toBeInTheDocument()
  })

  it("hides a clinical page from a session without the scope", async () => {
    mocks.hasClinicalScope = false
    const user = userEvent.setup()
    await open(user)
    expect(screen.queryByText("Cases")).not.toBeInTheDocument()
  })

  it("shows a clinical page to a session holding the scope", async () => {
    mocks.hasClinicalScope = true
    const user = userEvent.setup()
    await open(user)
    expect(screen.getByText("Cases")).toBeInTheDocument()
  })

  it("hides a platform-admin page from an ordinary tenant", async () => {
    mocks.isPlatformAdmin = false
    const user = userEvent.setup()
    await open(user)
    expect(screen.queryByText("Tenants")).not.toBeInTheDocument()
  })

  it("leaves a gated module listed but not selectable", async () => {
    const user = userEvent.setup()
    await open(user)
    expect(screen.getByText("Surveys").closest('[role="option"]')).toHaveAttribute(
      "aria-disabled",
      "true",
    )
  })
})

describe("actions", () => {
  it("offers only actions with a verified entry point", async () => {
    const user = userEvent.setup()
    await open(user)
    for (const label of [
      "Add client",
      "Add practitioner",
      "Add organisation",
      "Schedule session",
    ]) {
      expect(screen.getByText(label)).toBeInTheDocument()
    }
  })

  it("opens the ordinary create form rather than mutating", async () => {
    const user = userEvent.setup()
    await open(user)
    await user.click(screen.getByText("Add client"))
    expect(mocks.navigate).toHaveBeenCalledWith({ to: "/clients", search: { new: true } })
  })

  it("hides write actions from a Viewer", async () => {
    mocks.canWrite = false
    const user = userEvent.setup()
    await open(user)
    expect(screen.queryByText("Add client")).not.toBeInTheDocument()
    expect(screen.queryByText("Schedule session")).not.toBeInTheDocument()
  })

  it("offers no action that names a workflow which does not exist", async () => {
    const user = userEvent.setup()
    const input = await open(user)
    await user.type(input, "nugget")
    await waitFor(() => expect(mocks.global).toHaveBeenCalled())
    const selectable = screen.queryAllByRole("option").map((el) => el.textContent ?? "")
    expect(selectable.some((label) => /nugget/i.test(label))).toBe(false)
  })

  it("says nothing matched without flickering a stale local message", async () => {
    const user = userEvent.setup()
    const input = await open(user)
    await user.type(input, "zzzz")
    await waitFor(() => expect(screen.getByText(/no records match/i)).toBeInTheDocument())
    expect(screen.queryByText(/no pages or actions match/i)).not.toBeInTheDocument()
  })
})
