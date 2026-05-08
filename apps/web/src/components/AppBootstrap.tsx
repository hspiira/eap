/**
 * AppBootstrap — replaces AuthProvider + TenantProvider.
 * Mounted once near the root. Owns:
 *  - one-shot auth hydrate from localStorage
 *  - apiClient 401 callback → store clear + redirect to /auth/login
 *  - tenant restore-on-auth and clear-on-logout side effects
 */

import { useEffect } from 'react'

import { useNavigate } from '@tanstack/react-router'

import apiClient from '@/api/client'
import { authActions } from '@/lib/auth-store'
import { tenantStorage } from '@/lib/storage'
import { tenantActions } from '@/lib/tenant-actions'
import { useAuthStore } from '@/store/slices/authSlice'
import { useTenantStore } from '@/store/slices/tenantSlice'

const AUTH_PAGES = new Set(['/auth/login', '/auth/signup', '/auth/set-password'])

export function AppBootstrap() {
  const navigate = useNavigate()
  const isAuthenticated = useAuthStore((s) => s.isAuthenticated)
  const authLoading = useAuthStore((s) => s.isLoading)
  const token = useAuthStore((s) => s.token)
  const currentTenant = useTenantStore((s) => s.currentTenant)

  useEffect(() => {
    authActions.initAuth()
  }, [])

  useEffect(() => {
    apiClient.setAuthErrorCallback(() => {
      useAuthStore.getState().clearAuth()
      const path = typeof window !== 'undefined' ? window.location.pathname : '/'
      const redirect = path && !AUTH_PAGES.has(path) ? path : undefined
      navigate({
        to: '/auth/login',
        search: { tenant_code: undefined, email: undefined, redirect },
        replace: true,
      })
    })
    return () => apiClient.setAuthErrorCallback(null)
  }, [navigate])

  // Restore current tenant by ID after auth is hydrated. No list fetch on bootstrap.
  useEffect(() => {
    if (authLoading || !isAuthenticated || !token) return
    const storedTenantId = tenantStorage.readId()
    if (storedTenantId && !currentTenant) {
      tenantActions.loadTenant(storedTenantId)
    } else if (!storedTenantId) {
      useTenantStore.setState({ isLoading: false })
    }
  }, [authLoading, isAuthenticated, token, currentTenant])

  // Clear tenant state when user logs out. Skip during initial auth hydrate
  // (isAuthenticated is false before token is restored from localStorage).
  useEffect(() => {
    if (authLoading || isAuthenticated) return
    tenantActions.clear()
  }, [authLoading, isAuthenticated])

  return null
}
