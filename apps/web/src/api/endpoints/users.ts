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
}
