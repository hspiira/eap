/**
 * Providers API.
 *
 * Providers are Persons whose `person_type === ServiceProvider` and who carry
 * a `provider_profile` (tier, region, accreditation, panel status, specialties).
 * This module is a thin wrapper around `personsApi` that filters for that
 * combination: the BE has no separate `/providers` route.
 *
 * Lifecycle and roster management live in `panel.ts` (bulk-status, tier-change,
 * eligibility) and `non-compete-clauses.ts`.
 */

import apiClient from "../client"
import type { ListParams, PaginatedResponse, Provider } from "../types"

export interface ProviderListParams extends ListParams {
  status?: string
  /** Free-text search in user email (delegated to persons.list). */
  search?: string
}

export const providersApi = {
  /**
   * List providers (Persons with type=ServiceProvider AND non-null provider_profile).
   *
   * Filtering by tier/region happens client-side here because the BE's persons
   * list filter doesn't support those fields. Future improvement: BE adds a
   * tier/region filter to `/persons?person_type=ServiceProvider`.
   */
  async list(params: ProviderListParams = {}): Promise<PaginatedResponse<Provider>> {
    return apiClient.get<PaginatedResponse<Provider>>("/providers", params)
  },

  async getById(id: string): Promise<Provider> {
    return apiClient.get<Provider>(`/providers/${id}`)
  },
}
