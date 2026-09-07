/**
 * Global search state that lives outside React: the open/close signal and the
 * lifetime of cached record results.
 *
 * Results are keyed by identity and tenant, so a new session cannot read the
 * previous one's rows even before anything is cleared. `clearGlobalSearch`
 * additionally cancels requests still in flight, so a late response from the
 * old session cannot repopulate the cache after a sign-out or a switch.
 */

import type { QueryKey } from "@tanstack/react-query"

import { queryClient } from "@/lib/query-client"

const TOGGLE_EVENT = "toggle-global-search"

/** The prefix every global-search query shares. */
export const GLOBAL_SEARCH_KEY: QueryKey = ["search", "global"]

export interface SearchScope {
  userId: string | null
  tenantId: string | null
}

export function globalSearchQueryKey(scope: SearchScope, query: string, limit: number): QueryKey {
  return [...GLOBAL_SEARCH_KEY, scope.userId, scope.tenantId, query, limit]
}

export function openGlobalSearch(): void {
  window.dispatchEvent(new Event(TOGGLE_EVENT))
}

/** Subscribe to launcher clicks from the header and anywhere else. */
export function onGlobalSearchToggle(handler: () => void): () => void {
  window.addEventListener(TOGGLE_EVENT, handler)
  return () => window.removeEventListener(TOGGLE_EVENT, handler)
}

/**
 * Drop every cached record search and cancel the in-flight ones. Call on
 * sign-out, on a change of identity, and on a change of workspace.
 */
export async function clearGlobalSearch(): Promise<void> {
  await queryClient.cancelQueries({ queryKey: GLOBAL_SEARCH_KEY })
  queryClient.removeQueries({ queryKey: GLOBAL_SEARCH_KEY })
}
