/**
 * EAP Programmes + Authorizations API Endpoints
 *
 * A programme defines per-service-category session caps for a contract; an
 * authorization instantiates one for a single case and tracks consumption.
 * Lifecycle: Active -> ExtensionRequested -> Extended -> {Exhausted, Expired, Closed}.
 * grant-extension is a two-person sign-off (clinician + admin).
 */

import type { Schemas } from '@/api/generated'

import apiClient from '../client'
import type { Authorization, EAPProgramme } from '../types'

export type CreateEAPProgrammeRequest = Schemas['CreateEAPProgrammeRequest']
export type AuthorizeCaseRequest = Schemas['AuthorizeCaseRequest']
export type RequestExtensionRequest = Schemas['RequestExtensionRequest']
export type GrantExtensionRequest = Schemas['GrantExtensionRequest']

export const eapProgrammesApi = {
  async create(data: CreateEAPProgrammeRequest): Promise<EAPProgramme> {
    return apiClient.post<EAPProgramme>('/eap-programmes', data)
  },

  async list(): Promise<EAPProgramme[]> {
    return apiClient.get<EAPProgramme[]>('/eap-programmes')
  },

  async getById(programmeId: string): Promise<EAPProgramme> {
    return apiClient.get<EAPProgramme>(`/eap-programmes/${programmeId}`)
  },
}

export const authorizationsApi = {
  async createForCase(caseId: string, data: AuthorizeCaseRequest): Promise<Authorization> {
    return apiClient.post<Authorization>(`/cases/${caseId}/authorize`, data)
  },

  async consume(authorizationId: string): Promise<Authorization> {
    return apiClient.post<Authorization>(`/authorizations/${authorizationId}/consume`, {})
  },

  async requestExtension(
    authorizationId: string,
    data: RequestExtensionRequest,
  ): Promise<Authorization> {
    return apiClient.post<Authorization>(
      `/authorizations/${authorizationId}/request-extension`,
      data,
    )
  },

  async grantExtension(
    authorizationId: string,
    data: GrantExtensionRequest,
  ): Promise<Authorization> {
    return apiClient.post<Authorization>(
      `/authorizations/${authorizationId}/grant-extension`,
      data,
    )
  },
}
