import { useCallback, useEffect, useRef } from "react"

/**
 * Calls `onLoadMore` once the returned ref's element comes into view.
 *
 * Attach it to a sentinel sitting after the last row. The root is the viewport
 * rather than the scrolling pane: a sentinel inside a pane the user has not
 * scrolled down is clipped, so it does not count as visible either way, and
 * this needs no knowledge of which ancestor scrolls.
 *
 * A callback ref rather than an object ref, because the table unmounts between
 * its loading, empty and populated states; this re-observes whatever element
 * comes back instead of holding a reference to one that has gone.
 */
export function useInfiniteScroll({
  onLoadMore,
  enabled,
}: {
  onLoadMore: () => void
  /** False once there is nothing left to fetch, which stops observing. */
  enabled: boolean
}) {
  const handler = useRef(onLoadMore)
  useEffect(() => {
    handler.current = onLoadMore
  }, [onLoadMore])

  const observer = useRef<IntersectionObserver | null>(null)
  useEffect(() => () => observer.current?.disconnect(), [])

  return useCallback(
    (node: HTMLElement | null) => {
      observer.current?.disconnect()
      observer.current = null
      if (!node || !enabled || typeof IntersectionObserver === "undefined") return
      observer.current = new IntersectionObserver(
        (entries) => {
          if (entries.some((entry) => entry.isIntersecting)) handler.current()
        },
        // Fetch a little before the sentinel is reached, so the next rows are
        // usually there by the time the user arrives at the bottom.
        { rootMargin: "300px" },
      )
      observer.current.observe(node)
    },
    [enabled],
  )
}
