import { Loader2 } from "lucide-react"

import { useInfiniteScroll } from "@/hooks/useInfiniteScroll"

/**
 * The end of a list that keeps going.
 *
 * Sits after the last row, inside the scrolling pane, and asks for the next
 * page as it comes into view. It renders nothing once the list is complete, so
 * a list that fits on one page looks exactly as it did before.
 */
export function InfiniteScrollSentinel({
  onLoadMore,
  hasMore,
  loadingMore,
}: {
  onLoadMore: () => void
  hasMore: boolean
  loadingMore: boolean
}) {
  const ref = useInfiniteScroll({ onLoadMore, enabled: hasMore && !loadingMore })
  if (!hasMore && !loadingMore) return null
  return (
    <div
      ref={ref}
      role="status"
      aria-live="polite"
      className="flex items-center justify-center gap-2 py-4 text-xs text-fg-muted"
    >
      {loadingMore ? (
        <>
          <Loader2 className="size-3.5 animate-spin" aria-hidden />
          Loading more…
        </>
      ) : (
        <span className="sr-only">More rows load as you scroll</span>
      )}
    </div>
  )
}
