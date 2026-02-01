/**
 * Authentication API Endpoints
 */

import apiClient from '../client'
import type { AuthResponse, LoginRequest } from '../types'

export const authApi = {
  /**
   * Login with email and password
   */
  async login(credentials: LoginRequest): Promise<AuthResponse> {
    const response = await apiClient.post<AuthResponse>(
      '/auth/login',
      credentials
    )
    
    if (response.access_token) {
      apiClient.setToken(response.access_token)
    }
    if (response.refresh_token) {
      apiClient.setRefreshToken(response.refresh_token)
    }

    return response
  },

  /**
   * Logout (clear token)
   */
  logout(): void {
    apiClient.clearAuth()
  },

  /**
   * Check if user is authenticated
   */
  isAuthenticated(): boolean {
    return apiClient.getToken() !== null
  },

  /**
   * Get current token
   */
  getToken(): string | null {
    return apiClient.getToken()
  },
}
