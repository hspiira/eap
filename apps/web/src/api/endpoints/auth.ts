/**
 * Authentication API Endpoints
 */

import apiClient from '../client'
import type { AuthResponse, LoginRequest } from '../types'

function useAuthCookies(): boolean {
  return import.meta.env.VITE_AUTH_USE_COOKIES === 'true'
}

export const authApi = {
  /**
   * Login with email and password.
   * When using cookie auth, tokens are set by the backend via Set-Cookie; do not store in client.
   */
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>(
      '/auth/login',
      credentials
    )

    if (!useAuthCookies()) {
      if (response.access_token) {
        apiClient.setToken(response.access_token)
      }
      if (response.refresh_token) {
        apiClient.setRefreshToken(response.refresh_token)
      }
    }

    return response
  },

  /**
   * Logout: revoke refresh token on backend then clear client state.
   * With cookie auth, POST is called with credentials so backend clears cookies and revokes.
   */
  async logout(): Promise<void> {
    if (useAuthCookies()) {
      try {
        await apiClient.post<unknown>('/auth/logout', undefined)
      } catch {
        // Ignore
      }
    } else {
      const refreshToken = apiClient.getRefreshToken()
      if (refreshToken) {
        try {
          await apiClient.post<unknown>('/auth/logout', { refresh_token: refreshToken })
        } catch {
          // Ignore
        }
      }
    }
    apiClient.clearAuth()
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    if (useAuthCookies()) {
      return false
    }
    return apiClient.getToken() !== null
  },

  /**
   * Get current token
   */
  getToken(): string | null {
    return apiClient.getToken()
  },
}
