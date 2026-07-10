/**
 * Tenant store slice — single source of truth for tenant context.
 *
 * `currentTenantId` is hydrated from localStorage at module init so the apiClient
 * can read it before AppBootstrap finishes loading the full Tenant object.
 * Setters write through to storage; apiClient should not touch storage directly.
 */

import { create } from 'zustand'

import { tenantStorage } from '@/lib/storage'
import type { Tenant } from '@/types/entities'

export interface TenantState {
  currentTenant: Tenant | null
  currentTenantId: string | null
  availableTenants: Tenant[]
  isLoading: boolean
}

export interface TenantActions {
  setCurrentTenant: (tenant: Tenant | null) => void
  setCurrentTenantId: (id: string | null) => void
  setAvailableTenants: (tenants: Tenant[]) => void
  setLoading: (loading: boolean) => void
  clear: () => void
}

export type TenantStore = TenantState & TenantActions

function readInitialState(): TenantState {
  return {
    currentTenant: null,
    currentTenantId: tenantStorage.readId(),
    availableTenants: [],
    isLoading: true,
  }
}

export const useTenantStore = create<TenantStore>((set) => ({
  ...readInitialState(),

  setCurrentTenant: (tenant) => {
    const id = tenant?.id ?? null
    tenantStorage.writeId(id)
    set({ currentTenant: tenant, currentTenantId: id })
  },

  setCurrentTenantId: (id) => {
    tenantStorage.writeId(id)
    set({ currentTenantId: id })
  },

  setAvailableTenants: (availableTenants) => set({ availableTenants }),

  setLoading: (isLoading) => set({ isLoading }),

  clear: () => {
    tenantStorage.clear()
    set({
      currentTenant: null,
      currentTenantId: null,
      availableTenants: [],
      isLoading: false,
    })
  },
}))
