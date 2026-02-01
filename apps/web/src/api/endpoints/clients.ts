/**
 * Clients API Endpoints
 */

import apiClient from '../client'
import type {
  Client,
  ClientTag,
  ClientContactInfo,
  ClientBillingAddress,
  ClientStats,
  PaginatedResponse,
  ListParams,
} from '../types'

export interface ClientCreate {
  name: string
  code: string // Required, 3-5 chars
  contact_info: ClientContactInfo
  billing_address?: ClientBillingAddress | null
  industry_id?: string | null
  parent_client_id?: string | null
  preferred_contact_method?: string | null
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
   * Update contact info only
   */
  async updateContactInfo(clientId: string, data: ClientContactInfo): Promise<Client> {
    return apiClient.patch<Client>(`/clients/${clientId}/contact-info`, data)
  },

  /**
   * Update billing address only
   */
  async updateBillingAddress(clientId: string, data: ClientBillingAddress): Promise<Client> {
    return apiClient.patch<Client>(`/clients/${clientId}/billing-address`, data)
  },

  /**
   * Mark client as verified (backend requires verified_by query param = current user ID)
   */
  async verify(clientId: string, verifiedBy: string): Promise<Client> {
    return apiClient.post<Client>(
      `/clients/${clientId}/verify?verified_by=${encodeURIComponent(verifiedBy)}`
    )
  },

  /**
   * Activate client (requires contact_info)
   */
  async activate(clientId: string): Promise<Client> {
    return apiClient.post<Client>(`/clients/${clientId}/activate`)
  },

  /**
   * Deactivate client
   */
  async deactivate(clientId: string, reason?: string): Promise<Client> {
    return apiClient.post<Client>(`/clients/${clientId}/deactivate`, reason != null ? { reason } : undefined)
  },

  /**
   * Suspend client (reason required)
   */
  async suspend(clientId: string, reason: string): Promise<Client> {
    return apiClient.post<Client>(`/clients/${clientId}/suspend`, { reason })
  },

  /**
   * Terminate client (reason required, permanent)
   */
  async terminate(clientId: string, reason: string): Promise<Client> {
    return apiClient.post<Client>(`/clients/${clientId}/terminate`, { reason })
  },

  /**
   * Soft archive client
   */
  async archive(clientId: string): Promise<Client> {
    return apiClient.post<Client>(`/clients/${clientId}/archive`)
  },

  /**
   * Restore client from archive
   */
  async restore(clientId: string): Promise<Client> {
    return apiClient.post<Client>(`/clients/${clientId}/restore`)
  },

  /**
   * Get client stats (child count, contracts, verification)
   */
  async getStats(clientId: string): Promise<ClientStats> {
    return apiClient.get<ClientStats>(`/clients/${clientId}/stats`)
  },

  /**
   * Get paginated child clients
   */
  async getChildren(
    clientId: string,
    params?: ListParams
  ): Promise<PaginatedResponse<Client>> {
    return apiClient.get<PaginatedResponse<Client>>(`/clients/${clientId}/children`, params as Record<string, unknown>)
  },

  /**
   * Check client name availability
   */
  async checkNameAvailability(name: string): Promise<{ available: boolean }> {
    return apiClient.get<{ available: boolean }>(`/clients/check-name/${encodeURIComponent(name)}`)
  },

  /**
   * Get tags assigned to a client
   */
  async getTags(clientId: string): Promise<ClientTag[]> {
    const res = await apiClient.get<{ items: ClientTag[] } | ClientTag[]>(`/clients/${clientId}/tags`)
    return Array.isArray(res) ? res : (res.items ?? [])
  },
}
