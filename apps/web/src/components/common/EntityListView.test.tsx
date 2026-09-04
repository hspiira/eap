import { screen } from "@testing-library/react"
import userEvent from "@testing-library/user-event"
import { describe, expect, it, vi } from "vitest"

import { EntityListView, type ListColumn } from "@/components/common/EntityListView"
import { TableCell, TableRow } from "@/components/ui/table"
import { renderWithProviders } from "@/test/utils"

interface Row {
  id: string
  name: string
}

const COLUMNS: ListColumn[] = [{ header: "Name", sortField: "name" }, { header: "Code" }]

const ROWS: Row[] = [
  { id: "a", name: "Acme Holdings" },
  { id: "b", name: "Borealis Group" },
]

function view(props: Partial<React.ComponentProps<typeof EntityListView<Row>>> = {}) {
  const merged = {
    columns: COLUMNS,
    items: ROWS,
    rowKey: (row: Row) => row.id,
    renderRow: (row: Row) => (
      <TableRow>
        <TableCell>{row.name}</TableCell>
      </TableRow>
    ),
    loading: false,
    error: null,
    onRetry: vi.fn(),
    empty: <p>No clients yet</p>,
    sort: { field: undefined, desc: false },
    onToggleSort: vi.fn(),
    page: 1,
    total: 2,
    limit: 20,
    onPageChange: vi.fn(),
    ...props,
  }
  return { ...renderWithProviders(<EntityListView<Row> {...merged} />), props: merged }
}

describe("EntityListView", () => {
  it("renders one row per item", () => {
    view()
    expect(screen.getByText("Acme Holdings")).toBeInTheDocument()
    expect(screen.getByText("Borealis Group")).toBeInTheDocument()
  })

  it("shows the empty state instead of the table when there are no items", () => {
    view({ items: [] })
    expect(screen.getByText("No clients yet")).toBeInTheDocument()
    expect(screen.queryByRole("table")).not.toBeInTheDocument()
  })

  it("shows the error state instead of the table, and retries", async () => {
    const onRetry = vi.fn()
    view({ error: "Failed to load data", onRetry })
    expect(screen.getByText("Failed to load data")).toBeInTheDocument()
    expect(screen.queryByRole("table")).not.toBeInTheDocument()

    const retry = screen.queryByRole("button", { name: /retry|try again/i })
    if (retry) {
      await userEvent.click(retry)
      expect(onRetry).toHaveBeenCalled()
    }
  })

  it("prefers the error state over the empty state", () => {
    view({ items: [], error: "Failed to load data" })
    expect(screen.getByText("Failed to load data")).toBeInTheDocument()
    expect(screen.queryByText("No clients yet")).not.toBeInTheDocument()
  })

  it("prefers loading over both", () => {
    view({ items: [], loading: true, error: "Failed to load data" })
    expect(screen.queryByText("Failed to load data")).not.toBeInTheDocument()
    expect(screen.queryByText("No clients yet")).not.toBeInTheDocument()
  })

  it("gives the skeleton the same column count as the table", () => {
    const { unmount } = view({ loading: true })
    const skeletonCols = screen.getAllByRole("row")[0].querySelectorAll("td, th").length
    unmount()

    view()
    const headerCells = screen.getAllByRole("row")[0].querySelectorAll("th").length
    expect(skeletonCols).toBe(headerCells)
  })

  it("wires the select-all checkbox to the supplied state and handler", async () => {
    const onToggleSelectAll = vi.fn()
    view({ selectAllState: false, onToggleSelectAll })

    const selectAll = screen.getByLabelText("Select all")
    await userEvent.click(selectAll)
    expect(onToggleSelectAll).toHaveBeenCalledTimes(1)
  })

  it("reflects an indeterminate selection on the select-all checkbox", () => {
    view({ selectAllState: "indeterminate", onToggleSelectAll: vi.fn() })
    expect(screen.getByLabelText("Select all")).toHaveAttribute("data-state", "indeterminate")
  })

  it("omits the checkbox and actions columns when asked", () => {
    view({ selectable: false, actions: false })
    expect(screen.queryByLabelText("Select all")).not.toBeInTheDocument()
    expect(screen.getAllByRole("row")[0].querySelectorAll("th")).toHaveLength(COLUMNS.length)
  })

  it("makes a column sortable only when it names a field", async () => {
    const onToggleSort = vi.fn()
    view({ onToggleSort })

    await userEvent.click(screen.getByRole("button", { name: /name/i }))
    expect(onToggleSort).toHaveBeenCalledWith("name")
    expect(screen.queryByRole("button", { name: /^code$/i })).not.toBeInTheDocument()
  })

  it("renders the toolbar only when there are rows", () => {
    const { unmount } = view({ toolbar: <p>2 selected</p> })
    expect(screen.getByText("2 selected")).toBeInTheDocument()
    unmount()

    view({ items: [], toolbar: <p>2 selected</p> })
    expect(screen.queryByText("2 selected")).not.toBeInTheDocument()
  })
})
