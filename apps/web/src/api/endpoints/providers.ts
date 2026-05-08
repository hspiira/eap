/**
 * Providers (D-Provider v1) API. Fixture-backed until BE Phase 2 #3 ships.
 * Toggle with `VITE_PROVIDERS_USE_FIXTURE=false` once the BE endpoint is live.
 */

import apiClient from '../client'
import type { ListParams, PaginatedResponse, Provider } from '../types'

import { providersFixture } from './providers-fixture'
import type { ProviderRegion, ProviderTier } from '@/types/enums'

export interface ProviderListParams extends ListParams {
  tier?: ProviderTier
  region?: ProviderRegion
}

function useFixture(): boolean {
  if (typeof import.meta === 'undefined') return true
  return import.meta.env?.VITE_PROVIDERS_USE_FIXTURE !== 'false'
}

function applyFilters(items: Provider[], params: ProviderListParams): Provider[] {
  let out = items
  if (params.tier) out = out.filter((p) => p.tier === params.tier)
  if (params.region) out = out.filter((p) => p.region === params.region)
  if (params.search) {
    const q = params.search.toLowerCase()
    out = out.filter(
      (p) =>
        p.name.toLowerCase().includes(q) ||
        p.region.toLowerCase().includes(q) ||
        p.accreditation.registration_number.toLowerCase().includes(q),
    )
  }
  return out
}

export const providersApi = {
  async list(params: ProviderListParams = {}): Promise<PaginatedResponse<Provider>> {
    if (useFixture()) {
      const filtered = applyFilters(providersFixture, params)
      const page = params.page ?? 1
      const limit = params.limit ?? 20
      const start = (page - 1) * limit
      const slice = filtered.slice(start, start + limit)
      return Promise.resolve({
        items: slice,
        total: filtered.length,
        page,
        limit,
        has_more: start + slice.length < filtered.length,
      })
    }
    return apiClient.get<PaginatedResponse<Provider>>(
      '/v1/providers',
      params as Record<string, unknown>,
    )
  },

  async getById(id: string): Promise<Provider> {
    if (useFixture()) {
      const found = providersFixture.find((p) => p.id === id)
      if (!found) throw new Error(`Provider ${id} not found`)
      return Promise.resolve(found)
    }
    return apiClient.get<Provider>(`/v1/providers/${id}`)
  },
}
