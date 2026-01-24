/**
 * Clients API Endpoints
 */

import apiClient from '../client'
import type { Client, ClientTag, PaginatedResponse, ListParams } from '../types'

export interface ClientCreate {
  name: string
  industry_id?: string | null
  tax_id?: string | null
  registration_number?: string | null
  address?: {
    street?: string | null
    city?: string | null
    state?: string | null
    postal_code?: string | null
    country?: string | null
  } | null
  contact_info?: {
    email?: string | null
    phone?: string | null
    mobile?: string | null
    preferred_method?: string | null
  } | null
  parent_client_id?: string | null
  metadata?: Record<string, unknown> | null
}

export const clientsApi = {
  /**
   * Create a new client
   */
  async create(clientData: ClientCreate): Promise<Client> {
    return apiClient.post<Client>('/clients', clientData)
  },

  /**
   * Get client by ID
   */
  async getById(clientId: string): Promise<Client> {
    return apiClient.get<Client>(`/clients/${clientId}`)
  },

  /**
   * List clients
   */
  async list(params?: ListParams): Promise<PaginatedResponse<Client>> {
    return apiClient.get<PaginatedResponse<Client>>('/clients', params as Record<string, unknown>)
  },

  /**
   * Update client
   */
  async update(clientId: string, data: Partial<ClientCreate>): Promise<Client> {
    return apiClient.patch<Client>(`/clients/${clientId}`, data)
  },

  /**
   * Get tags assigned to a client
   */
  async getTags(clientId: string): Promise<ClientTag[]> {
    const res = await apiClient.get<{ items: ClientTag[] } | ClientTag[]>(`/clients/${clientId}/tags`)
    return Array.isArray(res) ? res : (res.items ?? [])
  },
}
