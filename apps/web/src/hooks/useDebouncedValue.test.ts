import { act, renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import { useDebouncedValue } from '@/hooks/useDebouncedValue'

describe('useDebouncedValue', () => {
  beforeEach(() => vi.useFakeTimers())
  afterEach(() => vi.useRealTimers())

  it('returns initial value immediately', () => {
    const { result } = renderHook(() => useDebouncedValue('hello', 300))
    expect(result.current).toBe('hello')
  })

  it('delays updates by the configured ms', () => {
    const { result, rerender } = renderHook(({ v }) => useDebouncedValue(v, 300), {
      initialProps: { v: 'a' },
    })
    rerender({ v: 'b' })
    expect(result.current).toBe('a')
    act(() => {
      vi.advanceTimersByTime(299)
    })
    expect(result.current).toBe('a')
    act(() => {
      vi.advanceTimersByTime(1)
    })
    expect(result.current).toBe('b')
  })

  it('cancels pending update when value changes again', () => {
    const { result, rerender } = renderHook(({ v }) => useDebouncedValue(v, 300), {
      initialProps: { v: 'a' },
    })
    rerender({ v: 'b' })
    act(() => {
      vi.advanceTimersByTime(200)
    })
    rerender({ v: 'c' })
    act(() => {
      vi.advanceTimersByTime(200)
    })
    expect(result.current).toBe('a')
    act(() => {
      vi.advanceTimersByTime(100)
    })
    expect(result.current).toBe('c')
  })

  it('default delay is 300ms', () => {
    const { result, rerender } = renderHook(({ v }) => useDebouncedValue(v), {
      initialProps: { v: 1 },
    })
    rerender({ v: 2 })
    act(() => {
      vi.advanceTimersByTime(299)
    })
    expect(result.current).toBe(1)
    act(() => {
      vi.advanceTimersByTime(1)
    })
    expect(result.current).toBe(2)
  })

  it('handles non-string types', () => {
    const obj1 = { a: 1 }
    const obj2 = { a: 2 }
    const { result, rerender } = renderHook(({ v }) => useDebouncedValue(v, 100), {
      initialProps: { v: obj1 },
    })
    rerender({ v: obj2 })
    act(() => {
      vi.advanceTimersByTime(100)
    })
    expect(result.current).toBe(obj2)
  })
})
