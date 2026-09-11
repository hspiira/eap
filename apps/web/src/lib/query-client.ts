import { QueryClient } from "@tanstack/react-query"

/**
 * How often a table that shows work arriving refetches while it is on screen.
 *
 * Opt in per query with `refetchInterval`; it is not a default, because a
 * screen nobody is watching still costs a request and a database read every
 * time it fires. TanStack pauses the interval while the tab is hidden.
 */
export const LIVE_REFRESH_MS = 30_000

export const queryClient = new QueryClient({
  defaultOptions: {
    queries: {
      staleTime: 30_000,
      retry: 1,
      // Coming back to a tab is when stale data is most visible and most
      // misleading. `staleTime` still applies, so this refetches what is
      // actually old rather than everything on every focus.
      refetchOnWindowFocus: true,
    },
  },
})
