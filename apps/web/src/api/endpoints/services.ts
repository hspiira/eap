/**
 * Services API Endpoints
 *
 * Shapes mirror BE OpenAPI (see `@/api/generated`).
 * `is_group_service` and `max_participants` are flat on the BE — there is no
 * `group_settings` wrapper or `min_group_size`. Group settings are configured
 * via a dedicated PATCH `/services/{id}/group-settings` route.
 */

import type { ServiceCreate, ServiceUpdate, ServiceUpdateGroupSettings } from '@/api/generated'

import apiClient from '../client'
import type { ListParams, PaginatedResponse, Service } from '../types'

export type { ServiceCreate, ServiceUpdate, ServiceUpdateGroupSettings }
/** @deprecated use `ServiceUpdateGroupSettings` from `@/api/generated`. */
export type GroupSettingsUpdate = ServiceUpdateGroupSettings

/** Mirrors the query params on `GET /services/` in the BE OpenAPI schema. */
export interface ServiceListParams extends ListParams {
  category?: string
  is_group_service?: boolean
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
  async list(params?: ServiceListParams): Promise<PaginatedResponse<Service>> {
    return apiClient.get<PaginatedResponse<Service>>('/services', params)
  },

  /**
   * Update service
   */
  async update(serviceId: string, data: ServiceUpdate): Promise<Service> {
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
