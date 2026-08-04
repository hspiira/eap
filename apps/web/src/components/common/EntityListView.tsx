import type { ReactNode } from "react"

import { ErrorState } from "@/components/common/ErrorState"
import { TableSkeleton } from "@/components/common/PageSkeletons"
import { SortHeader, type SortState } from "@/components/common/SortHeader"
import { ROW_BORDER } from "@/components/common/tableStyles"
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
  /** Returns a `<TableRow>` for a row (including the leading checkbox / trailing actions cells). */
  renderRow: (row: T) => ReactNode
  loading: boolean
  error: string | null
  onRetry: () => void
  /** Empty-state element rendered when there are no items and no error. */
  empty: ReactNode
  sort: SortState
  onToggleSort: (field: string) => void
  page: number
  total: number
  limit: number
  onPageChange: (page: number) => void
  /** Render the leading select-all checkbox column. Default true. */
  selectable?: boolean
  /** Render a trailing actions column header. Default true. */
  actions?: boolean
  /** Skeleton column count while loading. Defaults to the header count. */
  skeletonCols?: number
}

/**
 * The list-table shell shared by every entity list route: loading / error /
 * empty / table / pagination, with a sticky header of sortable columns. Row
 * content stays bespoke per entity via `renderRow`.
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
  selectable = true,
  actions = true,
  skeletonCols,
}: EntityListViewProps<T>) {
  const colCount = columns.length + (selectable ? 1 : 0) + (actions ? 1 : 0)

  return (
    <div className="flex min-h-0 flex-1 flex-col bg-bg">
      {loading ? (
        <div className="flex-1 overflow-auto p-5">
          <TableSkeleton cols={skeletonCols ?? colCount} />
        </div>
      ) : error ? (
        <ErrorState message={error} onRetry={onRetry} />
      ) : items.length === 0 ? (
        empty
      ) : (
        <>
          <div className="relative min-h-0 flex-1 overflow-auto">
            <Table className="w-full caption-bottom text-sm">
              <TableHeader className="sticky top-0 z-10 border-b-0 bg-surface shadow-[inset_0_-1px_0_rgb(0_0_0/0.08)]">
                <TableRow className={`hover:bg-transparent ${ROW_BORDER}`}>
                  {selectable && (
                    <TableHead className="w-10 px-3">
                      <Checkbox aria-label="Select all" />
                    </TableHead>
                  )}
                  {columns.map((col, i) => (
                    <TableHead key={i} className={col.className}>
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
                  <RowSlot key={rowKey(row)}>{renderRow(row)}</RowSlot>
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
      )}
    </div>
  )
}

// Fragment wrapper so renderRow's <TableRow> gets the stable key from rowKey.
function RowSlot({ children }: { children: ReactNode }) {
  return <>{children}</>
}
