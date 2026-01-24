/**
 * Table Filters Component
 * Provides search and filter controls for data tables
 */

import { Search, X, Plus } from 'lucide-react'
import { useState } from 'react'

export interface FilterOption {
  value: string
  label: string
}

export interface CustomFilter {
  id: string
  label: string
  value: string
  options: FilterOption[]
  onChange: (value: string) => void
}

export interface CreateAction {
  onClick: () => void
  label: string
}

export interface TableFiltersProps {
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
  className?: string
}

export function TableFilters({
  searchValue = '',
  onSearchChange,
  searchPlaceholder = 'Search...',
  statusFilter,
  dateRangeFilter,
  customFilters = [],
  onClearFilters,
  createAction,
  className = '',
}: TableFiltersProps) {
  const [localSearch, setLocalSearch] = useState(searchValue)

  const handleSearchChange = (value: string) => {
    setLocalSearch(value)
    onSearchChange?.(value)
  }

  const hasActiveFilters =
    localSearch ||
    (statusFilter && statusFilter.value) ||
    (dateRangeFilter && (dateRangeFilter.startDate || dateRangeFilter.endDate)) ||
    (customFilters && customFilters.some(filter => filter.value))

  const handleClear = () => {
    setLocalSearch('')
    onSearchChange?.('')
    statusFilter?.onChange('')
    if (dateRangeFilter) {
      dateRangeFilter.onStartDateChange('')
      dateRangeFilter.onEndDateChange('')
    }
    customFilters.forEach(filter => filter.onChange(''))
    onClearFilters?.()
  }

  return (
    <div className={`flex flex-col sm:flex-row sm:items-center gap-4 flex-wrap ${className}`}>
      {/* Search */}
      {onSearchChange && (
        <div className="flex-1 min-w-[200px] relative">
          <Search
            size={18}
            className="absolute left-3 top-1/2 transform -translate-y-1/2 text-safe-light"
          />
          <input
            type="text"
            value={localSearch}
            onChange={(e) => handleSearchChange(e.target.value)}
            placeholder={searchPlaceholder}
            className="w-full pl-10 pr-4 py-2 bg-calm border border-[0.5px] border-safe text-safe rounded-none focus:outline-none focus:border-natural"
          />
        </div>
      )}

      {/* Status Filter */}
      {statusFilter && (
        <select
          value={statusFilter.value}
          onChange={(e) => statusFilter.onChange(e.target.value)}
          className="px-4 py-2 bg-calm border border-[0.5px] border-safe text-safe rounded-none focus:outline-none focus:border-natural shrink-0"
        >
          <option value="">All Statuses</option>
          {statusFilter.options.map((option) => (
            <option key={option.value} value={option.value}>
              {option.label}
            </option>
          ))}
        </select>
      )}

      {/* Date Range Filter */}
      {dateRangeFilter && (
        <div className="flex gap-2 shrink-0">
          <input
            type="date"
            value={dateRangeFilter.startDate || ''}
            onChange={(e) => dateRangeFilter.onStartDateChange(e.target.value)}
            className="px-4 py-2 bg-calm border border-[0.5px] border-safe text-safe rounded-none focus:outline-none focus:border-natural"
            placeholder="Start date"
          />
          <input
            type="date"
            value={dateRangeFilter.endDate || ''}
            onChange={(e) => dateRangeFilter.onEndDateChange(e.target.value)}
            className="px-4 py-2 bg-calm border border-[0.5px] border-safe text-safe rounded-none focus:outline-none focus:border-natural"
            placeholder="End date"
          />
        </div>
      )}

      {/* Custom Filters */}
      {customFilters.map((filter) => (
        <div key={filter.id} className="flex items-center gap-2 shrink-0">
          <label htmlFor={filter.id} className="text-sm text-safe whitespace-nowrap">
            {filter.label}:
          </label>
          <select
            id={filter.id}
            value={filter.value}
            onChange={(e) => filter.onChange(e.target.value)}
            className="px-4 py-2 bg-calm border border-[0.5px] border-safe text-safe rounded-none focus:outline-none focus:border-natural"
          >
            {filter.options.map((option) => (
              <option key={option.value} value={option.value}>
                {option.label}
              </option>
            ))}
          </select>
        </div>
      ))}

      {/* Clear Filters Button */}
      {hasActiveFilters && onClearFilters && (
        <button
          onClick={handleClear}
          className="flex items-center gap-2 px-4 py-2 bg-safe hover:bg-safe-dark text-white rounded-none transition-colors shrink-0"
        >
          <X size={16} />
          <span>Clear</span>
        </button>
      )}

      {/* Create Action (icon-only, tooltip on hover) */}
      {createAction && (
        <button
          type="button"
          onClick={createAction.onClick}
          title={createAction.label}
          aria-label={createAction.label}
          className="p-2 bg-natural hover:bg-natural-dark text-white rounded-none transition-colors shrink-0"
        >
          <Plus size={18} />
        </button>
      )}
    </div>
  )
}
