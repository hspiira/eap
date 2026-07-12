/**
 * Triage instrument API (Phase 3 #2).
 *
 * BE base path is `/triage/instruments` (confirmed via openapi.json).
 * Fixture is DEV-only — flip to live by running production build.
 */

import apiClient from '../client'
import type { Questionnaire } from '../types'
import {
  fixtureGetAllQuestionnaires,
  fixtureGetQuestionnaireByCode,
} from './questionnaires-fixture'

function useFixture(): boolean {
  if (typeof import.meta === 'undefined') return true
  return import.meta.env.DEV
}

export const questionnairesApi = {
  async list(): Promise<Questionnaire[]> {
    if (useFixture()) return Promise.resolve(fixtureGetAllQuestionnaires())
    return apiClient.get<Questionnaire[]>('/triage/instruments')
  },

  async getByCode(code: string): Promise<Questionnaire> {
    if (useFixture()) {
      const found = fixtureGetQuestionnaireByCode(code)
      if (!found) throw new Error(`Questionnaire ${code} not found`)
      return Promise.resolve(found)
    }
    return apiClient.get<Questionnaire>(`/triage/instruments/${code}`)
  },
}
