/**
 * Auth actions and init — ui.timeline-style flow.
 * Single place for login, logout, initAuth; state lives in authSlice.
 */

import apiClient from '@/api/client'
import { authApi } from '@/api/endpoints/auth'
import { tenantsApi } from '@/api/endpoints/tenants'
import type { LoginRequest } from '@/api/types'
import { authStorage } from '@/lib/storage'
import { useAuthStore } from '@/store/slices/authSlice'
import { useTenantStore } from '@/store/slices/tenantSlice'
import type { Tenant } from '@/types/entities'

function useAuthCookies(): boolean {
  return import.meta.env.VITE_AUTH_USE_COOKIES === 'true'
}

export const authActions = {
  async login(credentials: LoginRequest): Promise<void> {
    const { setAuth, setLoading, setError, clearAuth } = useAuthStore.getState()
    setLoading(true)
    setError(null)

    try {
      const response = await authApi.login(credentials)
      if (useAuthCookies()) {
        setAuth(null, response.user_id, response.email)
      } else {
        setAuth(response.access_token, response.user_id, response.email)
      }
      let tenantId = response.tenant_id
      if (!tenantId && credentials.tenant_code) {
        try {
          const { items } = await tenantsApi.list()
          const tenant = items.find(
            (t: Tenant) => t.code?.toLowerCase() === credentials.tenant_code?.toLowerCase()
          )
          if (tenant) tenantId = tenant.id
        } catch (e) {
          console.warn('Could not resolve tenant by code after login:', e)
        }
      }
      if (tenantId) {
        apiClient.setTenantId(tenantId)
        try {
          const tenant = await tenantsApi.getById(tenantId)
          useTenantStore.getState().setCurrentTenant(tenant as Tenant)
        } catch (e) {
          console.warn('Could not load tenant details after login:', e)
        }
      }
      useAuthStore.getState().setLoading(false)
    } catch (error) {
      clearAuth()
      const message =
        error instanceof Error ? error.message : 'Login failed'
      setError(message)
      useAuthStore.getState().setLoading(false)
      throw error
    }
  },

  async logout(): Promise<void> {
    try {
      await authApi.logout()
    } catch {
      // server-side logout is best-effort; always tear down client state
    }
    apiClient.clearAuth()
    useAuthStore.getState().clearAuth()
    useTenantStore.setState({
      currentTenant: null,
      availableTenants: [],
      isLoading: false,
    })
  },

  async initAuth(): Promise<void> {
    const persisted = authStorage.read()
    // apiClient already restores tenantId from storage at module init.

    if (useAuthCookies()) {
      const valid = await apiClient.validateSession()
      if (!valid) {
        useAuthStore.getState().clearAuth()
        useAuthStore.getState().setLoading(false)
        return
      }
      useAuthStore.getState().setAuth(null, persisted.user_id, persisted.email)
      useAuthStore.getState().setLoading(false)
      return
    }

    const token = apiClient.getToken()
    if (!token) {
      useAuthStore.getState().setLoading(false)
      return
    }
    useAuthStore.getState().setAuth(token, persisted.user_id, persisted.email)
    useAuthStore.getState().setLoading(false)
  },

  clearError(): void {
    useAuthStore.getState().clearError()
  },
}
