/**
 * Table Filters Component
 * Provides search and filter controls for data tables
 */

import { Search, X } from 'lucide-react'
import { useState } from 'react'

export interface FilterOption {
  value: string
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
  onClearFilters?: () => void
  className?: string
}

export function TableFilters({
  searchValue = '',
  onSearchChange,
  searchPlaceholder = 'Search...',
  statusFilter,
  dateRangeFilter,
  onClearFilters,
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
    (dateRangeFilter && (dateRangeFilter.startDate || dateRangeFilter.endDate))

  const handleClear = () => {
    setLocalSearch('')
    onSearchChange?.('')
    statusFilter?.onChange('')
    if (dateRangeFilter) {
      dateRangeFilter.onStartDateChange('')
      dateRangeFilter.onEndDateChange('')
    }
    onClearFilters?.()
  }

  return (
    <div className={`flex flex-col sm:flex-row gap-4 ${className}`}>
      {/* Search */}
      {onSearchChange && (
        <div className="flex-1 relative">
          <Search
            size={18}
            className="absolute left-3 top-1/2 transform -translate-y-1/2 text-safe-light"
          />
          <input
            type="text"
            value={localSearch}
            onChange={(e) => handleSearchChange(e.target.value)}
            placeholder={searchPlaceholder}
            className="w-full pl-10 pr-4 py-2 bg-white border border-[0.5px] border-safe text-safe rounded-none focus:outline-none focus:border-natural"
          />
        </div>
      )}

      {/* Status Filter */}
      {statusFilter && (
        <select
          value={statusFilter.value}
          onChange={(e) => statusFilter.onChange(e.target.value)}
          className="px-4 py-2 bg-white border border-[0.5px] border-safe text-safe rounded-none focus:outline-none focus:border-natural"
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
        <div className="flex gap-2">
          <input
            type="date"
            value={dateRangeFilter.startDate || ''}
            onChange={(e) => dateRangeFilter.onStartDateChange(e.target.value)}
            className="px-4 py-2 bg-white border border-[0.5px] border-safe text-safe rounded-none focus:outline-none focus:border-natural"
            placeholder="Start date"
          />
          <input
            type="date"
            value={dateRangeFilter.endDate || ''}
            onChange={(e) => dateRangeFilter.onEndDateChange(e.target.value)}
            className="px-4 py-2 bg-white border border-[0.5px] border-safe text-safe rounded-none focus:outline-none focus:border-natural"
            placeholder="End date"
          />
        </div>
      )}

      {/* Clear Filters Button */}
      {hasActiveFilters && onClearFilters && (
        <button
          onClick={handleClear}
          className="flex items-center gap-2 px-4 py-2 bg-safe hover:bg-safe-dark text-white rounded-none transition-colors"
        >
          <X size={16} />
          <span>Clear</span>
        </button>
      )}
    </div>
  )
}
