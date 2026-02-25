import * as React from "react"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { Pagination } from "@/components/ui/pagination"
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
}: DataTableProps<T>) {
  const showPagination =
    typeof onPageChange === "function" && total > 0 && limit > 0

  return (
    <div className={cn("space-y-4", className)}>
      <div className="rounded-none border border-[#5A626A]/30">
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
                  className="text-center text-[#5A626A] py-8"
                >
                  {error}
                </TableCell>
              </TableRow>
            ) : loading ? (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="text-center text-[#5A626A] py-8"
                >
                  Loading…
                </TableCell>
              </TableRow>
            ) : data.length === 0 ? (
              <TableRow>
                <TableCell
                  colSpan={columns.length}
                  className="text-center text-[#5A626A] py-8"
                >
                  {emptyMessage}
                </TableCell>
              </TableRow>
            ) : (
              data.map((row, rowIndex) => (
                <TableRow key={rowIndex}>
                  {columns.map((col) => (
                    <TableCell key={col.id}>
                      {col.cell
                        ? col.cell(row)
                        : String(getCellValue(row, col.accessorKey) ?? "")}
                    </TableCell>
                  ))}
                </TableRow>
              ))
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
