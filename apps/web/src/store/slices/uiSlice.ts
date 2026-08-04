/**
 * UI store slice — global UI state (theme).
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
  /** User-selected theme preference */
  theme: ThemePreference
}

export interface UIActions {
  setTheme: (theme: ThemePreference) => void
}

export type UIStore = UIState & UIActions

function readInitialState(): UIState {
  const persisted = uiStorage.read()
  return {
    theme: persisted.theme,
  }
}

export const useUIStore = create<UIStore>((set) => ({
  ...readInitialState(),

  setTheme: (theme) => {
    uiStorage.patch({ theme })
    set({ theme })
  },
}))
