/**
 * DataTable Component
 * Powerful, reusable data table with pagination, sorting, and filtering
 */

import { useState, useMemo } from 'react'
import { ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react'
import { Pagination } from './Pagination'
import { TableFilters, type FilterOption } from './TableFilters'
import { StatusBadge } from './StatusBadge'
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
    onClearFilters?: () => void
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
  const handleSelectAll = (checked: boolean) => {
    if (!rowSelection) return

    const newSelection = checked
      ? new Set(data.map((row) => rowSelection.getRowId(row)))
      : new Set<string>()

    setSelectedRows(newSelection)
    rowSelection.onSelectionChange(newSelection)
  }

  const handleSelectRow = (rowId: string, checked: boolean) => {
    if (!rowSelection) return

    const newSelection = new Set(selectedRows)
    if (checked) {
      newSelection.add(rowId)
    } else {
      newSelection.delete(rowId)
    }

    setSelectedRows(newSelection)
    rowSelection.onSelectionChange(newSelection)
  }

  const isAllSelected =
    rowSelection && data.length > 0 && selectedRows.size === data.length
  const isIndeterminate =
    rowSelection && selectedRows.size > 0 && selectedRows.size < data.length

  // Render cell content
  const renderCell = (column: Column<T>, row: T) => {
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
  }

  // Get sort icon
  const getSortIcon = (columnId: string) => {
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
  }

  if (loading) {
    return (
      <div className={`flex items-center justify-center p-12 bg-calm ${className}`}>
        <div className="text-safe">Loading...</div>
      </div>
    )
  }

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
          onClearFilters={filters.onClearFilters}
        />
      )}

      {/* Desktop Table View */}
      <div className="hidden md:block overflow-x-auto">
        <table className="w-full border-collapse bg-calm">
          <thead>
            <tr className="bg-calm border-b border-[0.5px] border-safe">
              {rowSelection && (
                <th className="px-4 py-3 text-left">
                  <input
                    type="checkbox"
                    checked={isAllSelected}
                    ref={(input) => {
                      if (input) input.indeterminate = isIndeterminate || false
                    }}
                    onChange={(e) => handleSelectAll(e.target.checked)}
                    className="rounded-none border-[0.5px] border-safe"
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
            {data.length === 0 ? (
              <tr>
                <td
                  colSpan={columns.length + (rowSelection ? 1 : 0)}
                  className="px-4 py-12 text-center text-safe-light bg-calm"
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
                    className={`border-b border-[0.5px] border-safe ${
                      isSelected ? 'bg-calm-dark' : 'bg-calm hover:bg-calm-dark/50'
                    } transition-colors`}
                  >
                    {rowSelection && (
                      <td className="px-4 py-3">
                        <input
                          type="checkbox"
                          checked={isSelected}
                          onChange={(e) => handleSelectRow(rowId, e.target.checked)}
                          className="rounded-none border-[0.5px] border-safe"
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
        {data.length === 0 ? (
          <div className="p-12 text-center text-safe-light bg-calm border border-[0.5px] border-safe">
            {emptyMessage}
          </div>
        ) : (
          data.map((row, rowIndex) => {
            const rowId = rowSelection?.getRowId(row) || row.id || `row-${rowIndex}`
            const isSelected = selectedRows.has(rowId)

            return (
              <div
                key={rowId}
                className={`bg-calm border border-[0.5px] border-safe p-4 ${
                  isSelected ? 'bg-calm-dark' : ''
                }`}
              >
                {rowSelection && (
                  <div className="mb-3">
                    <input
                      type="checkbox"
                      checked={isSelected}
                      onChange={(e) => handleSelectRow(rowId, e.target.checked)}
                      className="rounded-none border-[0.5px] border-safe"
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
