/**
 * Tenant Context
 * Provides tenant state and management. Uses Zustand tenant store as source of truth.
 */

import { createContext, useContext, useEffect, useCallback, ReactNode } from 'react'
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

const TenantContext = createContext<TenantContextType | undefined>(undefined)

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
  const { isAuthenticated, token } = useAuth()
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
        if (typeof window !== 'undefined') localStorage.removeItem('current_tenant_id')
      } finally {
        setLoading(false)
      }
    },
    [setStoreTenant, setLoading]
  )

  useEffect(() => {
    if (typeof window === 'undefined') return
    const storedTenantId = localStorage.getItem('current_tenant_id')
    if (storedTenantId) {
      loadTenant(storedTenantId)
    } else {
      setLoading(false)
    }
  }, [loadTenant, setLoading])

  useEffect(() => {
    syncTenantToApiAndStorage(currentTenant)
  }, [currentTenant])

  const setCurrentTenant = useCallback(
    (tenant: TenantEntity | null) => {
      setStoreTenant(tenant)
      syncTenantToApiAndStorage(tenant)
      invalidateAll()
    },
    [setStoreTenant, invalidateAll]
  )

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

  useEffect(() => {
    if (isAuthenticated && token) {
      refreshTenantsList()
    }
  }, [isAuthenticated, token, refreshTenantsList])

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

export function useTenant() {
  const context = useContext(TenantContext)
  if (context === undefined) {
    throw new Error('useTenant must be used within a TenantProvider')
  }
  return context
}
