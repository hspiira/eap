/**
 * Tenant Context
 * Provides tenant state and management throughout the application
 */

import { createContext, useContext, useState, useEffect, ReactNode } from 'react'
import { useAuth } from './AuthContext'
import { tenantsApi } from '@/api/endpoints/tenants'
import apiClient from '@/api/client'
import type { Tenant, TenantCreate, TenantCreateResponse } from '@/api/endpoints/tenants'

interface TenantContextType {
  currentTenant: Tenant | null
  availableTenants: Tenant[]
  isLoading: boolean
  setCurrentTenant: (tenant: Tenant | null) => void
  createTenant: (tenantData: TenantCreate) => Promise<TenantCreateResponse>
  refreshTenant: () => Promise<void>
  refreshTenantsList: () => Promise<void>
}

const TenantContext = createContext<TenantContextType | undefined>(undefined)

export function TenantProvider({ children }: { children: ReactNode }) {
  const { isAuthenticated, token } = useAuth()
  const [currentTenant, setCurrentTenantState] = useState<Tenant | null>(null)
  const [availableTenants, setAvailableTenants] = useState<Tenant[]>([])
  const [isLoading, setIsLoading] = useState(true)

  // Load tenant from localStorage on mount
  useEffect(() => {
    if (typeof window !== 'undefined') {
      const storedTenantId = localStorage.getItem('current_tenant_id')
      if (storedTenantId) {
        loadTenant(storedTenantId)
      } else {
        setIsLoading(false)
      }
    }
  }, [])

  // Update API client when tenant changes
  useEffect(() => {
    if (currentTenant) {
      apiClient.setTenantId(currentTenant.id)
      localStorage.setItem('current_tenant_id', currentTenant.id)
    } else {
      apiClient.setTenantId(null)
      localStorage.removeItem('current_tenant_id')
    }
  }, [currentTenant])

  // Load tenant details
  const loadTenant = async (tenantId: string) => {
    try {
      setIsLoading(true)
      const tenant = await tenantsApi.getById(tenantId)
      setCurrentTenant(tenant)
    } catch (error) {
      console.error('Failed to load tenant:', error)
      // Clear invalid tenant
      setCurrentTenant(null)
      localStorage.removeItem('current_tenant_id')
    } finally {
      setIsLoading(false)
    }
  }

  // Set current tenant
  const setCurrentTenant = (tenant: Tenant | null) => {
    setCurrentTenantState(tenant)
    if (tenant) {
      apiClient.setTenantId(tenant.id)
      localStorage.setItem('current_tenant_id', tenant.id)
    } else {
      apiClient.setTenantId(null)
      localStorage.removeItem('current_tenant_id')
    }
  }

  // Create new tenant (returns tenant + admin password)
  const createTenant = async (tenantData: TenantCreate): Promise<TenantCreateResponse> => {
    try {
      setIsLoading(true)
      const response = await tenantsApi.create(tenantData)
      
      // Convert response to Tenant format and set as current
      // The response structure from the API matches TenantCreateResponse
      const tenant: Tenant = {
        id: response.id,
        tenant_id: response.id, // For multi-tenant context
        name: response.name,
        status: response.status as any,
        created_at: new Date().toISOString(),
        updated_at: new Date().toISOString(),
      }
      setCurrentTenant(tenant)
      
      return response
    } catch (error) {
      throw error
    } finally {
      setIsLoading(false)
    }
  }

  // Refresh current tenant details
  const refreshTenant = async () => {
    if (currentTenant) {
      await loadTenant(currentTenant.id)
    }
  }

  // Refresh list of available tenants
  const refreshTenantsList = async () => {
    if (!isAuthenticated) {
      return
    }

    try {
      setIsLoading(true)
      const response = await tenantsApi.list()
      setAvailableTenants(response.items)
    } catch (error) {
      console.error('Failed to load tenants list:', error)
    } finally {
      setIsLoading(false)
    }
  }

  // Load available tenants when authenticated
  useEffect(() => {
    if (isAuthenticated && token) {
      refreshTenantsList()
    }
  }, [isAuthenticated, token])

  // Note: createTenant can be called without authentication
  // The backend should allow public tenant creation

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
