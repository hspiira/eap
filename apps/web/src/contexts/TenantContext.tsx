/**
 * Tenant Context
 * Provides tenant state and management. Uses Zustand tenant store as source of truth.
 * @see docs/FRONTEND_DEVELOPMENT_GUIDE.md – Tenant context, GET /tenants/{tenant_id}, store tenant_id
 * @see docs/IMPLEMENTATION_PLAN.md – Phase 1.2 Tenant Context Management
 */

import { createContext, useEffect, useCallback, ReactNode } from 'react'
import { useAuth } from './AuthContext'
import { tenantsApi } from '@/api/endpoints/tenants'
import apiClient from '@/api/client'
import { useTenantStore } from '@/store/slices/tenantSlice'
import { useEntityCacheStore } from '@/store/slices/entityCacheSlice'
import type { TenantCreate, TenantCreateResponse } from '@/api/endpoints/tenants'
import type { Tenant as TenantEntity } from '@/types/entities'

interface TenantContextType {
  currentTenant: TenantEntity | null
  availableTenants: TenantEntity[]
  isLoading: boolean
  setCurrentTenant: (tenant: TenantEntity | null) => void
  createTenant: (tenantData: TenantCreate) => Promise<TenantCreateResponse>
  refreshTenant: () => Promise<void>
  refreshTenantsList: () => Promise<void>
}

export const TenantContext = createContext<TenantContextType | undefined>(undefined)

function syncTenantToApiAndStorage(tenant: TenantEntity | null) {
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

export function TenantProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated, token, isLoading: authLoading } = useAuth()
  const {
    currentTenant,
    availableTenants,
    isLoading,
    setCurrentTenant: setStoreTenant,
    setAvailableTenants,
    setLoading,
  } = useTenantStore()
  const invalidateAll = useEntityCacheStore((s) => s.invalidateAll)

  const loadTenant = useCallback(
    async (tenantId: string) => {
      try {
        setLoading(true)
        const tenant = await tenantsApi.getById(tenantId)
        setStoreTenant(tenant as TenantEntity)
      } catch (error) {
        console.error('Failed to load tenant:', error)
        setStoreTenant(null)
        // Keep current_tenant_id in localStorage so we can retry on next load; only logout clears it.
      } finally {
        setLoading(false)
      }
    },
    [setStoreTenant, setLoading]
  )

  const setCurrentTenant = useCallback(
    (tenant: TenantEntity | null) => {
      setStoreTenant(tenant)
      syncTenantToApiAndStorage(tenant)
      invalidateAll()
    },
    [setStoreTenant, invalidateAll]
  )

  useEffect(() => {
    syncTenantToApiAndStorage(currentTenant)
  }, [currentTenant])

  // Restore current tenant by ID only (see docs: GET /tenants/{tenant_id}). No list fetch on bootstrap.
  // Wait for auth to be restored from localStorage before reading current_tenant_id.
  useEffect(() => {
    if (typeof window === 'undefined' || authLoading || !isAuthenticated || !token) return
    const storedTenantId = localStorage.getItem('current_tenant_id')
    if (storedTenantId && !currentTenant) {
      loadTenant(storedTenantId)
    } else if (!storedTenantId) {
      setLoading(false)
    }
  }, [authLoading, isAuthenticated, token, currentTenant, loadTenant, setLoading])

  // Clear tenant state when user logs out. Do NOT clear during initial auth load:
  // isAuthenticated is false before token is restored from localStorage, which would
  // wipe current_tenant_id and cause "tenant lost on reload".
  useEffect(() => {
    if (authLoading || isAuthenticated) return
    setStoreTenant(null)
    setAvailableTenants([])
    setLoading(false)
    syncTenantToApiAndStorage(null)
    if (typeof window !== 'undefined') localStorage.removeItem('current_tenant_id')
  }, [authLoading, isAuthenticated, setStoreTenant, setAvailableTenants, setLoading])

  const createTenant = useCallback(
    async (tenantData: TenantCreate): Promise<TenantCreateResponse> => {
      try {
        setLoading(true)
        const response = await tenantsApi.create(tenantData)
        const tenant: TenantEntity = {
          id: response.id,
          tenant_id: response.id,
          name: response.name,
          status: response.status as TenantEntity['status'],
          created_at: new Date().toISOString(),
          updated_at: new Date().toISOString(),
        }
        setCurrentTenant(tenant)
        return response
      } finally {
        setLoading(false)
      }
    },
    [setLoading, setCurrentTenant]
  )

  const refreshTenant = useCallback(async () => {
    if (currentTenant) await loadTenant(currentTenant.id)
  }, [currentTenant, loadTenant])

  const refreshTenantsList = useCallback(async () => {
    if (!isAuthenticated || !token) return
    try {
      setLoading(true)
      const response = await tenantsApi.list()
      setAvailableTenants(response.items as TenantEntity[])
    } catch (error) {
      console.error('Failed to load tenants list:', error)
    } finally {
      setLoading(false)
    }
  }, [isAuthenticated, token, setAvailableTenants, setLoading])

  return (
    <TenantContext.Provider
      value={{
        currentTenant,
        availableTenants,
        isLoading,
        setCurrentTenant,
        createTenant,
        refreshTenant,
        refreshTenantsList,
      }}
    >
      {children}
    </TenantContext.Provider>
  )
}
