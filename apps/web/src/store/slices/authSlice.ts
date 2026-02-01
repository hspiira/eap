/**
 * Auth store slice
 * Single source of truth for authentication state.
 * AuthContext syncs with this store (read/write).
 *
 * IMPORTANT: Always starts in loading state to avoid SSR hydration mismatch.
 * AuthContext hydrates from localStorage after mount.
 */

import { create } from 'zustand'

export interface AuthState {
  token: string | null
  user_id: string | null
  email: string | null
  isAuthenticated: boolean
  isLoading: boolean
}

export interface AuthActions {
  setAuth: (token: string | null, user_id?: string | null, email?: string | null) => void
  setLoading: (loading: boolean) => void
  clearAuth: () => void
}

export type AuthStore = AuthState & AuthActions

// Always start with loading state - both server and client render the same initially.
// Client hydrates from localStorage in AuthContext useEffect after mount.
const initialState: AuthState = {
  token: null,
  user_id: null,
  email: null,
  isAuthenticated: false,
  isLoading: true,
}

export const useAuthStore = create<AuthStore>((set) => ({
  ...initialState,

  setAuth: (token, user_id, email) => {
    // Persist to localStorage
    if (typeof window !== 'undefined') {
      if (token) {
        localStorage.setItem('auth_token', token)
      } else {
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
      isAuthenticated: !!token,
    })
  },

  setLoading: (isLoading) => set({ isLoading }),

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
    })
  },
}))
