import { QueryClient, QueryClientProvider } from '@tanstack/react-query'
import { act, renderHook, waitFor } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import {
  entityDetailKey,
  entityListKey,
  useEntityDetail,
  useEntityList,
  useEntityMutation,
} from '@/lib/queries'

interface Item {
  id: string
  name: string
}

let queryClient: QueryClient

beforeEach(() => {
  queryClient = new QueryClient({
    defaultOptions: {
      queries: { retry: false, staleTime: 0, gcTime: 0 },
      mutations: { retry: false },
    },
  })
})
afterEach(() => queryClient.clear())

function wrapper({ children }: { children: React.ReactNode }) {
  return <QueryClientProvider client={queryClient}>{children}</QueryClientProvider>
}

describe('query keys', () => {
  it('entityListKey produces stable shape', () => {
    expect(entityListKey('clients', { page: 1 })).toEqual(['clients', 'list', { page: 1 }])
    expect(entityListKey('clients')).toEqual(['clients', 'list'])
  })

  it('entityDetailKey produces stable shape', () => {
    expect(entityDetailKey('clients', 'abc')).toEqual(['clients', 'detail', 'abc'])
  })
})

describe('useEntityList', () => {
  it('calls listFn with the params and exposes data', async () => {
    const listFn = vi.fn().mockResolvedValue({
      items: [{ id: '1', name: 'a' }],
      total: 1,
      page: 1,
      limit: 20,
      has_more: false,
    })
    const { result } = renderHook(
      () =>
        useEntityList<Item>({
          resource: 'clients',
          params: { page: 1, limit: 20 },
          listFn,
        }),
      { wrapper },
    )

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(listFn).toHaveBeenCalledWith({ page: 1, limit: 20 })
    expect(result.current.data?.items).toEqual([{ id: '1', name: 'a' }])
  })

  it('refetches when params change (different query key)', async () => {
    const listFn = vi.fn().mockImplementation((p) => {
      return Promise.resolve({ items: [], total: p.page, page: p.page, limit: 20, has_more: false })
    })

    const { result, rerender } = renderHook(
      ({ page }) =>
        useEntityList<Item>({ resource: 'clients', params: { page, limit: 20 }, listFn }),
      { wrapper, initialProps: { page: 1 } },
    )

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(listFn).toHaveBeenCalledTimes(1)

    rerender({ page: 2 })
    await waitFor(() => expect(result.current.data?.total).toBe(2))
    expect(listFn).toHaveBeenCalledTimes(2)
  })

  it('exposes isError when listFn rejects', async () => {
    const listFn = vi.fn().mockRejectedValue(new Error('nope'))
    const { result } = renderHook(
      () => useEntityList<Item>({ resource: 'clients', params: { page: 1 }, listFn }),
      { wrapper },
    )
    await waitFor(() => expect(result.current.isError).toBe(true))
  })
})

describe('useEntityDetail', () => {
  it('calls detailFn with the id', async () => {
    const detailFn = vi.fn().mockResolvedValue({ id: 'abc', name: 'thing' })
    const { result } = renderHook(
      () => useEntityDetail<Item>({ resource: 'clients', id: 'abc', detailFn }),
      { wrapper },
    )

    await waitFor(() => expect(result.current.isSuccess).toBe(true))
    expect(detailFn).toHaveBeenCalledWith('abc')
    expect(result.current.data?.id).toBe('abc')
  })

  it('skips fetch when id is null', () => {
    const detailFn = vi.fn()
    const { result } = renderHook(
      () => useEntityDetail<Item>({ resource: 'clients', id: null, detailFn }),
      { wrapper },
    )
    expect(result.current.isPending).toBe(true)
    expect(detailFn).not.toHaveBeenCalled()
  })
})

describe('useEntityMutation', () => {
  it('runs the mutation and invalidates list queries', async () => {
    const seedQuery = vi.fn().mockResolvedValue({
      items: [{ id: '1', name: 'a' }],
      total: 1,
      page: 1,
      limit: 20,
      has_more: false,
    })
    queryClient.setQueryData(['clients', 'list', { page: 1 }], { items: [], total: 0 })
    const { result: listResult } = renderHook(
      () => useEntityList<Item>({ resource: 'clients', params: { page: 1 }, listFn: seedQuery }),
      { wrapper },
    )
    await waitFor(() => expect(listResult.current.isSuccess).toBe(true))
    expect(seedQuery).toHaveBeenCalledTimes(1)

    const mutationFn = vi.fn().mockResolvedValue({ id: '2', name: 'b' })
    const { result: mutationResult } = renderHook(
      () => useEntityMutation({ resource: 'clients', mutationFn }),
      { wrapper },
    )

    await act(async () => {
      await mutationResult.current.mutateAsync({ name: 'b' })
    })

    expect(mutationFn.mock.calls[0][0]).toEqual({ name: 'b' })
    await waitFor(() => expect(seedQuery).toHaveBeenCalledTimes(2))
  })

  it('invalidates detail when detailId is provided', async () => {
    queryClient.setQueryData(['clients', 'detail', 'abc'], { id: 'abc', name: 'old' })
    const detailFn = vi.fn().mockResolvedValue({ id: 'abc', name: 'fresh' })
    const { result: detailResult } = renderHook(
      () => useEntityDetail<Item>({ resource: 'clients', id: 'abc', detailFn }),
      { wrapper },
    )
    await waitFor(() => expect(detailResult.current.isSuccess).toBe(true))
    expect(detailFn).toHaveBeenCalledTimes(1)

    const mutationFn = vi.fn().mockResolvedValue({ id: 'abc', name: 'updated' })
    const { result: m } = renderHook(
      () => useEntityMutation({ resource: 'clients', mutationFn, detailId: 'abc' }),
      { wrapper },
    )
    await act(async () => {
      await m.current.mutateAsync({ name: 'updated' })
    })
    await waitFor(() => expect(detailFn).toHaveBeenCalledTimes(2))
  })

  it('forwards onSuccess to caller after invalidation', async () => {
    const onSuccess = vi.fn()
    const mutationFn = vi.fn().mockResolvedValue({ id: '1' })
    const { result } = renderHook(
      () => useEntityMutation({ resource: 'clients', mutationFn, onSuccess }),
      { wrapper },
    )
    await act(async () => {
      await result.current.mutateAsync({})
    })
    expect(onSuccess).toHaveBeenCalled()
  })

  it('skipListInvalidation prevents the list refetch', async () => {
    const listFn = vi.fn().mockResolvedValue({ items: [], total: 0, page: 1, limit: 20, has_more: false })
    const { result: listResult } = renderHook(
      () => useEntityList<Item>({ resource: 'clients', params: { page: 1 }, listFn }),
      { wrapper },
    )
    await waitFor(() => expect(listResult.current.isSuccess).toBe(true))
    expect(listFn).toHaveBeenCalledTimes(1)

    const mutationFn = vi.fn().mockResolvedValue({ id: '2' })
    const { result: m } = renderHook(
      () => useEntityMutation({ resource: 'clients', mutationFn, skipListInvalidation: true }),
      { wrapper },
    )
    await act(async () => {
      await m.current.mutateAsync({})
    })

    await new Promise((resolve) => setTimeout(resolve, 30))
    expect(listFn).toHaveBeenCalledTimes(1)
  })
})
