/**
 * Diagnoses (D-Tax v2) API.
 *
 * BE shape is a flat two-level taxonomy: types → diagnoses.
 * Three routes (confirmed via openapi.json):
 *   GET /diagnoses/types   — list all diagnosis types
 *   GET /diagnoses/tree    — types with nested diagnoses (preferred for UI)
 *   GET /diagnoses         — flat list, optionally filtered by type_code
 *
 * Fixture is DEV-only.
 */

import apiClient from '../client'
import type { Diagnosis, DiagnosisTree, DiagnosisType } from '@/types/entities'
import {
  fixtureGetTree,
  fixtureGetTypes,
  fixtureListDiagnoses,
} from './diagnoses-fixture'

export interface DiagnosisListParams {
  type_code?: string
  active_only?: boolean
}

function useFixture(): boolean {
  if (typeof import.meta === 'undefined') return true
  return import.meta.env.DEV
}

export const diagnosesApi = {
  async getTypes(): Promise<DiagnosisType[]> {
    if (useFixture()) return Promise.resolve(fixtureGetTypes())
    return apiClient.get<DiagnosisType[]>('/diagnoses/types')
  },

  async getTree(): Promise<DiagnosisTree> {
    if (useFixture()) return Promise.resolve(fixtureGetTree())
    return apiClient.get<DiagnosisTree>('/diagnoses/tree')
  },

  async list(params: DiagnosisListParams = {}): Promise<Diagnosis[]> {
    if (useFixture()) return Promise.resolve(fixtureListDiagnoses(params.type_code))
    return apiClient.get<Diagnosis[]>('/diagnoses', params as Record<string, unknown>)
  },
}
