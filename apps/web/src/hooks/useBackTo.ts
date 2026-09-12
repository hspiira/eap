import { useCallback } from "react"

import { useCanGoBack, useNavigate, useRouter } from "@tanstack/react-router"

/**
 * Leave a detail page the way the user arrived at it.
 *
 * Steps back through history when there is app history to step through, and
 * navigates to `fallback` only on a page opened cold (a deep link, a new tab).
 * Navigating straight to the bare list route instead discards the search,
 * filters, page and scroll position the list held, because a list keeps all of
 * those in its URL; it also pushes an entry, so the browser's own back button
 * then returns to the detail page the user just left.
 */
export function useBackTo(fallback: string): () => void {
  const router = useRouter()
  const navigate = useNavigate()
  const canGoBack = useCanGoBack()

  return useCallback(() => {
    if (canGoBack) {
      router.history.back()
      return
    }
    void navigate({ to: fallback as never })
  }, [canGoBack, router, navigate, fallback])
}
