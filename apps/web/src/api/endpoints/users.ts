/**
 * Users API Endpoints
 */

import apiClient from '../client'
import type { User, PaginatedResponse, ListParams, CreateRequest } from '../types'

export interface UserCreate extends CreateRequest {
  email: string
  password?: string
  preferred_language?: string
  timezone?: string
}

export interface UserUpdatePasswordRequest {
  current_password: string
  password: string
}

export interface UserUpdatePreferencesRequest {
  preferred_language?: string
  timezone?: string
  date_format?: string
  week_starts_on?: string
  email_notifications?: boolean
  assignment_alerts?: boolean
  session_reminders?: boolean
  weekly_digest?: boolean
}

export interface TwoFactorSetupResponse {
  secret: string
  qr_code_url: string // Data URL or image URL
  manual_entry_key: string // For manual entry
}

export interface TwoFactorVerifyRequest {
  code: string
}

export interface TwoFactorVerifyResponse {
  verified: boolean
  recovery_codes?: string[] // Only returned on successful enable
}

export const usersApi = {
  /**
   * Create a new user
   */
  async create(userData: UserCreate): Promise<User> {
    return apiClient.post<User>('/users', userData)
  },

  /**
   * Get user by ID
   */
  async getById(userId: string): Promise<User> {
    return apiClient.get<User>(`/users/${userId}`)
  },

  /**
   * List users
   */
  async list(params?: ListParams): Promise<PaginatedResponse<User>> {
    return apiClient.get<PaginatedResponse<User>>('/users', params)
  },

  /**
   * Update user password
   */
  async updatePassword(userId: string, data: UserUpdatePasswordRequest): Promise<void> {
    return apiClient.patch<void>(`/users/${userId}/password`, data)
  },

  /**
   * Update user preferences (language, timezone)
   */
  async updatePreferences(userId: string, data: UserUpdatePreferencesRequest): Promise<User> {
    return apiClient.patch<User>(`/users/${userId}/preferences`, data)
  },

  /**
   * Setup 2FA - Get QR code and secret
   */
  async setup2FA(userId: string): Promise<TwoFactorSetupResponse> {
    return apiClient.post<TwoFactorSetupResponse>(`/users/${userId}/setup-2fa`, {})
  },

  /**
   * Verify 2FA code and enable 2FA
   */
  async verify2FA(userId: string, data: TwoFactorVerifyRequest): Promise<TwoFactorVerifyResponse> {
    return apiClient.post<TwoFactorVerifyResponse>(`/users/${userId}/verify-2fa`, data)
  },

  /**
   * Enable 2FA (after verification)
   */
  async enable2FA(userId: string): Promise<void> {
    return apiClient.post<void>(`/users/${userId}/enable-2fa`, {})
  },

  /**
   * Disable 2FA
   */
  async disable2FA(userId: string): Promise<void> {
    return apiClient.post<void>(`/users/${userId}/disable-2fa`, {})
  },
}
