import { useQuery } from '@tanstack/react-query'

import { usersApi } from '@/api/endpoints/users'
import { useAuthStore } from '@/store/slices/authSlice'
import { AccessScope, TenantRole } from '@/types/enums'

function useCurrentUser() {
  const userId = useAuthStore((s) => s.user_id)
  return useQuery({
    queryKey: ['user', userId],
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
 * gate distinguish "still checking" from "confirmed no access" — clinical
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
