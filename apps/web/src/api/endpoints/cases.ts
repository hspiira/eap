/**
 * Clinical Cases API Endpoints
 *
 * All routes require the Clinical access scope (BE fails closed with 403
 * otherwise). GET /cases takes no query params — the BE list is unfiltered
 * and unpaginated, so the list page filters/searches client-side, same as
 * care-callbacks/engagements/surveys.
 */

import type { Schemas } from '@/api/generated'

import apiClient from '../client'
import type { Case } from '../types'

export type OpenCaseRequest = Schemas['OpenCaseRequest']
export type AssignCounsellorRequest = Schemas['AssignCounsellorRequest']
export type AdvanceCaseRequest = Schemas['AdvanceCaseRequest']
export type CloseCaseRequest = Schemas['CloseCaseRequest']
export type ReferOutCaseRequest = Schemas['ReferOutCaseRequest']

export const casesApi = {
  async create(data: OpenCaseRequest): Promise<Case> {
    return apiClient.post<Case>('/cases', data)
  },

  async list(): Promise<Case[]> {
    return apiClient.get<Case[]>('/cases')
  },

  async getById(caseId: string): Promise<Case> {
    return apiClient.get<Case>(`/cases/${caseId}`)
  },

  async assignCounsellor(caseId: string, data: AssignCounsellorRequest): Promise<Case> {
    return apiClient.post<Case>(`/cases/${caseId}/assign-counsellor`, data)
  },

  async advance(caseId: string, data: AdvanceCaseRequest): Promise<Case> {
    return apiClient.post<Case>(`/cases/${caseId}/advance`, data)
  },

  async close(caseId: string, data: CloseCaseRequest): Promise<Case> {
    return apiClient.post<Case>(`/cases/${caseId}/close`, data)
  },

  async referOut(caseId: string, data: ReferOutCaseRequest): Promise<Case> {
    return apiClient.post<Case>(`/cases/${caseId}/refer-out`, data)
  },
}
