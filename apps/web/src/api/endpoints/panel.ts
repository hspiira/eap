/**
 * Provider Panel API.
 *
 * Mirrors BE `app/api/routes/panel.py`. Operates on persons whose
 * `person_type === ServiceProvider` and who have a `provider_profile`.
 */

import type { PanelStatus, ProviderTier } from '@/types/enums'

import apiClient from '../client'

export interface BulkPanelStatusUpdate {
  provider_ids: string[]
  new_status: PanelStatus
  reason: string
}

export interface BulkPanelStatusResponse {
  updated: string[]
  skipped_no_change: string[]
  not_found: string[]
  not_provider: string[]
  updated_count: number
  requested_count: number
}

export interface TierChangeRequest {
  new_tier: ProviderTier
  reason: string
}

export interface TierChangeResponse {
  provider_id: string
  new_tier: ProviderTier
}

export interface ProviderEligibilityResponse {
  provider_id: string
  client_id: string | null
  panel_eligible: boolean
  binding_non_compete_count: number
  binding_non_compete_ids: string[]
  eligible: boolean
  reasons: string[]
}

export const panelApi = {
  /** Audit-trailed bulk panel-status update (supports the 80→8 cull). */
  async bulkUpdateStatus(data: BulkPanelStatusUpdate): Promise<BulkPanelStatusResponse> {
    return apiClient.patch<BulkPanelStatusResponse>('/panel/bulk-panel-status', data)
  },

  /** Audited tier change for a single provider. */
  async changeTier(providerId: string, data: TierChangeRequest): Promise<TierChangeResponse> {
    return apiClient.patch<TierChangeResponse>(`/panel/${providerId}/tier`, data)
  },

  /**
   * Pre-assignment eligibility check. `clientId` scopes the check to non-competes
   * bound to that client; omit it for a panel-only check.
   */
  async checkEligibility(
    providerId: string,
    clientId?: string,
  ): Promise<ProviderEligibilityResponse> {
    return apiClient.get<ProviderEligibilityResponse>(
      `/panel/${providerId}/eligibility`,
      clientId ? { client_id: clientId } : undefined,
    )
  },
}
