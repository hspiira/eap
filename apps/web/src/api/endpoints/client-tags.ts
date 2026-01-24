/**
 * Client Tags API Endpoints
 */

import apiClient from '../client'
import type { ClientTag, Client, PaginatedResponse, ListParams } from '../types'

export interface ClientTagCreate {
  name: string
  color?: string | null
  description?: string | null
  metadata?: Record<string, unknown> | null
}

export const clientTagsApi = {
  async create(data: ClientTagCreate): Promise<ClientTag> {
    return apiClient.post<ClientTag>('/client-tags', data)
  },

  async getById(tagId: string): Promise<ClientTag> {
    return apiClient.get<ClientTag>(`/client-tags/${tagId}`)
  },

  async list(params?: ListParams): Promise<PaginatedResponse<ClientTag>> {
    return apiClient.get<PaginatedResponse<ClientTag>>('/client-tags', params as Record<string, unknown>)
  },

  async update(tagId: string, data: Partial<ClientTagCreate>): Promise<ClientTag> {
    return apiClient.patch<ClientTag>(`/client-tags/${tagId}`, data)
  },

  async assign(tagId: string, clientId: string): Promise<unknown> {
    return apiClient.post<unknown>(`/client-tags/${tagId}/assign`, { client_id: clientId })
  },

  async unassign(tagId: string, clientId: string): Promise<void> {
    await apiClient.delete(`/client-tags/${tagId}/assign/${clientId}`)
  },

  async getAssignedClients(tagId: string): Promise<Client[]> {
    const res = await apiClient.get<{ items: Client[] } | Client[]>(`/client-tags/${tagId}/clients`)
    return Array.isArray(res) ? res : (res.items ?? [])
  },
}
