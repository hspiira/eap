import { useState, useCallback, useEffect } from 'react'
import type { ListParams, PaginatedResponse } from '@/types/api'
import { normalizeErrorMessage } from '@/utils/errorHandler'

export interface UseListOptions<T> {
  listFn: (params: ListParams) => Promise<PaginatedResponse<T>>
  initialParams?: Partial<ListParams>
  errorFallback?: string
}

export interface UseListResult<T> {
  items: T[]
  total: number
  page: number
  limit: number
  has_more: boolean
  setPage: (page: number) => void
  setParams: (params: Partial<ListParams> | ((prev: ListParams) => Partial<ListParams>)) => void
  loading: boolean
  error: string | null
  refetch: () => Promise<void>
}

const defaultParams: ListParams = {
  page: 1,
  limit: 20,
}

export function useList<T>({
  listFn,
  initialParams = {},
  errorFallback = 'Failed to load data',
}: UseListOptions<T>): UseListResult<T> {
  const [params, setParamsState] = useState<ListParams>({ ...defaultParams, ...initialParams })
  const [items, setItems] = useState<T[]>([])
  const [total, setTotal] = useState(0)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const refetch = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const response = await listFn(params)
      setItems(response.items)
      setTotal(response.total)
    } catch (err: unknown) {
      setError(normalizeErrorMessage(err, errorFallback))
    } finally {
      setLoading(false)
    }
  }, [listFn, params, errorFallback])

  useEffect(() => {
    refetch()
  }, [refetch])

  const setPage = useCallback((page: number) => {
    setParamsState((prev) => ({ ...prev, page: Math.max(1, page) }))
  }, [])

  const setParams = useCallback(
    (update: Partial<ListParams> | ((prev: ListParams) => Partial<ListParams>)) => {
      setParamsState((prev) => {
        const next = typeof update === 'function' ? update(prev) : update
        return { ...prev, ...next }
      })
    },
    []
  )

  const page = params.page ?? defaultParams.page!
  const limit = params.limit ?? defaultParams.limit!
  const has_more = total > 0 && page * limit < total

  return {
    items,
    total,
    page,
    limit,
    has_more,
    setPage,
    setParams,
    loading,
    error,
    refetch,
  }
}
