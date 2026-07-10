import { useQuery } from '@tanstack/react-query'

import { usersApi } from '@/api/endpoints/users'
import { useAuthStore } from '@/store/slices/authSlice'
import { TenantRole } from '@/types/enums'

export function useCurrentRole(): TenantRole | null {
  const userId = useAuthStore((s) => s.user_id)
  const { data } = useQuery({
    queryKey: ['user', userId],
    queryFn: () => usersApi.getById(userId!),
    enabled: !!userId,
    staleTime: 5 * 60_000,
  })
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
