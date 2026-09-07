/**
 * Practitioners API.
 *
 * A practitioner is the individual who delivers a session. `/providers` is its
 * own resource: it is not a Person, and it does not require a user account.
 *
 * General edit covers ordinary profile and contact fields only. Tier, panel
 * status, accreditation and record status move through the lifecycle commands
 * below, each of which requires a reason and is audited. Account linking is
 * separate again, and Admin-only.
 */

import type { LicenseInfo } from "@/types/entities/identity"
import type {
  AccreditationStatus,
  BaseStatus,
  PanelStatus,
  ProviderGender,
  ProviderTier,
  UgandaRegion,
} from "@/types/enums"

import apiClient from "../client"
import type { ListParams, PaginatedResponse, Provider } from "../types"

export interface ProviderListParams extends ListParams {
  /** Free text over display name and contact email. */
  search?: string
  tier?: ProviderTier[]
  region?: UgandaRegion[]
  panel_status?: PanelStatus[]
  accreditation_status?: AccreditationStatus[]
  status?: BaseStatus[]
  /** Narrow to practitioners with, or without, a linked account. */
  has_account?: boolean
}

/**
 * Fields a practitioner owns. Tier and region are required on create only.
 *
 * Specialties are not here: they are catalogue links, written through
 * `providerSpecialtiesApi`. Sending them on this path is rejected.
 */
export interface ProviderProfileInput {
  display_name?: string
  email?: string | null
  phone?: string | null
  region?: UgandaRegion
  bio?: string | null
  gender?: ProviderGender | null
  license_info?: LicenseInfo | null
}

export interface ProviderCreateRequest extends ProviderProfileInput {
  display_name: string
  tier: ProviderTier
  region: UgandaRegion
}

export const providersApi = {
  async list(params: ProviderListParams = {}): Promise<PaginatedResponse<Provider>> {
    return apiClient.get<PaginatedResponse<Provider>>("/providers", params)
  },

  async getById(id: string): Promise<Provider> {
    return apiClient.get<Provider>(`/providers/${id}`)
  },

  async create(data: ProviderCreateRequest): Promise<Provider> {
    return apiClient.post<Provider>("/providers", data)
  },

  /**
   * Partial update of ordinary fields. Omitted means unchanged and explicit
   * null clears a nullable field. Sending a lifecycle field is rejected, so
   * callers must not include those keys at all.
   */
  async update(id: string, data: ProviderProfileInput): Promise<Provider> {
    return apiClient.patch<Provider>(`/providers/${id}`, data)
  },

  async changeTier(id: string, data: { tier: ProviderTier; reason: string }): Promise<Provider> {
    return apiClient.patch<Provider>(`/providers/${id}/tier`, data)
  },

  async changePanelStatus(
    id: string,
    data: { panel_status: PanelStatus; reason: string },
  ): Promise<Provider> {
    return apiClient.patch<Provider>(`/providers/${id}/panel-status`, data)
  },

  async changeAccreditation(
    id: string,
    data: {
      accreditation_status: AccreditationStatus
      accreditation_authority?: string | null
      accreditation_expiry?: string | null
      reason: string
    },
  ): Promise<Provider> {
    return apiClient.patch<Provider>(`/providers/${id}/accreditation`, data)
  },

  async changeStatus(id: string, data: { status: BaseStatus; reason: string }): Promise<Provider> {
    return apiClient.patch<Provider>(`/providers/${id}/status`, data)
  },

  async linkAccount(id: string, data: { user_id: string; reason: string }): Promise<Provider> {
    return apiClient.post<Provider>(`/providers/${id}/account-link`, data)
  },

  async unlinkAccount(id: string, data: { reason: string }): Promise<Provider> {
    return apiClient.delete<Provider>(`/providers/${id}/account-link`, data)
  },
}
