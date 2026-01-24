/**
 * Auth store slice
 * Single source of truth for authentication state.
 * AuthContext syncs with this store (read/write).
 * Hydrates from localStorage on init so we never have a false "logged out" phase on reload.
 */

import { create } from 'zustand'

export interface AuthState {
  token: string | null
  isAuthenticated: boolean
  isLoading: boolean
}

export interface AuthActions {
  setAuth: (token: string | null) => void
  setLoading: (loading: boolean) => void
  clearAuth: () => void
}

export type AuthStore = AuthState & AuthActions

function getInitialState(): AuthState {
  if (typeof window === 'undefined') {
    return { token: null, isAuthenticated: false, isLoading: true }
  }
  const token = localStorage.getItem('auth_token')
  return {
    token,
    isAuthenticated: !!token,
    isLoading: false,
  }
}

export const useAuthStore = create<AuthStore>((set) => ({
  ...getInitialState(),

  setAuth: (token) =>
    set({
      token,
      isAuthenticated: !!token,
    }),

  setLoading: (isLoading) => set({ isLoading }),

  clearAuth: () =>
    set({
      token: null,
      isAuthenticated: false,
    }),
}))
