/**
 * Service Sessions API Endpoints
 */

import apiClient from '../client'
import type { ServiceSession, PaginatedResponse, ListParams } from '../types'
import type { SessionStatus } from '@/types/enums'

export interface ServiceSessionCreate {
  service_id: string
  person_id: string
  service_provider_id?: string | null
  contract_id?: string | null
  scheduled_at: string
  location?: string | null
  notes?: string | null
  metadata?: Record<string, unknown> | null
}

export interface ServiceSessionReschedule {
  scheduled_at: string
  notes?: string | null
}

export interface ServiceSessionFeedback {
  rating?: number | null
  comments?: string | null
}

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
   * Update service session
   */
  async update(sessionId: string, data: Partial<ServiceSessionCreate>): Promise<ServiceSession> {
    return apiClient.patch<ServiceSession>(`/service-sessions/${sessionId}`, data)
  },

  /**
   * Reschedule service session
   */
  async reschedule(sessionId: string, data: ServiceSessionReschedule): Promise<ServiceSession> {
    return apiClient.post<ServiceSession>(`/service-sessions/${sessionId}/reschedule`, data)
  },

  /**
   * Complete service session
   */
  async complete(sessionId: string): Promise<ServiceSession> {
    return apiClient.post<ServiceSession>(`/service-sessions/${sessionId}/complete`, {})
  },

  /**
   * Cancel service session
   */
  async cancel(sessionId: string): Promise<ServiceSession> {
    return apiClient.post<ServiceSession>(`/service-sessions/${sessionId}/cancel`, {})
  },

  /**
   * Mark service session as no-show
   */
  async noShow(sessionId: string): Promise<ServiceSession> {
    return apiClient.post<ServiceSession>(`/service-sessions/${sessionId}/no-show`, {})
  },

  /**
   * Update session feedback
   */
  async updateFeedback(sessionId: string, feedback: ServiceSessionFeedback): Promise<ServiceSession> {
    return apiClient.patch<ServiceSession>(`/service-sessions/${sessionId}/feedback`, feedback)
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
