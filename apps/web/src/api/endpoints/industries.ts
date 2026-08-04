/**
 * Industries API Endpoints
 */

import apiClient from '../client'
import type { Industry, ListParams, PaginatedResponse } from '../types'

export interface IndustryCreate {
  name: string
  code?: string | null
  parent_id?: string | null
  level?: number | null
  metadata?: Record<string, unknown> | null
}

export const industriesApi = {
  async create(data: IndustryCreate): Promise<Industry> {
    return apiClient.post<Industry>('/industries', data)
  },

  async getById(industryId: string): Promise<Industry> {
    return apiClient.get<Industry>(`/industries/${industryId}`)
  },

  async list(params?: ListParams & { parent_id?: string | null }): Promise<PaginatedResponse<Industry>> {
    return apiClient.get<PaginatedResponse<Industry>>('/industries', params)
  },

  async update(industryId: string, data: Partial<IndustryCreate>): Promise<Industry> {
    return apiClient.patch<Industry>(`/industries/${industryId}`, data)
  },

  async getChildren(industryId: string): Promise<Industry[]> {
    const res = await apiClient.get<{ items: Industry[] } | Industry[]>(
      `/industries/${industryId}/children`
    )
    return Array.isArray(res) ? res : (res.items ?? [])
  },

  async activate(industryId: string): Promise<Industry> {
    return apiClient.post<Industry>(`/industries/${industryId}/activate`, {})
  },

  async deactivate(industryId: string): Promise<Industry> {
    return apiClient.post<Industry>(`/industries/${industryId}/deactivate`, {})
  },

  async checkName(name: string): Promise<{ available: boolean; name: string }> {
    return apiClient.get<{ available: boolean; name: string }>(
      `/industries/check-name/${encodeURIComponent(name)}`,
    )
  },
}
