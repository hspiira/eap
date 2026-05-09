/**
 * Questionnaire API. Backs the dynamic triage form (Phase 3 #1).
 *
 * Fixture-driven until BE Phase 3 #2 lands — flip `VITE_QUESTIONNAIRES_USE_FIXTURE=false`
 * to switch to the live `/v1/questionnaires` endpoint.
 */

import apiClient from '../client'
import type { Questionnaire } from '../types'
import {
  fixtureGetAllQuestionnaires,
  fixtureGetQuestionnaireByCode,
} from './questionnaires-fixture'

function useFixture(): boolean {
  if (typeof import.meta === 'undefined') return true
  return import.meta.env?.VITE_QUESTIONNAIRES_USE_FIXTURE !== 'false'
}

export const questionnairesApi = {
  async list(): Promise<Questionnaire[]> {
    if (useFixture()) return Promise.resolve(fixtureGetAllQuestionnaires())
    return apiClient.get<Questionnaire[]>('/v1/questionnaires')
  },

  async getByCode(code: string): Promise<Questionnaire> {
    if (useFixture()) {
      const found = fixtureGetQuestionnaireByCode(code)
      if (!found) throw new Error(`Questionnaire ${code} not found`)
      return Promise.resolve(found)
    }
    return apiClient.get<Questionnaire>(`/v1/questionnaires/${code}`)
  },
}
