import { screen, waitFor } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { beforeEach, describe, expect, it, vi } from "vitest"

vi.mock("@/api/endpoints/industries", () => ({
  industriesApi: {
    list: vi.fn(),
    getById: vi.fn(),
    getChildren: vi.fn(),
  },
}))
vi.mock("@/components/common/AuthedLayout", () => ({
  AuthedLayout: ({ children }: { children: React.ReactNode }) => <div>{children}</div>,
}))

import { industriesApi } from "@/api/endpoints/industries"
import { renderWithProviders } from "@/test/utils"
import type { Industry } from "@/types/entities"

import { Route } from "./industries"

const PAGE_SIZE = 20

function industry(
  id: string,
  name: string,
  code: string,
  parentId: string | null = null,
): Industry {
  return { id, name, code, parent_industry_id: parentId } as Industry
}

const PARENT = industry("i_agr", "Agriculture & Agribusiness", "AGR")
/** Deep in the list, so paging to it is the only way to reach it. */
const CHILD = industry("i_lst", "Livestock Farming", "AGR-LST", "i_agr")

/** 140 rows: the child sits at index 120, which is page 7 of 20. */
const ALL = [
  PARENT,
  ...Array.from({ length: 119 }, (_, i) => industry(`i_${i}`, `Industry ${i}`, `IND-${i}`)),
  CHILD,
  ...Array.from({ length: 19 }, (_, i) => industry(`i_z${i}`, `Zed ${i}`, `ZED-${i}`)),
]

function renderPage() {
  const Page = Route.options.component as React.ComponentType
  return renderWithProviders(<Page />)
}

beforeEach(() => {
  vi.clearAllMocks()
  vi.mocked(industriesApi.list).mockImplementation(async (params) => {
    const limit = params?.limit ?? PAGE_SIZE
    const page = params?.page ?? 1
    const search = params?.search?.toLowerCase()
    const matched = search ? ALL.filter((row) => row.name.toLowerCase().includes(search)) : ALL
    const offset = (page - 1) * limit
    const items = matched.slice(offset, offset + limit)
    return { items, total: matched.length, page, limit, has_more: offset + limit < matched.length }
  })
  vi.mocked(industriesApi.getById).mockImplementation(
    async (id: string) => ALL.find((row) => row.id === id) as Industry,
  )
  vi.mocked(industriesApi.getChildren).mockImplementation(async (id: string) =>
    id === PARENT.id ? [CHILD] : [],
  )
})

describe("following the hierarchy", () => {
  it("pages the table to a child instead of searching for its code", async () => {
    const user = userEvent.setup()
    renderPage()

    await user.click(await screen.findByRole("cell", { name: /Agriculture & Agribusiness/ }))
    await user.click(await screen.findByRole("button", { name: "Open Livestock Farming" }))

    // The row is on page 7, and asking for it by code would match nothing:
    // the server searches names only.
    await waitFor(() =>
      expect(industriesApi.list).toHaveBeenCalledWith(
        expect.objectContaining({ page: 7, limit: PAGE_SIZE, search: undefined }),
      ),
    )
    expect(industriesApi.list).not.toHaveBeenCalledWith(
      expect.objectContaining({ search: "AGR-LST" }),
    )
    // The row is reachable rather than filtered away.
    expect((await screen.findAllByText("Livestock Farming")).length).toBeGreaterThan(0)
    expect(screen.queryByText("No industries match your filters")).not.toBeInTheDocument()
  })

  it("does not scan when the row is already on the visible page", async () => {
    const user = userEvent.setup()
    renderPage()

    const row = await screen.findByRole("cell", { name: /Agriculture & Agribusiness/ })
    await user.click(row)
    await waitFor(() =>
      expect(screen.getByRole("button", { name: /Open Livestock/ })).toBeVisible(),
    )
    const before = vi.mocked(industriesApi.list).mock.calls.length

    // The parent is on page 1, which is showing, so selecting it pages nowhere.
    await user.click(row)
    expect(vi.mocked(industriesApi.list).mock.calls.length).toBe(before)
  })
})
