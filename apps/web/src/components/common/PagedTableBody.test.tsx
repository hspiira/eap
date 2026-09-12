/**
 * Rows grouped back into the pages they were fetched as.
 *
 * The grouping is what lets the pagination controls say which page the user is
 * reading rather than which page the list started at, so it is pinned here
 * along with the boundary rule: where two pages are both on screen, the one
 * the user has scrolled up to is the one they have arrived at.
 */

import { render, screen } from "@testing-library/react"
import { beforeEach, describe, expect, it, vi } from "vitest"

import { PagedTableBody } from "@/components/common/PagedTableBody"
import { Table, TableCell, TableRow } from "@/components/ui/table"

interface Row {
  id: string
}

/** Drives IntersectionObserver by hand; jsdom has none. */
const observers: { cb: IntersectionObserverCallback; targets: Set<Element> }[] = []

beforeEach(() => {
  observers.length = 0
  vi.stubGlobal(
    "IntersectionObserver",
    class {
      targets = new Set<Element>()
      constructor(cb: IntersectionObserverCallback) {
        observers.push({ cb, targets: this.targets })
      }
      observe(el: Element) {
        this.targets.add(el)
      }
      unobserve(el: Element) {
        this.targets.delete(el)
      }
      disconnect() {
        this.targets.clear()
      }
    },
  )
})

function intersect(pages: Record<number, boolean>) {
  for (const observer of observers) {
    const entries = [...observer.targets]
      .map((el) => ({ target: el, page: Number((el as HTMLElement).dataset.page) }))
      .filter(({ page }) => page in pages)
      .map(({ target, page }) => ({ target, isIntersecting: pages[page] }))
    if (entries.length > 0) {
      observer.cb(entries as unknown as IntersectionObserverEntry[], {} as IntersectionObserver)
    }
  }
}

function renderBody(props: Partial<React.ComponentProps<typeof PagedTableBody<Row>>> = {}) {
  const items: Row[] = Array.from({ length: 5 }, (_, i) => ({ id: `row-${i + 1}` }))
  const onVisiblePageChange = vi.fn()
  render(
    <Table>
      <PagedTableBody<Row>
        items={items}
        anchorPage={1}
        limit={2}
        rowKey={(row) => row.id}
        renderRow={(row) => (
          <TableRow>
            <TableCell>{row.id}</TableCell>
          </TableRow>
        )}
        onVisiblePageChange={onVisiblePageChange}
        {...props}
      />
    </Table>,
  )
  return { onVisiblePageChange }
}

describe("PagedTableBody", () => {
  it("splits a flat list back into the pages it was fetched as", () => {
    renderBody()

    const bodies = document.querySelectorAll("tbody")
    expect([...bodies].map((b) => b.dataset.page)).toEqual(["1", "2", "3"])
    // The trailing page is short, and keeps only the rows it has.
    expect(bodies[2].querySelectorAll("tr")).toHaveLength(1)
    expect(screen.getByText("row-5")).toBeInTheDocument()
  })

  it("starts the numbering at the anchor, not at one", () => {
    renderBody({ anchorPage: 4 })

    expect([...document.querySelectorAll("tbody")].map((b) => b.dataset.page)).toEqual([
      "4",
      "5",
      "6",
    ])
  })

  it("reports the page the user has scrolled to", () => {
    const { onVisiblePageChange } = renderBody()

    intersect({ 1: false, 2: true })

    expect(onVisiblePageChange).toHaveBeenLastCalledWith(2)
  })

  it("names the topmost page while two are on screen at a boundary", () => {
    const { onVisiblePageChange } = renderBody()

    intersect({ 2: true, 3: true })

    expect(onVisiblePageChange).toHaveBeenLastCalledWith(2)
  })

  it("keeps a single page of rows in one group", () => {
    renderBody({ items: [{ id: "only" }], limit: 20 })

    const bodies = document.querySelectorAll("tbody")
    expect(bodies).toHaveLength(1)
    expect(bodies[0].dataset.page).toBe("1")
  })
})
