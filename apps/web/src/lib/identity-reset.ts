import { queryClient } from "@/lib/query-client"
import { clearGlobalSearch } from "@/lib/search-state"

/**
 * Drop everything the previous identity can still be read from.
 *
 * Logout cleared the auth and tenant stores but left the query cache alone, so
 * a synthetic case put in the cache before `logout()` was still readable from
 * `queryClient` afterwards. Keys like `['cases', 'list']` carry neither tenant
 * nor user, so the next person to sign in on the same tab renders against them.
 *
 * Call this on every identity change, not only on logout: expiry, SSO, a failed
 * sign-in and a fresh login all move the workspace to a different subject.
 */
export function resetIdentityState(): Promise<void> {
  // Emptying the caches is synchronous on purpose. A workspace switch calls
  // this and returns immediately, and the render that follows must not be able
  // to read the previous tenant's rows while an awaited cancel is still
  // pending. `clear()` empties the mutation cache as well as the query cache.
  queryClient.clear()
  // Then stop anything still in flight from writing the old session's rows
  // back in. Both calls sit in one synchronous block, so no response can land
  // between them.
  return Promise.all([queryClient.cancelQueries(), clearGlobalSearch()]).then(() => undefined)
}
