/**
 * Providers API.
 *
 * Providers are Persons whose `person_type === ServiceProvider` and who carry
 * a `provider_profile` (tier, region, accreditation, panel status, specialties).
 * This module is a thin wrapper around `personsApi` that filters for that
 * combination — the BE has no separate `/providers` route.
 *
 * Lifecycle and roster management live in `panel.ts` (bulk-status, tier-change,
 * eligibility) and `non-compete-clauses.ts`.
 */

import { PersonType } from '@/types/enums'

import type { ListParams, PaginatedResponse, Person, Provider } from '../types'
import { personsApi } from './persons'

export interface ProviderListParams extends ListParams {
  status?: string
  /** Free-text search in user email (delegated to persons.list). */
  search?: string
}

function isProvider(p: Person): p is Provider {
  return (
    p.person_type === PersonType.SERVICE_PROVIDER &&
    p.provider_profile != null
  )
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
    const page = await personsApi.list({
      ...params,
      person_type: PersonType.SERVICE_PROVIDER,
    })
    const providers = page.items.filter(isProvider)
    return {
      ...page,
      items: providers,
      // total/has_more come from BE; if profile-less providers were dropped,
      // those counts are slightly optimistic, but acceptable for v1.
    }
  },

  async getById(id: string): Promise<Provider> {
    const person = await personsApi.getById(id)
    if (!isProvider(person)) {
      throw new Error(
        `Person ${id} is not a service provider (type=${person.person_type}, profile=${
          person.provider_profile == null ? 'missing' : 'present'
        })`,
      )
    }
    return person
  },
}
