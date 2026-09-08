import { readdirSync, readFileSync } from "node:fs"
import { join } from "node:path"

import { render } from "@testing-library/react"
import { describe, expect, it } from "vitest"

import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"

function renderTable(scrollable?: boolean) {
  return render(
    <div data-testid="scroll-area" className="overflow-auto">
      <Table scrollable={scrollable}>
        <TableHeader className="sticky top-0">
          <TableRow>
            <TableHead>Name</TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow>
            <TableCell>Row</TableCell>
          </TableRow>
        </TableBody>
      </Table>
    </div>,
  )
}

/**
 * `position: sticky` resolves against the nearest scrolling ancestor. Table
 * used to always wrap itself in an `overflow-auto` div, so on a list page the
 * nearest ancestor was that wrapper rather than the page's scroll area. The
 * wrapper is never height-constrained, so it never scrolls, and a sticky
 * header inside it rode up with the rows. Every list page carried the sticky
 * class and none of them worked.
 */
describe("Table scroll container", () => {
  it("keeps its own wrapper by default, for a table in a card or dialog", () => {
    const { getByTestId, container } = renderTable()
    const table = container.querySelector("table")!
    expect(table.parentElement).not.toBe(getByTestId("scroll-area"))
    expect(table.parentElement!.className).toContain("overflow-auto")
  })

  it("puts the table straight into the caller's scroll area when asked", () => {
    const { getByTestId, container } = renderTable(false)
    const table = container.querySelector("table")!
    expect(table.parentElement).toBe(getByTestId("scroll-area"))
  })

  it("leaves nothing that scrolls between a sticky header and the scroll area", () => {
    const { getByTestId, container } = renderTable(false)
    const thead = container.querySelector("thead")!
    const area = getByTestId("scroll-area")
    for (let node = thead.parentElement; node && node !== area; node = node.parentElement) {
      expect(
        node.className,
        `${node.tagName} scrolls between thead and the scroll area`,
      ).not.toMatch(/overflow-(auto|scroll)/)
    }
  })
})

/**
 * The prop and the class have to travel together. A sticky header without
 * `scrollable={false}` is inert, and it fails silently, which is how this
 * regressed unnoticed across a dozen pages.
 */
describe("sticky headers are paired with the prop that makes them work", () => {
  const root = join(process.cwd(), "src")

  function tsxFiles(dir: string): string[] {
    return readdirSync(dir, { withFileTypes: true }).flatMap((entry) => {
      const path = join(dir, entry.name)
      if (entry.isDirectory()) return tsxFiles(path)
      // Skip tests: this file names the pattern it is checking for.
      const isTest = entry.name.endsWith(".test.tsx")
      return entry.name.endsWith(".tsx") && !isTest ? [path] : []
    })
  }

  it("every table with a sticky header hands scrolling to its caller", () => {
    const offenders: string[] = []
    for (const file of tsxFiles(root)) {
      const source = readFileSync(file, "utf8")
      if (!source.includes("STICKY_TABLE_HEAD")) continue
      for (const tag of source.match(/<Table\b[^>]*>/g) ?? []) {
        if (!tag.includes("scrollable={false}")) {
          offenders.push(`${file.slice(root.length + 1)}: ${tag}`)
        }
      }
    }
    expect(offenders).toEqual([])
  })
})
