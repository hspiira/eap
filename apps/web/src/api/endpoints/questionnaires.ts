/**
 * Triage instrument API (Phase 3 #2).
 *
 * BE base path is `/triage/instruments` (confirmed via openapi.json).
 * Fixture is DEV-only — flip to live by running production build.
 */

import { useFixtures } from '@/lib/fixtures'

import apiClient from '../client'
import type { Questionnaire } from '../types'
import {
  fixtureGetAllQuestionnaires,
  fixtureGetQuestionnaireByCode,
} from './questionnaires-fixture'

export const questionnairesApi = {
  async list(): Promise<Questionnaire[]> {
    if (useFixtures()) return Promise.resolve(fixtureGetAllQuestionnaires())
    return apiClient.get<Questionnaire[]>('/triage/instruments')
  },

  async getByCode(code: string): Promise<Questionnaire> {
    if (useFixtures()) {
      const found = fixtureGetQuestionnaireByCode(code)
      if (!found) throw new Error(`Questionnaire ${code} not found`)
      return Promise.resolve(found)
    }
    return apiClient.get<Questionnaire>(`/triage/instruments/${code}`)
  },
}
