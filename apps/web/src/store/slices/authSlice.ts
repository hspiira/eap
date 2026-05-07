/**
 * Auth store slice
 * Single source of truth for authentication state.
 *
 * Always starts in loading state to avoid SSR hydration mismatch.
 * AppBootstrap calls authActions.initAuth() to hydrate from localStorage on mount.
 */

import { create } from 'zustand'

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
    const useCookies = typeof import.meta !== 'undefined' && import.meta.env?.VITE_AUTH_USE_COOKIES === 'true'
    if (typeof window !== 'undefined') {
      if (token && !useCookies) {
        localStorage.setItem('auth_token', token)
      } else if (!token || useCookies) {
        localStorage.removeItem('auth_token')
      }
      if (user_id) {
        localStorage.setItem('auth_user_id', user_id)
      } else {
        localStorage.removeItem('auth_user_id')
      }
      if (email) {
        localStorage.setItem('auth_email', email)
      } else {
        localStorage.removeItem('auth_email')
      }
    }

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
    // Clear from localStorage
    if (typeof window !== 'undefined') {
      localStorage.removeItem('auth_token')
      localStorage.removeItem('auth_user_id')
      localStorage.removeItem('auth_email')
    }

    set({
      token: null,
      user_id: null,
      email: null,
      isAuthenticated: false,
      error: null,
    })
  },
}))
