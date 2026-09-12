import { Fragment, type ReactNode, useCallback, useEffect, useMemo, useRef } from "react"

import { TableBody } from "@/components/ui/table"

interface PagedTableBodyProps<T> {
  items: T[]
  /** The page `items[0]` came from. Rows after it are the pages that follow. */
  anchorPage: number
  /** Rows per page, which is what splits the flat list back into its pages. */
  limit: number
  rowKey: (row: T) => string
  renderRow: (row: T) => ReactNode
  /** Called with the topmost page on screen, whenever that changes. */
  onVisiblePageChange?: (page: number) => void
}

/**
 * Table rows grouped into the pages they were fetched as.
 *
 * One `<tbody>` per page, which HTML allows and which gives each page an
 * element to watch. Scrolling into a page reports it, so the pagination
 * controls can say which page the user is reading rather than which one the
 * list happened to start at.
 *
 * The topmost intersecting page wins. At a boundary two pages are both on
 * screen, and the one the user has scrolled to the top is the one they have
 * arrived at.
 */
export function PagedTableBody<T>({
  items,
  anchorPage,
  limit,
  rowKey,
  renderRow,
  onVisiblePageChange,
}: PagedTableBodyProps<T>) {
  const groups = useMemo(() => {
    if (limit <= 0) return [{ page: anchorPage, rows: items }]
    const out: { page: number; rows: T[] }[] = []
    for (let i = 0; i < items.length; i += limit) {
      out.push({ page: anchorPage + out.length, rows: items.slice(i, i + limit) })
    }
    return out.length > 0 ? out : [{ page: anchorPage, rows: [] }]
  }, [items, anchorPage, limit])

  const report = useRef(onVisiblePageChange)
  useEffect(() => {
    report.current = onVisiblePageChange
  }, [onVisiblePageChange])

  const visible = useRef(new Set<number>())
  const observer = useRef<IntersectionObserver | null>(null)

  // Built on first attach rather than in an effect. Ref callbacks run during
  // the commit, before passive effects, so an effect-built observer would not
  // exist yet when the first groups ask to be observed.
  const getObserver = useCallback(() => {
    if (!observer.current && typeof IntersectionObserver !== "undefined") {
      observer.current = new IntersectionObserver((entries) => {
        for (const entry of entries) {
          const page = Number((entry.target as HTMLElement).dataset.page)
          if (!Number.isFinite(page)) continue
          if (entry.isIntersecting) visible.current.add(page)
          else visible.current.delete(page)
        }
        if (visible.current.size > 0) report.current?.(Math.min(...visible.current))
      })
    }
    return observer.current
  }, [])

  useEffect(
    () => () => {
      observer.current?.disconnect()
      observer.current = null
      visible.current.clear()
    },
    [],
  )

  // A cleanup-returning ref callback, so this stays stable across renders and
  // does not re-observe every group on each one.
  const attach = useCallback(
    (node: HTMLTableSectionElement) => {
      const io = getObserver()
      io?.observe(node)
      return () => {
        io?.unobserve(node)
        visible.current.delete(Number(node.dataset.page))
      }
    },
    [getObserver],
  )

  return (
    <>
      {groups.map((group) => (
        <TableBody key={group.page} ref={attach} data-page={group.page}>
          {group.rows.map((row) => (
            <Fragment key={rowKey(row)}>{renderRow(row)}</Fragment>
          ))}
        </TableBody>
      ))}
    </>
  )
}
