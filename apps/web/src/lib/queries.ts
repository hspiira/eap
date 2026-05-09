/**
 * Resource-oriented wrappers around TanStack Query.
 *
 * Convention:
 *   list   → ['<resource>', 'list', params]
 *   detail → ['<resource>', 'detail', id]
 *
 * On mutation, invalidate the matching prefix to refetch lists/details that depend on it.
 */

import {
  type QueryKey,
  useMutation,
  type UseMutationOptions,
  useQuery,
  useQueryClient,
  type UseQueryOptions,
} from '@tanstack/react-query'

import type { ListParams, PaginatedResponse } from '@/types/api'

export function entityListKey(resource: string, params?: object): QueryKey {
  return params ? [resource, 'list', params] : [resource, 'list']
}

export function entityDetailKey(resource: string, id: string): QueryKey {
  return [resource, 'detail', id]
}

export interface UseEntityListOptions<T, P extends ListParams = ListParams> {
  resource: string
  params: P
  listFn: (params: P) => Promise<PaginatedResponse<T>>
  enabled?: boolean
  staleTime?: number
}

export function useEntityList<T, P extends ListParams = ListParams>({
  resource,
  params,
  listFn,
  enabled,
  staleTime,
}: UseEntityListOptions<T, P>) {
  return useQuery({
    queryKey: entityListKey(resource, params),
    queryFn: () => listFn(params),
    placeholderData: (prev) => prev,
    enabled,
    staleTime,
  } as UseQueryOptions<PaginatedResponse<T>>)
}

export interface UseEntityDetailOptions<T> {
  resource: string
  id: string | null | undefined
  detailFn: (id: string) => Promise<T>
  enabled?: boolean
  staleTime?: number
}

export function useEntityDetail<T>({
  resource,
  id,
  detailFn,
  enabled,
  staleTime,
}: UseEntityDetailOptions<T>) {
  return useQuery({
    queryKey: entityDetailKey(resource, id ?? ''),
    queryFn: () => detailFn(id as string),
    enabled: enabled !== undefined ? enabled : !!id,
    staleTime,
  } as UseQueryOptions<T>)
}

export interface UseEntityMutationOptions<TVariables, TResult>
  extends Omit<UseMutationOptions<TResult, unknown, TVariables>, 'mutationFn'> {
  resource: string
  mutationFn: (vars: TVariables) => Promise<TResult>
  /** Detail id to invalidate after success (for update/delete). */
  detailId?: string | ((result: TResult, vars: TVariables) => string | null | undefined)
  /** Skip invalidating list queries (rare). Defaults to false. */
  skipListInvalidation?: boolean
  /**
   * Extra query keys to invalidate after success (for nested/related caches).
   * Can be static or computed from result + variables. Use the broadest prefix
   * that should refetch (e.g. `['engagements', 'timeline', engagementId]`).
   */
  invalidateKeys?: QueryKey[] | ((result: TResult, vars: TVariables) => QueryKey[])
}

export function useEntityMutation<TVariables, TResult>(
  opts: UseEntityMutationOptions<TVariables, TResult>,
) {
  const qc = useQueryClient()
  const {
    resource,
    mutationFn,
    detailId,
    skipListInvalidation,
    invalidateKeys,
    onSuccess,
    ...rest
  } = opts

  return useMutation({
    mutationFn,
    onSuccess: async (result, vars, ...rest_args) => {
      if (!skipListInvalidation) {
        await qc.invalidateQueries({ queryKey: [resource, 'list'] })
      }
      const id =
        typeof detailId === 'function' ? detailId(result, vars) : detailId
      if (id) {
        await qc.invalidateQueries({ queryKey: entityDetailKey(resource, id) })
      }
      const extras =
        typeof invalidateKeys === 'function' ? invalidateKeys(result, vars) : invalidateKeys
      if (extras && extras.length > 0) {
        await Promise.all(
          extras.map((key) => qc.invalidateQueries({ queryKey: key })),
        )
      }
      onSuccess?.(result, vars, ...rest_args)
    },
    ...rest,
  })
}
