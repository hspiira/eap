/**
 * Diagnoses (D-Tax) API.
 *
 * BE endpoint `/v1/diagnoses` ships in BE Phase 2 #1. Until then, this module returns
 * the bundled fixture under [src/api/endpoints/diagnoses-fixture.ts]. Flip
 * `VITE_DIAGNOSES_USE_FIXTURE=false` once the BE is live.
 */

import apiClient from '../client'
import type { Diagnosis, PaginatedResponse } from '../types'
import { diagnosesFixture } from './diagnoses-fixture'

export interface DiagnosisListParams {
  search?: string
  parent_id?: string | null
  /** Limit to a max depth from the root. Optional. */
  max_level?: number
  page?: number
  limit?: number
}

function useFixture(): boolean {
  if (typeof import.meta === 'undefined') return true
  return import.meta.env?.VITE_DIAGNOSES_USE_FIXTURE !== 'false'
}

function fixtureList(params: DiagnosisListParams): PaginatedResponse<Diagnosis> {
  const search = params.search?.trim().toLowerCase() ?? ''
  let items = diagnosesFixture

  if (search) {
    items = items.filter(
      (d) =>
        d.code.toLowerCase().includes(search) ||
        d.label.toLowerCase().includes(search) ||
        d.path.toLowerCase().includes(search),
    )
  } else if (params.parent_id !== undefined) {
    items = items.filter((d) => d.parent_id === params.parent_id)
  } else {
    items = items.filter((d) => d.parent_id === null)
  }

  if (typeof params.max_level === 'number') {
    items = items.filter((d) => d.level <= (params.max_level as number))
  }

  const page = params.page ?? 1
  const limit = params.limit ?? 100
  const start = (page - 1) * limit
  const slice = items.slice(start, start + limit)
  return {
    items: slice,
    total: items.length,
    page,
    limit,
    has_more: start + slice.length < items.length,
  }
}

export const diagnosesApi = {
  async list(params: DiagnosisListParams = {}): Promise<PaginatedResponse<Diagnosis>> {
    if (useFixture()) {
      return Promise.resolve(fixtureList(params))
    }
    return apiClient.get<PaginatedResponse<Diagnosis>>(
      '/v1/diagnoses',
      params as Record<string, unknown>,
    )
  },

  async getById(id: string): Promise<Diagnosis> {
    if (useFixture()) {
      const found = diagnosesFixture.find((d) => d.id === id)
      if (!found) throw new Error(`Diagnosis ${id} not found in fixture`)
      return Promise.resolve(found)
    }
    return apiClient.get<Diagnosis>(`/v1/diagnoses/${id}`)
  },
}
