/**
 * Pagination Component
 * Handles page navigation and items per page selection
 */

import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react'

export type PaginationInfoPosition = 'above' | 'below' | 'inline'

export interface PaginationProps {
  currentPage: number
  totalPages: number
  pageSize: number
  totalItems: number
  onPageChange: (page: number) => void
  onPageSizeChange: (size: number) => void
  pageSizeOptions?: number[]
  showPageSizeSelector?: boolean
  /** Where to show "Showing X to Y of Z": above nav, below nav, or inline (default). */
  infoPosition?: PaginationInfoPosition
  className?: string
}

const defaultPageSizeOptions = [10, 25, 50, 100]

export function Pagination({
  currentPage,
  totalPages,
  pageSize,
  totalItems,
  onPageChange,
  onPageSizeChange,
  pageSizeOptions = defaultPageSizeOptions,
  showPageSizeSelector = true,
  infoPosition = 'inline',
  className = '',
}: PaginationProps) {
  const startItem = totalItems === 0 ? 0 : (currentPage - 1) * pageSize + 1
  const endItem = Math.min(currentPage * pageSize, totalItems)

  const handleFirstPage = () => {
    if (currentPage > 1) {
      onPageChange(1)
    }
  }

  const handlePreviousPage = () => {
    if (currentPage > 1) {
      onPageChange(currentPage - 1)
    }
  }

  const handleNextPage = () => {
    if (currentPage < totalPages) {
      onPageChange(currentPage + 1)
    }
  }

  const handleLastPage = () => {
    if (currentPage < totalPages) {
      onPageChange(totalPages)
    }
  }

  if (totalPages === 0) {
    return null
  }

  // Generate page numbers: show all only when ≤5 pages; otherwise first, last, current only, ellipsis.
  // Compact (window 0) keeps strip narrow so it fits in small areas.
  const getPageNumbers = (): (number | string)[] => {
    if (totalPages <= 5) {
      return Array.from({ length: totalPages }, (_, i) => i + 1)
    }

    const windowSize = 0
    const left = Math.max(2, currentPage - windowSize)
    const right = Math.min(totalPages - 1, currentPage + windowSize)
    const numbers = new Set<number>([1, totalPages])
    for (let i = left; i <= right; i++) numbers.add(i)
    const sorted = [...numbers].sort((a, b) => a - b)

    const pages: (number | string)[] = []
    let prev = 0
    for (const n of sorted) {
      if (prev !== 0 && n > prev + 1) pages.push('...')
      pages.push(n)
      prev = n
    }
    return pages
  }

  const infoBlock = (
    <div className="flex flex-wrap items-center justify-center sm:justify-start gap-2 sm:gap-4 min-w-0">
      <span className="text-sm text-text">
        Showing {startItem} to {endItem} of {totalItems}
      </span>
      {showPageSizeSelector && (
        <div className="flex items-center gap-2">
          <label htmlFor="page-size" className="text-sm text-text">
            Items per page:
          </label>
          <select
            id="page-size"
            value={pageSize}
            onChange={(e) => onPageSizeChange(Number(e.target.value))}
            className="px-2 py-1 bg-surface border border-[0.5px] border-border text-text text-sm rounded-none focus:outline-none focus:border-border-focus"
          >
            {pageSizeOptions.map((size) => (
              <option key={size} value={size}>
                {size}
              </option>
            ))}
          </select>
        </div>
      )}
    </div>
  )

  const navBlock = (
    <div className="flex flex-nowrap items-center justify-center gap-0.5 min-w-0 overflow-x-auto max-w-full">
      <button
        onClick={handleFirstPage}
        disabled={currentPage === 1}
        className="p-1 border border-[0.5px] border-border text-text disabled:opacity-50 disabled:cursor-not-allowed hover:bg-surface-hover transition-colors rounded-none shrink-0"
        aria-label="First page"
      >
        <ChevronsLeft size={12} />
      </button>
      <button
        onClick={handlePreviousPage}
        disabled={currentPage === 1}
        className="p-1 border border-[0.5px] border-border text-text disabled:opacity-50 disabled:cursor-not-allowed hover:bg-surface-hover transition-colors rounded-none shrink-0"
        aria-label="Previous page"
      >
        <ChevronLeft size={12} />
      </button>

      <div className="flex flex-nowrap items-center gap-0.5 min-w-0 shrink">
        {getPageNumbers().map((page, index) => {
          if (page === '...') {
            return (
              <span key={`ellipsis-${index}`} className="px-0.5 text-text text-xs shrink-0">
                …
              </span>
            )
          }

          const pageNum = page as number
          const isActive = pageNum === currentPage

          return (
            <button
              key={pageNum}
              onClick={() => onPageChange(pageNum)}
              className={`min-w-[1.25rem] w-5 h-5 flex items-center justify-center border border-[0.5px] text-xs font-medium transition-colors rounded-none shrink-0 ${
                isActive
? 'bg-primary text-white border-primary-hover'
                    : 'bg-surface text-text border-border hover:bg-surface-hover'
              }`}
            >
              {pageNum}
            </button>
          )
        })}
      </div>

      <button
        onClick={handleNextPage}
        disabled={currentPage === totalPages}
        className="p-1 border border-[0.5px] border-border text-text disabled:opacity-50 disabled:cursor-not-allowed hover:bg-surface-hover transition-colors rounded-none shrink-0"
        aria-label="Next page"
      >
        <ChevronRight size={12} />
      </button>
      <button
        onClick={handleLastPage}
        disabled={currentPage === totalPages}
        className="p-1 border border-[0.5px] border-border text-text disabled:opacity-50 disabled:cursor-not-allowed hover:bg-surface-hover transition-colors rounded-none shrink-0"
        aria-label="Last page"
      >
        <ChevronsRight size={12} />
      </button>
    </div>
  )

  if (infoPosition === 'above') {
    return (
      <div className={`flex flex-col items-stretch gap-2 min-w-0 w-full ${className}`}>
        {infoBlock}
        {navBlock}
      </div>
    )
  }

  if (infoPosition === 'below') {
    return (
      <div className={`flex flex-col items-stretch gap-2 min-w-0 w-full ${className}`}>
        {navBlock}
        {infoBlock}
      </div>
    )
  }

  return (
    <div className={`flex flex-col sm:flex-row items-center justify-between gap-4 min-w-0 w-full ${className}`}>
      {infoBlock}
      {navBlock}
    </div>
  )
}
