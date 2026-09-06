/**
 * Provider organisations API.
 *
 * A provider organisation is a supplier firm with its own identity and
 * approval status. It is never a practitioner and never a login. An
 * organisation is not deleted, because affiliations and past sessions
 * reference it; it is deactivated instead.
 *
 * `is_active` and `approval_status` are independent and neither is patchable.
 * They move only through the reason-carrying commands below.
 */

import type { ProviderOrganisation } from "@/types/entities"
import type { ProviderApprovalStatus } from "@/types/enums"

import apiClient from "../client"
import type { ListParams, PaginatedResponse } from "../types"

export interface ProviderOrganisationListParams extends ListParams {
  /** Free text over name and registration number. */
  search?: string
  is_active?: boolean
  approval_status?: ProviderApprovalStatus
}

export interface ProviderOrganisationInput {
  name?: string
  registration_number?: string | null
  contact_email?: string | null
  contact_phone?: string | null
}

export interface ProviderOrganisationCreateRequest extends ProviderOrganisationInput {
  name: string
}

type Command = "approve" | "suspend" | "revoke" | "deactivate" | "reactivate"

export const providerOrganisationsApi = {
  async list(
    params: ProviderOrganisationListParams = {},
  ): Promise<PaginatedResponse<ProviderOrganisation>> {
    return apiClient.get<PaginatedResponse<ProviderOrganisation>>("/provider-organisations", params)
  },

  async getById(id: string): Promise<ProviderOrganisation> {
    return apiClient.get<ProviderOrganisation>(`/provider-organisations/${id}`)
  },

  async create(data: ProviderOrganisationCreateRequest): Promise<ProviderOrganisation> {
    return apiClient.post<ProviderOrganisation>("/provider-organisations", data)
  },

  async update(id: string, data: ProviderOrganisationInput): Promise<ProviderOrganisation> {
    return apiClient.patch<ProviderOrganisation>(`/provider-organisations/${id}`, data)
  },

  /** Admin-only lifecycle command. The reason must not be blank. */
  async runCommand(id: string, command: Command, reason: string): Promise<ProviderOrganisation> {
    return apiClient.post<ProviderOrganisation>(`/provider-organisations/${id}/${command}`, {
      reason,
    })
  },
}
