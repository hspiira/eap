/**
 * The "1–20 of 340" counter has to describe what is actually on screen.
 *
 * Scrolling appends pages without moving the anchor, so the count of rows
 * shown exceeds one page's worth while the page number stays where the user
 * is reading. A counter still derived from `page * limit` would under-report
 * every list the user had scrolled through.
 */

import { render, screen } from "@testing-library/react"
import { describe, expect, it, vi } from "vitest"

import { Pagination } from "@/components/ui/pagination"

function renderBar(props: Partial<React.ComponentProps<typeof Pagination>> = {}) {
  render(<Pagination page={1} total={340} limit={20} onPageChange={vi.fn()} {...props} />)
}

describe("Pagination", () => {
  it("counts one page when nothing has been appended", () => {
    renderBar()

    expect(screen.getByText("1–20 of 340")).toBeInTheDocument()
  })

  it("counts every row on screen once scrolling has appended pages", () => {
    renderBar({ shownCount: 60 })

    expect(screen.getByText("1–60 of 340")).toBeInTheDocument()
  })

  it("counts from the anchor when the list started part way in", () => {
    renderBar({ page: 3, shownCount: 40 })

    expect(screen.getByText("41–80 of 340")).toBeInTheDocument()
  })

  it("never runs past the total", () => {
    renderBar({ page: 1, total: 25, shownCount: 40 })

    expect(screen.getByText("1–25 of 25")).toBeInTheDocument()
  })

  it("says so when there is nothing to count", () => {
    renderBar({ total: 0, shownCount: 0 })

    expect(screen.getByText("0 items")).toBeInTheDocument()
  })
})
