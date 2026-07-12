/**
 * Survey campaign API (Phase 3 #3).
 *
 * BE base path is `/survey-campaigns` (confirmed via openapi.json).
 * Fixture is DEV-only.
 *
 * Note: `rotateWebhookToken` has been removed — BE has no such route.
 * The webhook secret is returned once on create; display it immediately.
 */

import apiClient from '../client'
import type { PaginatedResponse, Survey, SurveyAggregate } from '../types'
import { SurveyStatus } from '@/types/enums'
import {
  fixtureCloseSurvey,
  fixtureCreateSurvey,
  fixtureGetSurvey,
  fixtureListSurveys,
  fixtureSurveyAggregate,
  type SurveyCreateInput,
} from './surveys-fixture'

function useFixture(): boolean {
  if (typeof import.meta === 'undefined') return true
  return import.meta.env.DEV
}

function paginate<T>(items: T[]): PaginatedResponse<T> {
  return { items, total: items.length, page: 1, limit: items.length, has_more: false }
}

export const surveysApi = {
  async list(): Promise<PaginatedResponse<Survey>> {
    if (useFixture()) return Promise.resolve(paginate(fixtureListSurveys()))
    return apiClient.get<PaginatedResponse<Survey>>('/survey-campaigns')
  },

  async getById(id: string): Promise<Survey> {
    if (useFixture()) {
      const found = fixtureGetSurvey(id)
      if (!found) throw new Error(`Survey ${id} not found`)
      return Promise.resolve(found)
    }
    return apiClient.get<Survey>(`/survey-campaigns/${id}`)
  },

  async create(input: SurveyCreateInput): Promise<Survey> {
    if (useFixture()) return Promise.resolve(fixtureCreateSurvey(input))
    return apiClient.post<Survey>('/survey-campaigns', input)
  },

  async activate(id: string): Promise<Survey> {
    if (useFixture()) {
      const found = fixtureGetSurvey(id)
      if (!found) throw new Error(`Survey ${id} not found`)
      return Promise.resolve({ ...found, status: SurveyStatus.COLLECTING })
    }
    return apiClient.post<Survey>(`/survey-campaigns/${id}/activate`, {})
  },

  async close(id: string): Promise<Survey> {
    if (useFixture()) return Promise.resolve(fixtureCloseSurvey(id))
    return apiClient.post<Survey>(`/survey-campaigns/${id}/close`, {})
  },

  async getAggregate(id: string): Promise<SurveyAggregate> {
    if (useFixture()) return Promise.resolve(fixtureSurveyAggregate(id))
    return apiClient.get<SurveyAggregate>(`/survey-campaigns/${id}/aggregate`)
  },
}

export type { SurveyCreateInput } from './surveys-fixture'
