/**
 * Auth actions and init — ui.timeline-style flow.
 * Single place for login, logout, initAuth; state lives in authSlice.
 */

import apiClient from '@/api/client'
import { authApi } from '@/api/endpoints/auth'
import { tenantsApi } from '@/api/endpoints/tenants'
import type { LoginRequest } from '@/api/types'
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
          console.error('[auth] Could not resolve tenant by code after login:', e)
          useAuthStore.getState().setError('Tenant lookup failed — your workspace context may be incomplete. Please refresh.')
        }
      }
      if (tenantId) {
        apiClient.setTenantId(tenantId)
        try {
          const tenant = await tenantsApi.getById(tenantId)
          useTenantStore.getState().setCurrentTenant(tenant as Tenant)
        } catch (e) {
          console.error('[auth] Could not load tenant details after login:', e)
          useAuthStore.getState().setError('Could not load workspace details — please refresh the page.')
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

  /**
   * Hydrate auth + tenant state from server-set cookies after Azure SSO callback.
   * The BE has already set HttpOnly cookies on this domain; we call /auth/me to
   * resolve who we are, then load the tenant.
   */
  async bootstrapFromCookies(): Promise<void> {
    const { setAuth, setLoading, setError, clearAuth } = useAuthStore.getState()
    setLoading(true)
    setError(null)
    try {
      const me = await authApi.me()
      setAuth(null, me.user_id, me.email)
      apiClient.setTenantId(me.tenant_id)
      try {
        const tenant = await tenantsApi.getById(me.tenant_id)
        useTenantStore.getState().setCurrentTenant(tenant as Tenant)
      } catch (e) {
        console.error('[auth] Could not load tenant after Azure SSO:', e)
        setError('Signed in, but workspace details failed to load. Please refresh.')
      }
      useAuthStore.getState().setLoading(false)
    } catch (error) {
      clearAuth()
      const message = error instanceof Error ? error.message : 'Sign-in failed'
      setError(message)
      useAuthStore.getState().setLoading(false)
      throw error
    }
  },

  async logout(): Promise<void> {
    try {
      await authApi.logout()
    } catch (_err) {
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
    const auth = useAuthStore.getState()

    if (useAuthCookies()) {
      const valid = await apiClient.validateSession()
      if (!valid) {
        auth.clearAuth()
        auth.setLoading(false)
        return
      }
      auth.setAuth(null, auth.user_id, auth.email)
      auth.setLoading(false)
      return
    }

    const token = auth.token
    if (!token) {
      auth.setLoading(false)
      return
    }
    auth.setAuth(token, auth.user_id, auth.email)
    auth.setLoading(false)
  },

  clearError(): void {
    useAuthStore.getState().clearError()
  },
}
