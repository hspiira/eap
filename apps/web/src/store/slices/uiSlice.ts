/**
 * UI store slice — global UI state (modals, theme, global loading).
 *
 * Theme is hydrated from localStorage at module init and persisted on every change.
 * The DOM mutations and system-theme listener are wired by the `useThemeEffect` hook
 * mounted at the route root.
 */

import { create } from 'zustand'

import { uiStorage } from '@/lib/storage'

export type ThemePreference = 'light' | 'dark' | 'system'
export type EffectiveTheme = 'light' | 'dark'

export interface UIState {
  /** Active modal id; null when none open */
  activeModal: string | null
  /** Global loading overlay */
  globalLoading: boolean
  /** User-selected theme preference */
  theme: ThemePreference
}

export interface UIActions {
  openModal: (id: string) => void
  closeModal: (id?: string) => void
  setGlobalLoading: (loading: boolean) => void
  setTheme: (theme: ThemePreference) => void
}

export type UIStore = UIState & UIActions

function readInitialState(): UIState {
  const persisted = uiStorage.read()
  return {
    activeModal: null,
    globalLoading: false,
    theme: persisted.theme,
  }
}

export const useUIStore = create<UIStore>((set) => ({
  ...readInitialState(),

  openModal: (id) => set({ activeModal: id }),

  closeModal: (id) =>
    set((state) => {
      if (id != null && state.activeModal !== id) return state
      return { activeModal: null }
    }),

  setGlobalLoading: (globalLoading) => set({ globalLoading }),

  setTheme: (theme) => {
    uiStorage.patch({ theme })
    set({ theme })
  },
}))
