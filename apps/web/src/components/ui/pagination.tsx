import { ChevronLeft, ChevronRight } from "lucide-react"
import { cn } from "@/lib/utils"
import { Button } from "@/components/ui/button"

export interface PaginationProps {
  page: number
  total: number
  limit: number
  onPageChange: (page: number) => void
  className?: string
}

function getPageNumbers(current: number, totalPages: number): (number | 'ellipsis')[] {
  if (totalPages <= 7) {
    return Array.from({ length: totalPages }, (_, i) => i + 1)
  }
  const pages: (number | 'ellipsis')[] = []
  if (current <= 4) {
    for (let i = 1; i <= 5; i++) pages.push(i)
    pages.push('ellipsis')
    pages.push(totalPages)
  } else if (current >= totalPages - 3) {
    pages.push(1)
    pages.push('ellipsis')
    for (let i = totalPages - 4; i <= totalPages; i++) pages.push(i)
  } else {
    pages.push(1)
    pages.push('ellipsis')
    for (let i = current - 1; i <= current + 1; i++) pages.push(i)
    pages.push('ellipsis')
    pages.push(totalPages)
  }
  return pages
}

export function Pagination({
  page,
  total,
  limit,
  onPageChange,
  className,
}: PaginationProps) {
  const totalPages = Math.max(1, Math.ceil(total / limit))
  const pages = getPageNumbers(page, totalPages)
  const from = total === 0 ? 0 : (page - 1) * limit + 1
  const to = Math.min(page * limit, total)

  return (
    <div
      className={cn(
        "flex flex-col sm:flex-row items-center justify-between gap-2",
        className
      )}
    >
      <p className="text-sm text-[#5A626A]">
        {total === 0 ? "0 items" : `${from}–${to} of ${total}`}
      </p>
      <nav className="flex items-center gap-1" aria-label="Pagination">
        <Button
          variant="secondary"
          size="sm"
          className="rounded-none"
          onClick={() => onPageChange(page - 1)}
          disabled={page <= 1}
          aria-label="Previous page"
        >
          <ChevronLeft className="h-4 w-4" />
        </Button>
        <div className="flex items-center gap-1">
          {pages.map((p, i) =>
            p === 'ellipsis' ? (
              <span key={`e-${i}`} className="px-2 text-[#5A626A]">
                …
              </span>
            ) : (
              <Button
                key={p}
                variant={p === page ? "default" : "secondary"}
                size="sm"
                className="min-w-8 rounded-none"
                onClick={() => onPageChange(p)}
                aria-label={`Page ${p}`}
                aria-current={p === page ? "page" : undefined}
              >
                {p}
              </Button>
            )
          )}
        </div>
        <Button
          variant="secondary"
          size="sm"
          className="rounded-none"
          onClick={() => onPageChange(page + 1)}
          disabled={page >= totalPages}
          aria-label="Next page"
        >
          <ChevronRight className="h-4 w-4" />
        </Button>
      </nav>
    </div>
  )
}
