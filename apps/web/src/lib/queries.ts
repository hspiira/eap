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
  useInfiniteQuery,
  useMutation,
  type UseMutationOptions,
  useQuery,
  useQueryClient,
  type UseQueryOptions,
} from "@tanstack/react-query"

import type { ListParams, PaginatedResponse } from "@/types/api"

export function entityListKey(resource: string, params?: object): QueryKey {
  return params ? [resource, "list", params] : [resource, "list"]
}

export function entityDetailKey(resource: string, id: string): QueryKey {
  return [resource, "detail", id]
}

export interface UseEntityListOptions<T, P extends ListParams = ListParams> {
  resource: string
  params: P
  listFn: (params: P) => Promise<PaginatedResponse<T>>
  enabled?: boolean
  staleTime?: number
  /** Poll while the list is on screen. See LIVE_REFRESH_MS. */
  refetchInterval?: number | false
}

export function useEntityList<T, P extends ListParams = ListParams>({
  resource,
  params,
  listFn,
  enabled,
  staleTime,
  refetchInterval,
}: UseEntityListOptions<T, P>) {
  return useQuery({
    queryKey: entityListKey(resource, params),
    queryFn: () => listFn(params),
    placeholderData: (prev) => prev,
    enabled,
    staleTime,
    refetchInterval,
  } as UseQueryOptions<PaginatedResponse<T>>)
}

/**
 * A list that grows as the user scrolls, without losing the page controls.
 *
 * `params.page` is the anchor: the first page shown, and where a jump from the
 * pagination bar lands. Scrolling appends the pages after it. Anything that
 * changes the query key, a filter, the search, the sort or the anchor itself,
 * drops the appended pages and starts again, which is what the user means by
 * re-filtering a list.
 *
 * The shape of `data` matches `useEntityList` so a page can keep reading
 * `data.items` and `data.total`, with `total` taken from the newest page
 * fetched rather than the oldest.
 */
export function useEntityListPages<T, P extends ListParams = ListParams>({
  resource,
  params,
  listFn,
  enabled,
  staleTime,
  refetchInterval,
  anchorPage,
  pageParams,
}: UseEntityListOptions<T, P> & {
  /** The first page to show, when it is not `params.page`. */
  anchorPage?: number
  /**
   * How a page number reaches the API. Defaults to `{ page }`; an endpoint
   * that takes an offset supplies its own, or every page after the first
   * repeats the rows of the anchor.
   */
  pageParams?: (page: number) => Partial<P>
}) {
  const anchor = anchorPage ?? params.page ?? 1
  const query = useInfiniteQuery({
    queryKey: entityListKey(resource, params),
    queryFn: ({ pageParam }) =>
      listFn({
        ...params,
        ...(pageParams ? pageParams(pageParam as number) : { page: pageParam as number }),
      }),
    initialPageParam: anchor,
    // Counted from the page that was asked for, not the one the response
    // reports: an endpoint paged by offset has no page number to echo back.
    getNextPageParam: (last: PaginatedResponse<T>, _all, lastParam) =>
      last.has_more ? (lastParam as number) + 1 : undefined,
    placeholderData: (prev) => prev,
    enabled,
    staleTime,
    refetchInterval,
  })

  const pages = query.data?.pages as PaginatedResponse<T>[] | undefined
  const data = pages
    ? {
        items: pages.flatMap((p) => p.items),
        total: pages[pages.length - 1]?.total ?? 0,
        page: anchor,
        limit: pages[0]?.limit ?? params.limit ?? 0,
        has_more: pages[pages.length - 1]?.has_more ?? false,
      }
    : undefined

  return {
    ...query,
    data,
    /**
     * Held back while placeholder pages from the previous filter are showing.
     * Appending onto those would fetch the old query's next page and splice
     * rows the user has just filtered out back into the table.
     */
    hasMore: query.hasNextPage && !query.isPlaceholderData,
    loadingMore: query.isFetchingNextPage,
    loadMore: () => {
      if (query.hasNextPage && !query.isFetchingNextPage && !query.isPlaceholderData) {
        void query.fetchNextPage()
      }
    },
  }
}

export interface UseEntityDetailOptions<T> {
  resource: string
  id: string | null | undefined
  detailFn: (id: string) => Promise<T>
  enabled?: boolean
  staleTime?: number
  /** Poll while the record is on screen. See LIVE_REFRESH_MS. */
  refetchInterval?: number | false
}

export function useEntityDetail<T>({
  resource,
  id,
  detailFn,
  enabled,
  staleTime,
  refetchInterval,
}: UseEntityDetailOptions<T>) {
  return useQuery({
    queryKey: entityDetailKey(resource, id ?? ""),
    queryFn: () => detailFn(id as string),
    enabled: enabled !== undefined ? enabled : !!id,
    staleTime,
    refetchInterval,
  } as UseQueryOptions<T>)
}

export interface UseEntityMutationOptions<TVariables = void, TResult = unknown> extends Omit<
  UseMutationOptions<TResult, unknown, TVariables>,
  "mutationFn"
> {
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

export function useEntityMutation<TVariables = void, TResult = unknown>(
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
        await qc.invalidateQueries({ queryKey: [resource, "list"] })
      }
      const id = typeof detailId === "function" ? detailId(result, vars) : detailId
      if (id) {
        await qc.invalidateQueries({ queryKey: entityDetailKey(resource, id) })
      }
      const extras =
        typeof invalidateKeys === "function" ? invalidateKeys(result, vars) : invalidateKeys
      if (extras && extras.length > 0) {
        await Promise.all(extras.map((key) => qc.invalidateQueries({ queryKey: key })))
      }
      onSuccess?.(result, vars, ...rest_args)
    },
    ...rest,
  })
}
