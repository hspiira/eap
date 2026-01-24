/**
 * Tenant store slice
 * Single source of truth for tenant state.
 * TenantContext syncs with this store (read/write).
 */

import { create } from 'zustand'
import type { Tenant } from '@/types/entities'

export interface TenantState {
  currentTenant: Tenant | null
  availableTenants: Tenant[]
  isLoading: boolean
}

export interface TenantActions {
  setCurrentTenant: (tenant: Tenant | null) => void
  setAvailableTenants: (tenants: Tenant[]) => void
  setLoading: (loading: boolean) => void
}

export type TenantStore = TenantState & TenantActions

const initialState: TenantState = {
  currentTenant: null,
  availableTenants: [],
  isLoading: true,
}

export const useTenantStore = create<TenantStore>((set) => ({
  ...initialState,

  setCurrentTenant: (currentTenant) => set({ currentTenant }),

  setAvailableTenants: (availableTenants) => set({ availableTenants }),

  setLoading: (isLoading) => set({ isLoading }),
}))
