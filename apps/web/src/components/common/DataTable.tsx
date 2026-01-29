/**
 * DataTable Component
 * Powerful, reusable data table with pagination, sorting, and filtering
 */

import { useState, useMemo, useCallback, memo } from 'react'
import { ArrowUpDown, ArrowUp, ArrowDown, AlertCircle, RefreshCw } from 'lucide-react'
import { Pagination } from './Pagination'
import { TableFilters, type FilterOption, type CustomFilter, type CreateAction } from './TableFilters'
import { StatusBadge } from './StatusBadge'
import { TableRowSkeleton } from './LoadingSkeleton'
import type { PaginatedResponse } from '@/types/api'

export type SortDirection = 'asc' | 'desc' | null

export interface Column<T> {
  id: string
  header: string
  accessor?: keyof T | ((row: T) => React.ReactNode)
  sortable?: boolean
  render?: (value: unknown, row: T) => React.ReactNode
  className?: string
  headerClassName?: string
}

export interface DataTableProps<T> {
  data: T[]
  columns: Column<T>[]
  loading?: boolean
  error?: string | null
  onRetry?: () => void
  pagination?: {
    currentPage: number
    pageSize: number
    totalItems: number
    onPageChange: (page: number) => void
    onPageSizeChange: (size: number) => void
  }
  sorting?: {
    sortBy: string | null
    sortDirection: SortDirection
    onSort: (columnId: string) => void
  }
  filters?: {
    searchValue?: string
    onSearchChange?: (value: string) => void
    searchPlaceholder?: string
    statusFilter?: {
      value: string
      options: FilterOption[]
      onChange: (value: string) => void
    }
    dateRangeFilter?: {
      startDate?: string
      endDate?: string
      onStartDateChange: (date: string) => void
      onEndDateChange: (date: string) => void
    }
    customFilters?: CustomFilter[]
    onClearFilters?: () => void
    createAction?: CreateAction
  }
  rowSelection?: {
    selectedRows: Set<string>
    onSelectionChange: (selected: Set<string>) => void
    getRowId: (row: T) => string
  }
  emptyMessage?: string
  className?: string
}

export function DataTable<T extends { id?: string }>({
  data,
  columns,
  loading = false,
  error = null,
  onRetry,
  pagination,
  sorting,
  filters,
  rowSelection,
  emptyMessage = 'No data available',
  className = '',
}: DataTableProps<T>) {
  const [selectedRows, setSelectedRows] = useState<Set<string>>(
    rowSelection?.selectedRows || new Set()
  )

  // Handle row selection
  const handleSelectAll = useCallback(
    (checked: boolean) => {
      if (!rowSelection) return

      const newSelection = checked
        ? new Set(data.map((row) => rowSelection.getRowId(row)))
        : new Set<string>()

      setSelectedRows(newSelection)
      rowSelection.onSelectionChange(newSelection)
    },
    [rowSelection, data]
  )

  const handleSelectRow = useCallback(
    (rowId: string, checked: boolean) => {
      if (!rowSelection) return

      const newSelection = new Set(selectedRows)
      if (checked) {
        newSelection.add(rowId)
      } else {
        newSelection.delete(rowId)
      }

      setSelectedRows(newSelection)
      rowSelection.onSelectionChange(newSelection)
    },
    [rowSelection, selectedRows]
  )

  const isAllSelected =
    rowSelection && data.length > 0 && selectedRows.size === data.length
  const isIndeterminate =
    rowSelection && selectedRows.size > 0 && selectedRows.size < data.length

  // Render cell content
  const renderCell = useCallback(
    (column: Column<T>, row: T) => {
      if (column.render) {
        const value = column.accessor
          ? typeof column.accessor === 'function'
            ? column.accessor(row)
            : row[column.accessor]
          : undefined
        return column.render(value, row)
      }

      if (column.accessor) {
        if (typeof column.accessor === 'function') {
          return column.accessor(row)
        }
        return row[column.accessor] as React.ReactNode
      }

      return null
    },
    []
  )

  // Get sort icon
  const getSortIcon = useCallback(
    (columnId: string) => {
      if (!sorting || columnId !== sorting.sortBy) {
        return <ArrowUpDown size={14} className="text-safe-light" />
      }

      if (sorting.sortDirection === 'asc') {
        return <ArrowUp size={14} className="text-natural" />
      }

      if (sorting.sortDirection === 'desc') {
        return <ArrowDown size={14} className="text-natural" />
      }

      return <ArrowUpDown size={14} className="text-safe-light" />
    },
    [sorting]
  )

  // Memoize skeleton rows
  const skeletonRows = useMemo(
    () =>
      Array.from({ length: pagination?.pageSize || 10 }).map((_, i) => (
        <TableRowSkeleton key={`skeleton-${i}`} columns={columns.length + (rowSelection ? 1 : 0)} />
      )),
    [columns.length, rowSelection, pagination?.pageSize]
  )

  return (
    <div className={`flex flex-col gap-4 ${className}`}>
      {/* Filters */}
      {filters && (
        <TableFilters
          searchValue={filters.searchValue}
          onSearchChange={filters.onSearchChange}
          searchPlaceholder={filters.searchPlaceholder}
          statusFilter={filters.statusFilter}
          dateRangeFilter={filters.dateRangeFilter}
          customFilters={filters.customFilters}
          onClearFilters={filters.onClearFilters}
          createAction={filters.createAction}
        />
      )}

      {/* Desktop Table View */}
      <div className="hidden md:block overflow-x-auto">
        <table className="w-full border-collapse bg-white">
          <thead>
            <tr className="bg-white border-b border-[0.5px] border-safe/30">
              {rowSelection && (
                <th className="px-4 py-3 text-left">
                  <input
                    type="checkbox"
                    checked={isAllSelected}
                    ref={(input) => {
                      if (input) input.indeterminate = isIndeterminate || false
                    }}
                    onChange={(e) => handleSelectAll(e.target.checked)}
                    className="rounded-none border-[0.5px] border-safe/30"
                  />
                </th>
              )}
              {columns.map((column) => (
                <th
                  key={column.id}
                  className={`px-4 py-3 text-left text-sm font-semibold text-safe ${column.headerClassName || ''}`}
                >
                  <div className="flex items-center gap-2">
                    {sorting && column.sortable !== false ? (
                      <button
                        onClick={() => sorting.onSort(column.id)}
                        className="flex items-center gap-2 hover:text-natural transition-colors"
                      >
                        <span>{column.header}</span>
                        {getSortIcon(column.id)}
                      </button>
                    ) : (
                      <span>{column.header}</span>
                    )}
                  </div>
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {loading ? (
              skeletonRows
            ) : error ? (
              <tr>
                <td
                  colSpan={columns.length + (rowSelection ? 1 : 0)}
                  className="px-4 py-12 bg-white"
                >
                  <div className="flex flex-col items-center justify-center gap-3">
                    <div className="flex items-center gap-2 text-danger">
                      <AlertCircle size={20} />
                      <span className="font-medium">Error loading data</span>
                    </div>
                    <p className="text-safe-light text-sm text-center max-w-md">{error}</p>
                    {onRetry && (
                      <button
                        onClick={onRetry}
                        className="mt-2 px-4 py-2 bg-natural hover:bg-natural-dark text-white text-sm font-medium rounded-none transition-colors flex items-center gap-2"
                      >
                        <RefreshCw size={16} />
                        Retry
                      </button>
                    )}
                  </div>
                </td>
              </tr>
            ) : data.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length + (rowSelection ? 1 : 0)}
                  className="px-4 py-12 text-center text-safe-light bg-white"
                >
                  {emptyMessage}
                </td>
              </tr>
            ) : (
              data.map((row, rowIndex) => {
                const rowId = rowSelection?.getRowId(row) || row.id || `row-${rowIndex}`
                const isSelected = selectedRows.has(rowId)

                return (
                  <tr
                    key={rowId}
                    className={`border-b border-[0.5px] border-safe/30 ${
                      isSelected ? 'bg-gray-100' : 'bg-white hover:bg-gray-50'
                    } transition-colors`}
                  >
                    {rowSelection && (
                      <td className="px-4 py-3">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={(e) => handleSelectRow(rowId, e.target.checked)}
                          className="rounded-none border-[0.5px] border-safe/30"
                        />
                      </td>
                    )}
                    {columns.map((column) => (
                      <td
                        key={column.id}
                        className={`px-4 py-3 text-sm text-safe ${column.className || ''}`}
                      >
                        {renderCell(column, row)}
                      </td>
                    ))}
                  </tr>
                )
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Mobile Card View */}
      <div className="md:hidden space-y-4">
        {loading ? (
          <div className="space-y-4">
            {Array.from({ length: pagination?.pageSize || 5 }).map((_, i) => (
              <div key={`skeleton-${i}`} className="bg-white border border-[0.5px] border-safe/30 p-4">
                <div className="space-y-2">
                  {columns.map((col) => (
                    <div key={col.id} className="space-y-1">
                      <div className="h-3 w-20 bg-safe-light animate-pulse" />
                      <div className="h-4 w-full bg-safe-light animate-pulse" />
                    </div>
                  ))}
                </div>
              </div>
            ))}
          </div>
        ) : error ? (
          <div className="p-12 bg-white border border-[0.5px] border-danger">
            <div className="flex flex-col items-center justify-center gap-3">
              <div className="flex items-center gap-2 text-danger">
                <AlertCircle size={20} />
                <span className="font-medium">Error loading data</span>
              </div>
              <p className="text-safe-light text-sm text-center max-w-md">{error}</p>
              {onRetry && (
                <button
                  onClick={onRetry}
                  className="mt-2 px-4 py-2 bg-natural hover:bg-natural-dark text-white text-sm font-medium rounded-none transition-colors flex items-center gap-2"
                >
                  <RefreshCw size={16} />
                  Retry
                </button>
              )}
            </div>
          </div>
        ) : data.length === 0 ? (
          <div className="p-12 text-center text-safe-light bg-white border border-[0.5px] border-safe/30">
            {emptyMessage}
          </div>
        ) : (
          data.map((row, rowIndex) => {
            const rowId = rowSelection?.getRowId(row) || row.id || `row-${rowIndex}`
            const isSelected = selectedRows.has(rowId)

            return (
              <div
                key={rowId}
                className={`bg-white border border-[0.5px] border-safe/30 p-4 ${
                  isSelected ? 'bg-gray-100' : ''
                }`}
              >
                {rowSelection && (
                  <div className="mb-3">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={(e) => handleSelectRow(rowId, e.target.checked)}
                      className="rounded-none border-[0.5px] border-safe/30"
                    />
                  </div>
                )}
                <div className="space-y-2">
                  {columns.map((column) => (
                    <div key={column.id} className="flex flex-col">
                      <span className="text-xs font-semibold text-safe-light mb-1">
                        {column.header}
                      </span>
                      <span className="text-sm text-safe">{renderCell(column, row)}</span>
                    </div>
                  ))}
                </div>
              </div>
            )
          })
        )}
      </div>

      {/* Pagination */}
      {pagination && (
        <Pagination
          currentPage={pagination.currentPage}
          totalPages={Math.ceil(pagination.totalItems / pagination.pageSize)}
          pageSize={pagination.pageSize}
          totalItems={pagination.totalItems}
          onPageChange={pagination.onPageChange}
          onPageSizeChange={pagination.onPageSizeChange}
        />
      )}
    </div>
  )
}
