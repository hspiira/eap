/**
 * Services API Endpoints
 */

import apiClient from '../client'
import type { Service, PaginatedResponse, ListParams } from '../types'
import type { BaseStatus } from '@/types/enums'

export interface ServiceCreate {
  name: string
  description?: string | null
  service_type?: string | null
  category?: string | null
  duration_minutes?: number | null
  group_settings?: {
    max_group_size?: number | null
    min_group_size?: number | null
    allow_group_sessions?: boolean
  } | null
  metadata?: Record<string, unknown> | null
}

export interface GroupSettingsUpdate {
  max_group_size?: number | null
  min_group_size?: number | null
  allow_group_sessions?: boolean
}

export const servicesApi = {
  /**
   * Create a new service
   */
  async create(serviceData: ServiceCreate): Promise<Service> {
    return apiClient.post<Service>('/services', serviceData)
  },

  /**
   * Get service by ID
   */
  async getById(serviceId: string): Promise<Service> {
    return apiClient.get<Service>(`/services/${serviceId}`)
  },

  /**
   * List services
   */
  async list(params?: ListParams): Promise<PaginatedResponse<Service>> {
    return apiClient.get<PaginatedResponse<Service>>('/services', params as Record<string, unknown>)
  },

  /**
   * Update service
   */
  async update(serviceId: string, data: Partial<ServiceCreate>): Promise<Service> {
    return apiClient.patch<Service>(`/services/${serviceId}`, data)
  },

  /**
   * Activate service
   */
  async activate(serviceId: string): Promise<Service> {
    return apiClient.post<Service>(`/services/${serviceId}/activate`, {})
  },

  /**
   * Deactivate service
   */
  async deactivate(serviceId: string): Promise<Service> {
    return apiClient.post<Service>(`/services/${serviceId}/deactivate`, {})
  },

  /**
   * Archive service
   */
  async archive(serviceId: string): Promise<Service> {
    return apiClient.post<Service>(`/services/${serviceId}/archive`, {})
  },

  /**
   * Restore service from archive
   */
  async restore(serviceId: string): Promise<Service> {
    return apiClient.post<Service>(`/services/${serviceId}/restore`, {})
  },

  /**
   * Update group settings
   */
  async updateGroupSettings(serviceId: string, settings: GroupSettingsUpdate): Promise<Service> {
    return apiClient.patch<Service>(`/services/${serviceId}/group-settings`, settings)
  },
}
