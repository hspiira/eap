import { beforeEach, describe, expect, it } from 'vitest'

import { authStorage } from '@/lib/storage'
import { useAuthStore } from '@/store/slices/authSlice'

describe('useAuthStore', () => {
  beforeEach(() => {
    useAuthStore.setState({
      token: null,
      user_id: null,
      email: null,
      isAuthenticated: false,
      isLoading: true,
      error: null,
    })
    authStorage.clear()
  })

  it('starts in loading state with no auth', () => {
    const s = useAuthStore.getState()
    expect(s.isLoading).toBe(true)
    expect(s.isAuthenticated).toBe(false)
    expect(s.token).toBeNull()
  })

  it('setAuth marks the user authenticated', () => {
    useAuthStore.getState().setAuth('tok-1', 'user-1', 'a@b.com')
    const s = useAuthStore.getState()
    expect(s.token).toBe('tok-1')
    expect(s.user_id).toBe('user-1')
    expect(s.email).toBe('a@b.com')
    expect(s.isAuthenticated).toBe(true)
    expect(s.error).toBeNull()
  })

  it('setAuth persists to authStorage', () => {
    useAuthStore.getState().setAuth('tok-1', 'user-1', 'a@b.com')
    const stored = authStorage.read()
    expect(stored.token).toBe('tok-1')
    expect(stored.user_id).toBe('user-1')
    expect(stored.email).toBe('a@b.com')
  })

  it('setAuth with only user_id (cookie mode) still authenticates', () => {
    useAuthStore.getState().setAuth(null, 'user-1', 'a@b.com')
    expect(useAuthStore.getState().isAuthenticated).toBe(true)
  })

  it('clearAuth resets state and clears storage', () => {
    useAuthStore.getState().setAuth('tok-1', 'user-1', 'a@b.com')
    useAuthStore.getState().clearAuth()
    const s = useAuthStore.getState()
    expect(s.isAuthenticated).toBe(false)
    expect(s.token).toBeNull()
    expect(s.user_id).toBeNull()
    expect(s.email).toBeNull()
    const stored = authStorage.read()
    expect(stored.token).toBeNull()
    expect(stored.user_id).toBeNull()
  })

  it('setError + clearError', () => {
    useAuthStore.getState().setError('Bad password')
    expect(useAuthStore.getState().error).toBe('Bad password')
    useAuthStore.getState().clearError()
    expect(useAuthStore.getState().error).toBeNull()
  })

  it('setLoading flips the flag', () => {
    useAuthStore.getState().setLoading(false)
    expect(useAuthStore.getState().isLoading).toBe(false)
    useAuthStore.getState().setLoading(true)
    expect(useAuthStore.getState().isLoading).toBe(true)
  })

  it('setAuth clears any prior error', () => {
    useAuthStore.getState().setError('prior')
    useAuthStore.getState().setAuth('t', 'u', 'e')
    expect(useAuthStore.getState().error).toBeNull()
  })
})
