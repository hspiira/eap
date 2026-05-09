/**
 * Service Sessions API Endpoints
 *
 * Create payload sourced from BE OpenAPI (`@/api/generated.ServiceSessionCreate`).
 * Fields beyond `{service_id, provider_id, person_id, scheduled_at, location}`
 * are not accepted by the BE. Lifecycle mutations (complete/cancel/no-show)
 * have dedicated request schemas; see ServiceSessionCompleteRequest etc.
 */

import type { Schemas, ServiceSessionCreate } from '@/api/generated'

import apiClient from '../client'
import type { ListParams, PaginatedResponse, ServiceSession } from '../types'

export type { ServiceSessionCreate }
export type ServiceSessionUpdate = Schemas['ServiceSessionUpdate']
export type ServiceSessionCompleteRequest = Schemas['ServiceSessionCompleteRequest']
export type ServiceSessionCancelRequest = Schemas['ServiceSessionCancelRequest']
export type ServiceSessionRescheduleRequest = Schemas['ServiceSessionRescheduleRequest']
export type ServiceSessionUpdateFeedback = Schemas['ServiceSessionUpdateFeedback']

export const serviceSessionsApi = {
  /**
   * Create a new service session
   */
  async create(sessionData: ServiceSessionCreate): Promise<ServiceSession> {
    return apiClient.post<ServiceSession>('/service-sessions', sessionData)
  },

  /**
   * Get service session by ID
   */
  async getById(sessionId: string): Promise<ServiceSession> {
    return apiClient.get<ServiceSession>(`/service-sessions/${sessionId}`)
  },

  /**
   * List service sessions
   */
  async list(params?: ListParams): Promise<PaginatedResponse<ServiceSession>> {
    return apiClient.get<PaginatedResponse<ServiceSession>>('/service-sessions', params as Record<string, unknown>)
  },

  /**
   * Update service session (BE accepts only `{location?, notes?}`).
   */
  async update(sessionId: string, data: ServiceSessionUpdate): Promise<ServiceSession> {
    return apiClient.patch<ServiceSession>(`/service-sessions/${sessionId}`, data)
  },

  /**
   * Reschedule service session. BE field is `new_scheduled_at` (ISO datetime).
   */
  async reschedule(sessionId: string, data: ServiceSessionRescheduleRequest): Promise<ServiceSession> {
    return apiClient.post<ServiceSession>(`/service-sessions/${sessionId}/reschedule`, data)
  },

  /**
   * Complete service session. BE requires `{duration: int>0, notes: str≥1}`.
   */
  async complete(sessionId: string, data: ServiceSessionCompleteRequest): Promise<ServiceSession> {
    return apiClient.post<ServiceSession>(`/service-sessions/${sessionId}/complete`, data)
  },

  /**
   * Cancel service session. BE requires `{reason: str≥1}`.
   */
  async cancel(sessionId: string, data: ServiceSessionCancelRequest): Promise<ServiceSession> {
    return apiClient.post<ServiceSession>(`/service-sessions/${sessionId}/cancel`, data)
  },

  /**
   * Mark service session as no-show (BE accepts no body).
   */
  async noShow(sessionId: string): Promise<ServiceSession> {
    return apiClient.post<ServiceSession>(`/service-sessions/${sessionId}/no-show`, {})
  },

  /**
   * Update session feedback. BE accepts `{feedback: str≥1}` (single field).
   */
  async updateFeedback(sessionId: string, data: ServiceSessionUpdateFeedback): Promise<ServiceSession> {
    return apiClient.patch<ServiceSession>(`/service-sessions/${sessionId}/feedback`, data)
  },

  /**
   * Archive service session
   */
  async archive(sessionId: string): Promise<ServiceSession> {
    return apiClient.post<ServiceSession>(`/service-sessions/${sessionId}/archive`, {})
  },

  /**
   * Restore service session from archive
   */
  async restore(sessionId: string): Promise<ServiceSession> {
    return apiClient.post<ServiceSession>(`/service-sessions/${sessionId}/restore`, {})
  },
}
