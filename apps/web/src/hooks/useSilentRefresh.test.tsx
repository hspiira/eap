import { renderHook } from '@testing-library/react'
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest'

import apiClient from '@/api/client'
import { useSilentRefresh } from '@/hooks/useSilentRefresh'
import { useAuthStore } from '@/store/slices/authSlice'

describe('useSilentRefresh', () => {
  beforeEach(() => {
    vi.useFakeTimers()
    apiClient.clearAuth()
    useAuthStore.setState({
      token: null,
      user_id: null,
      email: null,
      isAuthenticated: false,
      isLoading: false,
      error: null,
    })
  })
  afterEach(() => {
    vi.useRealTimers()
    vi.restoreAllMocks()
  })

  it('does nothing when unauthenticated', () => {
    const spy = vi.spyOn(apiClient, 'refreshAccessToken').mockResolvedValue(true)
    renderHook(() => useSilentRefresh())
    vi.advanceTimersByTime(120_000)
    expect(spy).not.toHaveBeenCalled()
  })

  it('does nothing when token expiry is unknown', () => {
    apiClient.setToken('tok-1') // no expiresIn → no expiry tracked
    useAuthStore.getState().setAuth('tok-1', 'u', 'e')
    const spy = vi.spyOn(apiClient, 'refreshAccessToken').mockResolvedValue(true)

    renderHook(() => useSilentRefresh())
    vi.advanceTimersByTime(120_000)
    expect(spy).not.toHaveBeenCalled()
  })

  it('refreshes ~1 min before expiry', async () => {
    apiClient.setToken('tok-1', 120) // 2 minute TTL
    useAuthStore.getState().setAuth('tok-1', 'u', 'e')
    const spy = vi.spyOn(apiClient, 'refreshAccessToken').mockResolvedValue(true)

    renderHook(() => useSilentRefresh())

    vi.advanceTimersByTime(59_999) // just before fire-time (60s before expiry)
    expect(spy).not.toHaveBeenCalled()

    vi.advanceTimersByTime(2) // crossed fire-time
    expect(spy).toHaveBeenCalledTimes(1)
  })

  it('clears auth when refresh fails', async () => {
    apiClient.setToken('tok-1', 90) // 90s TTL → fires at ~30s
    useAuthStore.getState().setAuth('tok-1', 'u', 'e')
    vi.spyOn(apiClient, 'refreshAccessToken').mockResolvedValue(false)

    renderHook(() => useSilentRefresh())

    vi.advanceTimersByTime(35_000)
    await vi.advanceTimersByTimeAsync(0)
    expect(useAuthStore.getState().isAuthenticated).toBe(false)
  })

  it('uses MIN_DELAY when expiry has already passed', () => {
    apiClient.setToken('tok-1', 1) // 1s TTL → past fire-time immediately
    useAuthStore.getState().setAuth('tok-1', 'u', 'e')
    const spy = vi.spyOn(apiClient, 'refreshAccessToken').mockResolvedValue(true)

    renderHook(() => useSilentRefresh())

    vi.advanceTimersByTime(4_000) // before MIN_DELAY (5s)
    expect(spy).not.toHaveBeenCalled()
    vi.advanceTimersByTime(2_000) // crossed MIN_DELAY
    expect(spy).toHaveBeenCalledTimes(1)
  })
})
