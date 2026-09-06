/**
 * Provider affiliations API.
 *
 * An affiliation records the period during which a practitioner represents an
 * organisation. Its interval is start-inclusive and end-exclusive: it covers
 * `valid_from <= t < valid_until`, and a null `valid_until` is open-ended.
 *
 * A practitioner may hold concurrent affiliations with different
 * organisations. Two affiliations for the same practitioner and organisation
 * may not overlap. The practitioner and organisation of an existing
 * affiliation cannot be repointed, so only `valid_until` is editable.
 */

import type { ProviderAffiliation } from "@/types/entities"

import apiClient from "../client"
import type { ListParams, PaginatedResponse } from "../types"

export interface ProviderAffiliationListParams extends ListParams {
  provider_id?: string
  organisation_id?: string
  /** A date, not a datetime. Applies the end-exclusive rule server-side. */
  valid_at?: string
  /** Include affiliations whose interval has already ended. */
  include_ended?: boolean
}

export interface ProviderAffiliationCreateRequest {
  provider_id: string
  valid_from: string
  valid_until?: string | null
}

export const providerAffiliationsApi = {
  async list(
    params: ProviderAffiliationListParams = {},
  ): Promise<PaginatedResponse<ProviderAffiliation>> {
    return apiClient.get<PaginatedResponse<ProviderAffiliation>>("/provider-affiliations", params)
  },

  async create(
    organisationId: string,
    data: ProviderAffiliationCreateRequest,
  ): Promise<ProviderAffiliation> {
    return apiClient.post<ProviderAffiliation>(
      `/provider-organisations/${organisationId}/affiliations`,
      data,
    )
  },

  /** Only the end of the interval is editable. */
  async setValidUntil(id: string, validUntil: string | null): Promise<ProviderAffiliation> {
    return apiClient.patch<ProviderAffiliation>(`/provider-affiliations/${id}`, {
      valid_until: validUntil,
    })
  },
}
