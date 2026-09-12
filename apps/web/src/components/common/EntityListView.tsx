import { Fragment, type ReactNode } from "react"

import { ErrorState } from "@/components/common/ErrorState"
import { TableSkeleton } from "@/components/common/PageSkeletons"
import { SortHeader, type SortState } from "@/components/common/SortHeader"
import { ROW_BORDER, STICKY_TABLE_HEAD } from "@/components/common/tableStyles"
import { Checkbox } from "@/components/ui/checkbox"
import { Pagination } from "@/components/ui/pagination"
import { Table, TableBody, TableHead, TableHeader, TableRow } from "@/components/ui/table"

export interface ListColumn {
  /** Column header content. */
  header: ReactNode
  /** When set, the header is a sortable `SortHeader` for this field. */
  sortField?: string
  /** Extra classes for the `<TableHead>`. */
  className?: string
}

export interface EntityListViewProps<T> {
  columns: ListColumn[]
  items: T[]
  rowKey: (row: T) => string
  /** Returns a `<TableRow>` for a row, including its leading checkbox and trailing actions cells. */
  renderRow: (row: T) => ReactNode
  loading: boolean
  error: string | null
  onRetry: () => void
  /** Rendered when there are no items and no error. */
  empty: ReactNode
  sort: SortState
  onToggleSort: (field: string) => void
  page: number
  total: number
  limit: number
  onPageChange: (page: number) => void
  /** Rendered above the table when there are rows. Used for the selection bar. */
  toolbar?: ReactNode
  /** Leading select-all column. Pass the selection state with it, or rows cannot be selected. */
  selectable?: boolean
  selectAllState?: boolean | "indeterminate"
  onToggleSelectAll?: () => void
  /** Trailing actions column header. Default true. */
  actions?: boolean
}

/**
 * The list-table shell shared by every entity list route: loading, error, empty,
 * table and pagination, with a sticky header of sortable columns. Row content
 * stays bespoke per entity via `renderRow`.
 *
 * The loading skeleton takes its column count from the same `columns` array as
 * the header, so the two cannot drift. It renders no header text, because the
 * only alternative is inventing labels for columns whose header is an element.
 */
export function EntityListView<T>({
  columns,
  items,
  rowKey,
  renderRow,
  loading,
  error,
  onRetry,
  empty,
  sort,
  onToggleSort,
  page,
  total,
  limit,
  onPageChange,
  toolbar,
  selectable = true,
  selectAllState,
  onToggleSelectAll,
  actions = true,
}: EntityListViewProps<T>) {
  const columnCount = columns.length + (selectable ? 1 : 0) + (actions ? 1 : 0)

  let body: ReactNode
  if (loading) {
    body = (
      <div className="flex-1 overflow-auto p-5">
        <TableSkeleton cols={columnCount} withPagination />
      </div>
    )
  } else if (error) {
    body = <ErrorState message={error} onRetry={onRetry} />
  } else if (items.length === 0) {
    body = empty
  } else {
    body = (
      <>
        {toolbar}
        <div className="relative min-h-0 flex-1 overflow-auto" data-scroll-restoration-id="list">
          <Table className="w-full caption-bottom text-sm" scrollable={false}>
            <TableHeader className={STICKY_TABLE_HEAD}>
              <TableRow className={`hover:bg-transparent ${ROW_BORDER}`}>
                {selectable && (
                  <TableHead className="w-10 px-3">
                    <Checkbox
                      aria-label="Select all"
                      checked={selectAllState ?? false}
                      onCheckedChange={onToggleSelectAll}
                    />
                  </TableHead>
                )}
                {columns.map((col, i) => (
                  <TableHead key={col.sortField ?? i} className={col.className}>
                    {col.sortField ? (
                      <SortHeader field={col.sortField} sort={sort} onToggle={onToggleSort}>
                        {col.header}
                      </SortHeader>
                    ) : (
                      col.header
                    )}
                  </TableHead>
                ))}
                {actions && (
                  <TableHead className="w-16 text-right text-fg/65">
                    <span className="sr-only">Actions</span>
                  </TableHead>
                )}
              </TableRow>
            </TableHeader>
            <TableBody>
              {items.map((row) => (
                <Fragment key={rowKey(row)}>{renderRow(row)}</Fragment>
              ))}
            </TableBody>
          </Table>
        </div>
        {total > 0 && (
          <div className="shrink-0 border-t border-fg/10 bg-surface px-3 py-2">
            <Pagination page={page} total={total} limit={limit} onPageChange={onPageChange} />
          </div>
        )}
      </>
    )
  }

  return <div className="flex min-h-0 flex-1 flex-col bg-bg">{body}</div>
}
