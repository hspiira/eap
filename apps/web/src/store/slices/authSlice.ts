/**
 * Auth store slice
 * Single source of truth for authentication state.
 *
 * Always starts in loading state to avoid SSR hydration mismatch.
 * AppBootstrap calls authActions.initAuth() to hydrate from localStorage on mount.
 */

import { create } from 'zustand'

import { authStorage } from '@/lib/storage'

export interface AuthState {
  token: string | null
  user_id: string | null
  email: string | null
  isAuthenticated: boolean
  isLoading: boolean
  error: string | null
}

export interface AuthActions {
  setAuth: (token: string | null, user_id?: string | null, email?: string | null) => void
  setLoading: (loading: boolean) => void
  setError: (error: string | null) => void
  clearError: () => void
  clearAuth: () => void
}

export type AuthStore = AuthState & AuthActions

const initialState: AuthState = {
  token: null,
  user_id: null,
  email: null,
  isAuthenticated: false,
  isLoading: true,
  error: null,
}

export const useAuthStore = create<AuthStore>((set) => ({
  ...initialState,

  setAuth: (token, user_id, email) => {
    const useCookies =
      typeof import.meta !== 'undefined' && import.meta.env?.VITE_AUTH_USE_COOKIES === 'true'
    authStorage.patch({
      token: useCookies ? null : token ?? null,
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

  setLoading: (isLoading) => set({ isLoading }),

  setError: (error) => set({ error }),

  clearError: () => set({ error: null }),

  clearAuth: () => {
    authStorage.clear()
    set({
      token: null,
      user_id: null,
      email: null,
      isAuthenticated: false,
      error: null,
    })
  },
}))
