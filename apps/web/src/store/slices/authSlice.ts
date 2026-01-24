/**
 * Auth store slice
 * Single source of truth for authentication state.
 * AuthContext syncs with this store (read/write).
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

const initialState: AuthState = {
  token: null,
  isAuthenticated: false,
  isLoading: true,
}

export const useAuthStore = create<AuthStore>((set) => ({
  ...initialState,

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
