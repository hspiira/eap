/**
 * Clients API Endpoints
 *
 * Client profile updates are atomic. `setTier()` stays a separate call because
 * the dedicated audit action matters; the client form invokes it after saving.
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

export interface ClientImportRowPreview {
  row: number
  name: string
  code: string | null
  aliases: string[]
  contact: string | null
  state: "new" | "duplicate" | "similar" | "invalid"
  default_action: "create" | "skip"
  matched_client_id: string | null
  matched_client_name: string | null
}

export interface ClientImportResult {
  imported: number
  skipped: number
  failed: number
  clients: Array<{ name: string; code: string }>
  issues: ClientImportIssue[]
  rows: ClientImportRowPreview[]
}

export type ClientImportDecision = {
  action: "create" | "skip" | "merge"
  client_id?: string
}

export interface ClientImportJob {
  id: string
  filename: string
  status: "queued" | "processing" | "completed" | "failed"
  file_size: number
  total_rows: number
  processed_rows: number
  imported: number
  skipped: number
  failed: number
  retry_count: number
  issues: ClientImportIssue[]
  error_message: string | null
  created_at: string
  started_at: string | null
  completed_at: string | null
}

export type { ClientCreate, ClientUpdate }
export type ClientUpdateTier = Schemas["ClientUpdateTier"]

export interface ClientListParams extends ListParams {
  tier?: ClientTier
  parent_client_id?: string
  include_archived?: boolean
}

export interface ClientSavedView {
  id: string
  tenant_id: string
  name: string
  filters: {
    search?: string | null
    tier?: ClientTier | null
    archived: boolean
    parent_client_id?: string | null
  }
  created_by: string
  is_shared: boolean
  created_at: string
  updated_at: string
}

export interface ClientDuplicateCandidate {
  first: { id: string; name: string; code: string; contact_email?: string | null }
  second: { id: string; name: string; code: string; contact_email?: string | null }
  reason: string
  similarity: number
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

  async listViews(): Promise<{ items: ClientSavedView[]; total: number }> {
    return apiClient.get<{ items: ClientSavedView[]; total: number }>("/clients/views")
  },

  async saveView(data: {
    name: string
    filters: ClientSavedView["filters"]
    is_shared: boolean
  }): Promise<ClientSavedView> {
    return apiClient.post<ClientSavedView>("/clients/views", data)
  },

  async deleteView(viewId: string): Promise<void> {
    await apiClient.delete(`/clients/views/${viewId}`)
  },

  async scanDuplicates(): Promise<{
    items: ClientDuplicateCandidate[]
    scanned: number
  }> {
    return apiClient.get("/clients/duplicates")
  },

  async mergeDuplicate(
    targetClientId: string,
    sourceClientId: string,
  ): Promise<{
    client: Client
    source_client_id: string
    transferred: Record<string, number>
    conflicts: string[]
  }> {
    return apiClient.post<{
      client: Client
      source_client_id: string
      transferred: Record<string, number>
      conflicts: string[]
    }>(`/clients/${targetClientId}/merge`, {
      source_client_id: sourceClientId,
    })
  },

  async importCsv(
    file: File,
    dryRun = false,
    decisions?: Record<number, ClientImportDecision>,
  ): Promise<ClientImportResult> {
    const formData = new FormData()
    formData.append("file", file)
    if (decisions) formData.append("decisions_json", JSON.stringify(decisions))
    return apiClient.postFormData<ClientImportResult>(
      `/clients/import?dry_run=${String(dryRun)}`,
      formData,
    )
  },

  async queueImport(
    file: File,
    decisions?: Record<number, ClientImportDecision>,
  ): Promise<ClientImportJob> {
    const formData = new FormData()
    formData.append("file", file)
    if (decisions) formData.append("decisions_json", JSON.stringify(decisions))
    return apiClient.postFormData<ClientImportJob>("/clients/import/jobs", formData)
  },

  async getImportJob(jobId: string): Promise<ClientImportJob> {
    return apiClient.get<ClientImportJob>(`/clients/import/jobs/${jobId}`)
  },

  async listImportJobs(): Promise<{ items: ClientImportJob[]; total: number }> {
    return apiClient.get<{ items: ClientImportJob[]; total: number }>("/clients/import/jobs")
  },

  async retryImport(jobId: string): Promise<ClientImportJob> {
    return apiClient.post<ClientImportJob>(`/clients/import/jobs/${jobId}/retry`)
  },

  async getImportTemplate(): Promise<Blob> {
    return apiClient.getBlob("/clients/import/template")
  },

  async exportCsv(params?: Omit<ClientListParams, "page" | "limit">): Promise<Blob> {
    return apiClient.getBlob("/clients/export", params)
  },

  async exportSelected(clientIds: string[]): Promise<Blob> {
    return apiClient.getBlob("/clients/export", { client_ids: clientIds })
  },

  async updateTags(
    clientId: string,
    tagIds: string[],
    mode: "add" | "remove" | "replace" = "replace",
  ): Promise<unknown> {
    return apiClient.put(`/clients/${clientId}/tags`, { tag_ids: tagIds, mode })
  },

  async bulkUpdateTags(
    clientIds: string[],
    tagIds: string[],
    mode: "add" | "remove" | "replace" = "add",
  ): Promise<{ clients_updated: number; tags_applied: number }> {
    return apiClient.post("/clients/bulk/tags", { client_ids: clientIds, tag_ids: tagIds, mode })
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
