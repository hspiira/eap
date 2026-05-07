import { useCallback, useEffect,useState } from 'react'

import { normalizeErrorMessage } from '@/utils/errorHandler'

export interface ListResourceParams {
  page: number
  limit: number
  search?: string
  status?: string
  sort_by?: string
  sort_desc?: boolean
}

export interface UseListResourceOptions<T> {
  fetchList: (params: ListResourceParams) => Promise<{ items: T[]; total: number }>
  initialPageSize?: number
  errorFallback?: string
}

export type SortDirection = 'asc' | 'desc' | null

export function useListResource<T>({
  fetchList,
  initialPageSize = 25,
  errorFallback = 'Failed to load data',
}: UseListResourceOptions<T>) {
  const [items, setItems] = useState<T[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [currentPage, setCurrentPage] = useState(1)
  const [pageSize, setPageSize] = useState(initialPageSize)
  const [totalItems, setTotalItems] = useState(0)
  const [searchValue, setSearchValue] = useState('')
  const [statusFilter, setStatusFilter] = useState('')
  const [sortBy, setSortBy] = useState<string | null>(null)
  const [sortDirection, setSortDirection] = useState<SortDirection>(null)

  const refetch = useCallback(async () => {
    try {
      setLoading(true)
      setError(null)
      const params: ListResourceParams = {
        page: currentPage,
        limit: pageSize,
      }
      if (searchValue) params.search = searchValue
      if (statusFilter) params.status = statusFilter
      if (sortBy) {
        params.sort_by = sortBy
        params.sort_desc = sortDirection === 'desc'
      }
      const response = await fetchList(params)
      setItems(response.items)
      setTotalItems(response.total)
    } catch (err: unknown) {
      setError(normalizeErrorMessage(err, errorFallback))
      console.error('List fetch error:', err)
    } finally {
      setLoading(false)
    }
  }, [currentPage, pageSize, searchValue, statusFilter, sortBy, sortDirection, fetchList, errorFallback])

  useEffect(() => {
    refetch()
  }, [refetch])

  const handleSort = useCallback((columnId: string) => {
    if (sortBy === columnId) {
      if (sortDirection === 'asc') setSortDirection('desc')
      else if (sortDirection === 'desc') {
        setSortBy(null)
        setSortDirection(null)
      } else {
        setSortDirection('asc')
      }
    } else {
      setSortBy(columnId)
      setSortDirection('asc')
    }
  }, [sortBy, sortDirection])

  const setPageSizeAndReset = useCallback((size: number) => {
    setPageSize(size)
    setCurrentPage(1)
  }, [])

  const setSearchAndResetPage = useCallback((value: string) => {
    setSearchValue(value)
    setCurrentPage(1)
  }, [])

  const setStatusAndResetPage = useCallback((value: string) => {
    setStatusFilter(value)
    setCurrentPage(1)
  }, [])

  const clearFilters = useCallback(() => {
    setSearchValue('')
    setStatusFilter('')
    setCurrentPage(1)
  }, [])

  return {
    items,
    loading,
    error,
    refetch,
    currentPage,
    setCurrentPage,
    pageSize,
    setPageSize: setPageSizeAndReset,
    totalItems,
    searchValue,
    setSearchValue: setSearchAndResetPage,
    statusFilter,
    setStatusFilter: setStatusAndResetPage,
    sortBy,
    sortDirection,
    setSortBy,
    setSortDirection,
    handleSort,
    clearFilters,
  }
}
