import * as React from "react"

import { Pagination } from "@/components/ui/pagination"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { cn } from "@/lib/utils"

export interface DataTableColumn<T> {
  id: string
  accessorKey: keyof T | string
  header: string
  cell?: (row: T) => React.ReactNode
}

export interface DataTableProps<T> {
  columns: DataTableColumn<T>[]
  data: T[]
  loading?: boolean
  error?: string | null
  page?: number
  total?: number
  limit?: number
  onPageChange?: (page: number) => void
  emptyMessage?: string
  className?: string
  getRowId?: (row: T) => string | number
  onRowClick?: (row: T) => void
  selectedId?: string | number | null
}

function getCellValue<T>(row: T, accessorKey: keyof T | string): unknown {
  const key = accessorKey as keyof T
  return row[key]
}

export function DataTable<T extends object>({
  columns,
  data,
  loading = false,
  error = null,
  page = 1,
  total = 0,
  limit = 20,
  onPageChange,
  emptyMessage = "No results.",
  className,
  getRowId,
  onRowClick,
  selectedId,
}: DataTableProps<T>) {
  const showPagination =
    typeof onPageChange === "function" && total > 0 && limit > 0

  return (
    <div className={cn("space-y-2", className)}>
      <div className="rounded-none border border-fg/30">
        <Table>
          <TableHeader>
            <TableRow>
              {columns.map((col) => (
                <TableHead key={col.id}>{col.header}</TableHead>
              ))}
            </TableRow>
          </TableHeader>
          <TableBody>
            {error ? (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="text-center text-fg py-4 text-sm"
                >
                  {error}
                </TableCell>
              </TableRow>
            ) : loading ? (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="text-center text-fg py-4 text-sm"
                >
                  Loading…
                </TableCell>
              </TableRow>
            ) : data.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="text-center text-fg py-4 text-sm"
                >
                  {emptyMessage}
                </TableCell>
              </TableRow>
            ) : (
              data.map((row, rowIndex) => {
                const rowId = getRowId ? getRowId(row) : rowIndex
                const isSelected =
                  selectedId !== undefined && selectedId !== null && rowId === selectedId
                return (
                  <TableRow
                    key={getRowId ? rowId : rowIndex}
                    onClick={onRowClick ? () => onRowClick(row) : undefined}
                    className={cn(
                      onRowClick && "cursor-pointer",
                      isSelected && "bg-selection"
                    )}
                  >
                    {columns.map((col) => (
                      <TableCell key={col.id}>
                        {col.cell
                          ? col.cell(row)
                          : String(getCellValue(row, col.accessorKey) ?? "")}
                      </TableCell>
                    ))}
                  </TableRow>
                )
              })
            )}
          </TableBody>
        </Table>
      </div>
      {showPagination && (
        <Pagination
          page={page}
          total={total}
          limit={limit}
          onPageChange={onPageChange}
        />
      )}
    </div>
  )
}
