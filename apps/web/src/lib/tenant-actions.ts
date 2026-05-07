/**
 * Tenant actions — Zustand-only flow.
 * Single place for tenant CRUD/refresh/active-selection. State lives in tenantSlice.
 */

import apiClient from '@/api/client'
import type { TenantCreate, TenantCreateResponse } from '@/api/endpoints/tenants'
import { tenantsApi } from '@/api/endpoints/tenants'
import { useAuthStore } from '@/store/slices/authSlice'
import { useEntityCacheStore } from '@/store/slices/entityCacheSlice'
import { useTenantStore } from '@/store/slices/tenantSlice'
import type { Tenant } from '@/types/entities'

function syncToApiAndStorage(tenant: Tenant | null) {
  if (tenant) {
    apiClient.setTenantId(tenant.id)
    if (typeof window !== 'undefined') {
      localStorage.setItem('current_tenant_id', tenant.id)
    }
  } else {
    apiClient.setTenantId(null)
    if (typeof window !== 'undefined') {
      localStorage.removeItem('current_tenant_id')
    }
  }
}

export const tenantActions = {
  async loadTenant(tenantId: string): Promise<void> {
    const { setLoading, setCurrentTenant } = useTenantStore.getState()
    try {
      setLoading(true)
      const tenant = await tenantsApi.getById(tenantId)
      setCurrentTenant(tenant as Tenant)
    } catch (error) {
      // Keep current_tenant_id in localStorage so we can retry on next load; only logout clears it.
      console.error('Failed to load tenant:', error)
      setCurrentTenant(null)
    } finally {
      setLoading(false)
    }
  },

  setCurrentTenant(tenant: Tenant | null): void {
    useTenantStore.getState().setCurrentTenant(tenant)
    syncToApiAndStorage(tenant)
    useEntityCacheStore.getState().invalidateAll()
  },

  async createTenant(data: TenantCreate): Promise<TenantCreateResponse> {
    const { setLoading } = useTenantStore.getState()
    try {
      setLoading(true)
      const response = await tenantsApi.create(data)
      const tenant: Tenant = {
        id: response.id,
        tenant_id: response.id,
        name: response.name,
        status: response.status as Tenant['status'],
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
      tenantActions.setCurrentTenant(tenant)
      return response
    } finally {
      setLoading(false)
    }
  },

  async refreshTenant(): Promise<void> {
    const current = useTenantStore.getState().currentTenant
    if (current) await tenantActions.loadTenant(current.id)
  },

  async refreshTenantsList(): Promise<void> {
    const { isAuthenticated, token } = useAuthStore.getState()
    if (!isAuthenticated || !token) return
    const { setLoading, setAvailableTenants } = useTenantStore.getState()
    try {
      setLoading(true)
      const response = await tenantsApi.list()
      setAvailableTenants(response.items as Tenant[])
    } catch (error) {
      console.error('Failed to load tenants list:', error)
    } finally {
      setLoading(false)
    }
  },

  clear(): void {
    useTenantStore.setState({
      currentTenant: null,
      availableTenants: [],
      isLoading: false,
    })
    syncToApiAndStorage(null)
  },
}
