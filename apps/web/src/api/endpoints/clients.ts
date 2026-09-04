/**
 * Clients API Endpoints
 *
 * Client profile updates are atomic. `setTier()` remains available for inline
 * tier changes from the detail rail, where the dedicated audit action matters.
 */

import type { ClientCreate, ClientStatsResponse, ClientUpdate, Schemas } from "@/api/generated"
import type { ClientTier } from "@/types/enums"

import apiClient from "../client"
import type {
  Client,
  ClientBillingAddress,
  ClientContactInfo,
  ClientTag,
  ListParams,
  PaginatedResponse,
} from "../types"

export interface ClientImportIssue {
  row: number
  field?: string | null
  message: string
  severity?: "error" | "warning" | "skipped"
}

export interface ClientImportResult {
  imported: number
  skipped: number
  failed: number
  clients: Array<{ name: string; code: string }>
  issues: ClientImportIssue[]
}

export type { ClientCreate, ClientUpdate }
export type ClientUpdateTier = Schemas["ClientUpdateTier"]

export interface ClientListParams extends ListParams {
  tier?: ClientTier
  parent_client_id?: string
  include_archived?: boolean
}

export const clientsApi = {
  /**
   * Create a new client
   */
  async create(clientData: ClientCreate): Promise<Client> {
    return apiClient.post<Client>("/clients", clientData)
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
  async list(params?: ClientListParams): Promise<PaginatedResponse<Client>> {
    return apiClient.get<PaginatedResponse<Client>>("/clients", params)
  },

  async importCsv(file: File, dryRun = false): Promise<ClientImportResult> {
    const formData = new FormData()
    formData.append("file", file)
    return apiClient.postFormData<ClientImportResult>(
      `/clients/import?dry_run=${String(dryRun)}`,
      formData,
    )
  },

  async getImportTemplate(): Promise<Blob> {
    return apiClient.getBlob("/clients/import/template")
  },

  async exportCsv(params?: Omit<ClientListParams, "page" | "limit">): Promise<Blob> {
    return apiClient.getBlob("/clients/export", params)
  },

  /**
   * Update client
   */
  async update(clientId: string, data: ClientUpdate): Promise<Client> {
    return apiClient.patch<Client>(`/clients/${clientId}`, data)
  },

  /**
   * Set engagement tier. BE auditing keys off this dedicated endpoint.
   * Pass `tier: null` to clear.
   */
  async setTier(clientId: string, tier: ClientTier | null): Promise<Client> {
    return apiClient.patch<Client>(`/clients/${clientId}/tier`, { tier })
  },

  async updateAliases(clientId: string, aliases: string[]): Promise<Client> {
    return apiClient.patch<Client>(`/clients/${clientId}/aliases`, { aliases })
  },

  async mergeAliases(clientId: string, sourceClientId: string): Promise<Client> {
    return apiClient.post<Client>(`/clients/${clientId}/aliases/merge`, {
      source_client_id: sourceClientId,
    })
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
      `/clients/${clientId}/verify?verified_by=${encodeURIComponent(verifiedBy)}`,
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
    return apiClient.post<Client>(
      `/clients/${clientId}/deactivate`,
      reason != null ? { reason } : undefined,
    )
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
  async getStats(clientId: string): Promise<ClientStatsResponse> {
    return apiClient.get<ClientStatsResponse>(`/clients/${clientId}/stats`)
  },

  /**
   * Get paginated child clients
   */
  async getChildren(clientId: string, params?: ListParams): Promise<PaginatedResponse<Client>> {
    return apiClient.get<PaginatedResponse<Client>>(`/clients/${clientId}/children`, params)
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
    const res = await apiClient.get<{ items: ClientTag[] } | ClientTag[]>(
      `/clients/${clientId}/tags`,
    )
    return Array.isArray(res) ? res : (res.items ?? [])
  },
}
