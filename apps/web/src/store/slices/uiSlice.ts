/**
 * UI store slice
 * Global UI state: modals, loading indicators, etc.
 */

import { create } from 'zustand'

export interface UIState {
  /** Active modal id; null when none open */
  activeModal: string | null
  /** Global loading overlay */
  globalLoading: boolean
}

export interface UIActions {
  openModal: (id: string) => void
  closeModal: (id?: string) => void
  setGlobalLoading: (loading: boolean) => void
}

export type UIStore = UIState & UIActions

const initialState: UIState = {
  activeModal: null,
  globalLoading: false,
}

export const useUIStore = create<UIStore>((set) => ({
  ...initialState,

  openModal: (id) => set({ activeModal: id }),

  closeModal: (id) =>
    set((state) => {
      if (id != null && state.activeModal !== id) return state
      return { activeModal: null }
    }),

  setGlobalLoading: (globalLoading) => set({ globalLoading }),
}))
