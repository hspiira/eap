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

export interface UseEntityListOptions<T> {
  resource: string
  params: ListParams
  listFn: (params: ListParams) => Promise<PaginatedResponse<T>>
  enabled?: boolean
  staleTime?: number
}

export function useEntityList<T>({
  resource,
  params,
  listFn,
  enabled,
  staleTime,
}: UseEntityListOptions<T>) {
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
}

export function useEntityMutation<TVariables, TResult>(
  opts: UseEntityMutationOptions<TVariables, TResult>,
) {
  const qc = useQueryClient()
  const { resource, mutationFn, detailId, skipListInvalidation, onSuccess, ...rest } = opts

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
      onSuccess?.(result, vars, ...rest_args)
    },
    ...rest,
  })
}
