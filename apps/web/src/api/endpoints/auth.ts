/**
 * Authentication API Endpoints
 *
 * Two sign-in paths supported by the backend:
 *  - Password: POST /auth/login (tenant_code + email + password)
 *  - Azure AD: GET /auth/azure/login → 302 to Microsoft → callback sets cookies on FE domain
 */

import apiClient from '../client'
import type { AuthResponse, LoginRequest } from '../types'

function useAuthCookies(): boolean {
  return import.meta.env.VITE_AUTH_USE_COOKIES === 'true'
}

function azureSsoEnabled(): boolean {
  return import.meta.env.VITE_AZURE_SSO_ENABLED === 'true'
}

function apiBaseUrl(): string {
  return (import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000').replace(/\/$/, '')
}

export interface MeResponse {
  user_id: string
  tenant_id: string
  email: string
}

export const authApi = {
  /**
   * Password login (tenant_code + email + password).
   * Cookie mode: tokens set by Set-Cookie. Bearer mode: tokens stored client-side.
   */
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>('/auth/login', credentials)

    if (!useAuthCookies()) {
      if (response.access_token) apiClient.setToken(response.access_token, response.expires_in)
      if (response.refresh_token) apiClient.setRefreshToken(response.refresh_token)
    } else {
      const csrf = (response as AuthResponse & { csrf_token?: string }).csrf_token
      if (typeof csrf === 'string') apiClient.setCsrfToken(csrf)
    }

    return response
  },

  /**
   * Best-effort logout. Server revokes refresh token; client always tears down state.
   */
  async logout(): Promise<void> {
    if (useAuthCookies()) {
      try {
        await apiClient.post<unknown>('/auth/logout', undefined)
      } catch (_err) {
        // ignore — client clears state below
      }
    } else {
      const refreshToken = apiClient.getRefreshToken()
      if (refreshToken) {
        try {
          await apiClient.post<unknown>('/auth/logout', { refresh_token: refreshToken })
        } catch (_err) {
          // ignore
        }
      }
    }
    apiClient.clearAuth()
  },

  isAuthenticated(): boolean {
    if (useAuthCookies()) return false
    return apiClient.getToken() !== null
  },

  getToken(): string | null {
    return apiClient.getToken()
  },

  /**
   * Consume the one-time set-password link issued at tenant creation.
   */
  async setInitialPassword(data: {
    token: string
    password: string
    password_confirm: string
  }): Promise<void> {
    await apiClient.post<unknown>('/auth/set-initial-password', data)
  },

  /**
   * Get the current authenticated user from token/cookie.
   * Used to hydrate auth state after the Azure callback redirect (where cookies
   * are pre-set by the BE but the FE has no in-memory state yet).
   */
  async me(): Promise<MeResponse> {
    return apiClient.get<MeResponse>('/auth/me')
  },

  /**
   * Whether Azure SSO is enabled on this build (FE flag — BE must also be configured).
   */
  isAzureSsoEnabled(): boolean {
    return azureSsoEnabled()
  },

  /**
   * Absolute URL to the BE Azure login redirect endpoint.
   * The browser must hard-navigate here (not fetch) so Azure can perform the OAuth dance.
   */
  azureLoginUrl(): string {
    return `${apiBaseUrl()}/auth/azure/login`
  },
}
