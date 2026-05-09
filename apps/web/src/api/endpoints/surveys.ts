/**
 * Survey API (Phase 3 #2). Fixture-driven until BE Phase 3 #3 lands.
 * Toggle with `VITE_SURVEYS_USE_FIXTURE=false`.
 */

import apiClient from '../client'
import type { PaginatedResponse, Survey, SurveyAggregate } from '../types'
import {
  fixtureCloseSurvey,
  fixtureCreateSurvey,
  fixtureGetSurvey,
  fixtureListSurveys,
  fixtureRotateWebhookToken,
  fixtureSurveyAggregate,
  type SurveyCreateInput,
} from './surveys-fixture'

function useFixture(): boolean {
  if (typeof import.meta === 'undefined') return true
  return import.meta.env?.VITE_SURVEYS_USE_FIXTURE !== 'false'
}

function paginate<T>(items: T[]): PaginatedResponse<T> {
  return { items, total: items.length, page: 1, limit: items.length, has_more: false }
}

export const surveysApi = {
  async list(): Promise<PaginatedResponse<Survey>> {
    if (useFixture()) return Promise.resolve(paginate(fixtureListSurveys()))
    return apiClient.get<PaginatedResponse<Survey>>('/v1/surveys')
  },

  async getById(id: string): Promise<Survey> {
    if (useFixture()) {
      const found = fixtureGetSurvey(id)
      if (!found) throw new Error(`Survey ${id} not found`)
      return Promise.resolve(found)
    }
    return apiClient.get<Survey>(`/v1/surveys/${id}`)
  },

  async create(input: SurveyCreateInput): Promise<Survey> {
    if (useFixture()) return Promise.resolve(fixtureCreateSurvey(input))
    return apiClient.post<Survey>('/v1/surveys', input)
  },

  async close(id: string): Promise<Survey> {
    if (useFixture()) return Promise.resolve(fixtureCloseSurvey(id))
    return apiClient.post<Survey>(`/v1/surveys/${id}/close`, {})
  },

  async rotateWebhookToken(id: string): Promise<Survey> {
    if (useFixture()) return Promise.resolve(fixtureRotateWebhookToken(id))
    return apiClient.post<Survey>(`/v1/surveys/${id}/rotate-token`, {})
  },

  async getAggregate(id: string): Promise<SurveyAggregate> {
    if (useFixture()) return Promise.resolve(fixtureSurveyAggregate(id))
    return apiClient.get<SurveyAggregate>(`/v1/surveys/${id}/aggregate`)
  },
}

export type { SurveyCreateInput } from './surveys-fixture'
