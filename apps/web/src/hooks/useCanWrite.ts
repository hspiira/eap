import { useQuery } from "@tanstack/react-query"

import { authApi } from "@/api/endpoints/auth"
import { usersApi } from "@/api/endpoints/users"
import { queryKeys } from "@/lib/query-keys"
import { useAuthStore } from "@/store/slices/authSlice"
import { AccessScope, TenantRole } from "@/types/enums"

function useCurrentUser() {
  const userId = useAuthStore((s) => s.user_id)
  return useQuery({
    queryKey: queryKeys.users.detail(userId ?? ""),
    queryFn: () => usersApi.getById(userId!),
    enabled: !!userId,
    staleTime: 5 * 60_000,
  })
}

export function useCurrentRole(): TenantRole | null {
  const { data } = useCurrentUser()
  return (data?.role as TenantRole) ?? null
}

/**
 * Returns false once the current user's role is confirmed to be Viewer;
 * returns true while loading or for Admin/User roles.
 */
export function useCanWrite(): boolean {
  const role = useCurrentRole()
  return role !== TenantRole.VIEWER
}

/**
 * Whether the current user holds the Clinical scope. `isLoading` lets a
 * gate distinguish "still checking" from "confirmed no access", clinical
 * (PHI) routes must fail closed once resolved, but shouldn't flash a
 * forbidden screen while the check is in flight.
 */
export function useHasClinicalScope(): { hasScope: boolean; isLoading: boolean } {
  const { data, isPending } = useCurrentUser()
  return {
    hasScope: (data?.access_scopes ?? []).includes(AccessScope.CLINICAL),
    isLoading: isPending,
  }
}

/**
 * Whether this session may administer platform-wide surfaces.
 *
 * Derived server-side from PLATFORM_TENANT_ID and read off `/auth/me`, rather
 * than recomputed from VITE_PLATFORM_TENANT_ID. Two copies of the rule drifted:
 * the frontend skipped its check when the variable was unset and showed the
 * surface to everyone, while the API failed closed and returned 403.
 *
 * `isLoading` lets a gate distinguish "still checking" from "confirmed no", so
 * it can avoid flashing a forbidden screen mid-flight.
 */
export function useIsPlatformAdmin(): { isPlatformAdmin: boolean; isLoading: boolean } {
  const userId = useAuthStore((s) => s.user_id)
  const { data, isPending } = useQuery({
    queryKey: ["auth", "me"],
    queryFn: authApi.me,
    enabled: !!userId,
    staleTime: 5 * 60_000,
  })
  return {
    isPlatformAdmin: data?.is_platform_admin === true,
    isLoading: !!userId && isPending,
  }
}
