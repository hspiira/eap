/**
 * Auth store slice — single source of truth for authentication state.
 *
 * Initial state is hydrated synchronously from localStorage at module init, so
 * `useAuthStore.getState().token` is correct before AppBootstrap mounts.
 * Setters write through to storage; the apiClient reads/writes via this slice
 * rather than touching storage directly.
 */

import { create } from 'zustand'

import { authStorage } from '@/lib/storage'

function useCookies(): boolean {
  return (
    typeof import.meta !== 'undefined' &&
    import.meta.env?.VITE_AUTH_USE_COOKIES === 'true'
  )
}

export interface AuthState {
  token: string | null
  refreshToken: string | null
  csrfToken: string | null
  tokenExpiresAt: number | null
  user_id: string | null
  email: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}

export interface AuthActions {
  setAuth: (token: string | null, user_id?: string | null, email?: string | null) => void
  setToken: (token: string | null, expiresInSeconds?: number) => void
  setRefreshToken: (token: string | null) => void
  setCsrfToken: (token: string | null) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearError: () => void
  clearAuth: () => void
}

export type AuthStore = AuthState & AuthActions

function readInitialState(): AuthState {
  const persisted = authStorage.read()
  const token = useCookies() ? null : persisted.token
  const refreshToken = useCookies() ? null : persisted.refresh_token
  return {
    token,
    refreshToken,
    csrfToken: persisted.csrf_token,
    tokenExpiresAt: persisted.token_expires_at,
    user_id: persisted.user_id,
    email: persisted.email,
    isAuthenticated: !!(token || persisted.user_id),
    isLoading: true,
    error: null,
  }
}

export const useAuthStore = create<AuthStore>((set) => ({
  ...readInitialState(),

  setAuth: (token, user_id, email) => {
    const cookieMode = useCookies()
    authStorage.patch({
      token: cookieMode ? null : token ?? null,
      user_id: user_id ?? null,
      email: email ?? null,
    })
    set({
      token,
      user_id: user_id ?? null,
      email: email ?? null,
      isAuthenticated: !!token || !!(user_id ?? null),
      error: null,
    })
  },

  setToken: (token, expiresInSeconds) => {
    const cookieMode = useCookies()
    const tokenExpiresAt =
      token && typeof expiresInSeconds === 'number'
        ? Date.now() + expiresInSeconds * 1000
        : null
    if (!cookieMode) authStorage.patch({ token, token_expires_at: tokenExpiresAt })
    set({ token, tokenExpiresAt })
  },

  setRefreshToken: (refreshToken) => {
    if (!useCookies()) authStorage.patch({ refresh_token: refreshToken })
    set({ refreshToken })
  },

  setCsrfToken: (csrfToken) => {
    authStorage.patch({ csrf_token: csrfToken })
    set({ csrfToken })
  },

  setLoading: (isLoading) => set({ isLoading }),

  setError: (error) => set({ error }),

  clearError: () => set({ error: null }),

  clearAuth: () => {
    authStorage.clear()
    set({
      token: null,
      refreshToken: null,
      csrfToken: null,
      tokenExpiresAt: null,
      user_id: null,
      email: null,
      isAuthenticated: false,
      error: null,
    })
  },
}))
