/**
 * Pagination Component
 * Handles page navigation and items per page selection
 */

import { ChevronLeft, ChevronRight, ChevronsLeft, ChevronsRight } from 'lucide-react'

export interface PaginationProps {
  currentPage: number
  totalPages: number
  pageSize: number
  totalItems: number
  onPageChange: (page: number) => void
  onPageSizeChange: (size: number) => void
  pageSizeOptions?: number[]
  showPageSizeSelector?: boolean
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

  // Generate page numbers to display
  const getPageNumbers = () => {
    const pages: (number | string)[] = []
    const maxVisible = 5

    if (totalPages <= maxVisible) {
      // Show all pages if total is small
      for (let i = 1; i <= totalPages; i++) {
        pages.push(i)
      }
    } else {
      // Always show first page
      pages.push(1)

      if (currentPage > 3) {
        pages.push('...')
      }

      // Show pages around current page
      const start = Math.max(2, currentPage - 1)
      const end = Math.min(totalPages - 1, currentPage + 1)

      for (let i = start; i <= end; i++) {
        if (i !== 1 && i !== totalPages) {
          pages.push(i)
        }
      }

      if (currentPage < totalPages - 2) {
        pages.push('...')
      }

      // Always show last page
      if (totalPages > 1) {
        pages.push(totalPages)
      }
    }

    return pages
  }

  return (
    <div className={`flex flex-col sm:flex-row items-center justify-between gap-4 ${className}`}>
      {/* Items info and page size selector */}
      <div className="flex items-center gap-4">
        <span className="text-sm text-safe">
          Showing {startItem} to {endItem} of {totalItems}
        </span>
        {showPageSizeSelector && (
          <div className="flex items-center gap-2">
            <label htmlFor="page-size" className="text-sm text-safe">
              Items per page:
            </label>
            <select
              id="page-size"
              value={pageSize}
              onChange={(e) => onPageSizeChange(Number(e.target.value))}
              className="px-2 py-1 bg-calm border border-[0.5px] border-safe text-safe text-sm rounded-none focus:outline-none focus:border-natural"
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

      {/* Page navigation */}
      <div className="flex items-center gap-2">
        <button
          onClick={handleFirstPage}
          disabled={currentPage === 1}
          className="p-2 border border-[0.5px] border-safe text-safe disabled:opacity-50 disabled:cursor-not-allowed hover:bg-calm transition-colors rounded-none"
          aria-label="First page"
        >
          <ChevronsLeft size={16} />
        </button>
        <button
          onClick={handlePreviousPage}
          disabled={currentPage === 1}
          className="p-2 border border-[0.5px] border-safe text-safe disabled:opacity-50 disabled:cursor-not-allowed hover:bg-calm transition-colors rounded-none"
          aria-label="Previous page"
        >
          <ChevronLeft size={16} />
        </button>

        {/* Page numbers */}
        <div className="flex items-center gap-1">
          {getPageNumbers().map((page, index) => {
            if (page === '...') {
              return (
                <span key={`ellipsis-${index}`} className="px-2 text-safe">
                  ...
                </span>
              )
            }

            const pageNum = page as number
            const isActive = pageNum === currentPage

            return (
              <button
                key={pageNum}
                onClick={() => onPageChange(pageNum)}
                className={`px-3 py-1 border border-[0.5px] text-sm font-medium transition-colors rounded-none ${
                  isActive
                    ? 'bg-natural text-white border-natural-dark'
                    : 'bg-calm text-safe border-safe hover:bg-calm-dark'
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
          className="p-2 border border-[0.5px] border-safe text-safe disabled:opacity-50 disabled:cursor-not-allowed hover:bg-calm transition-colors rounded-none"
          aria-label="Next page"
        >
          <ChevronRight size={16} />
        </button>
        <button
          onClick={handleLastPage}
          disabled={currentPage === totalPages}
          className="p-2 border border-[0.5px] border-safe text-safe disabled:opacity-50 disabled:cursor-not-allowed hover:bg-calm transition-colors rounded-none"
          aria-label="Last page"
        >
          <ChevronsRight size={16} />
        </button>
      </div>
    </div>
  )
}
