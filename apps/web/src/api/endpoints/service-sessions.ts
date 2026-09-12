import type { Schemas, ServiceSessionCreate } from "@/api/generated"

type AvailabilityResponse = Schemas["AvailabilityResponse"]
type SessionChain = Schemas["SessionChainResponse"]
import type {
  SessionCategory,
  SessionClinicalStatus,
  SessionStatus,
  SessionType,
} from "@/types/enums"

import apiClient from "../client"
import type { ListParams, PaginatedResponse, ServiceSession } from "../types"

export type { ServiceSessionCreate }
export type ServiceSessionUpdate = Schemas["ServiceSessionUpdate"]
export type ServiceSessionCompleteRequest = Schemas["ServiceSessionCompleteRequest"]
export type SessionDrawdown = Schemas["SessionDrawdownResponse"]

/** `session` is typed as the entity, matching how the other endpoints here cast. */
export interface ServiceSessionCompleteResult {
  session: ServiceSession
  drawdown: SessionDrawdown
}
export type ServiceSessionCancelRequest = Schemas["ServiceSessionCancelRequest"]
export type ServiceSessionRescheduleRequest = Schemas["ServiceSessionRescheduleRequest"]
export type ServiceSessionUpdateFeedback = Schemas["ServiceSessionUpdateFeedback"]

/** Mirrors the query params on `GET /service-sessions/` in the BE OpenAPI schema. */
export interface ServiceSessionListParams extends ListParams {
  client_id?: string
  member_id?: string
  provider_id?: string
  service_id?: string
  /** One status, or several (repeated `status=` query params). */
  status?: SessionStatus | SessionStatus[]
  session_type?: SessionType
  category?: SessionCategory
  clinical_outcome?: SessionClinicalStatus
  /** ISO 8601 instant; inclusive lower bound on `scheduled_at`. */
  scheduled_from?: string
  /** ISO 8601 instant; inclusive upper bound on `scheduled_at`. */
  scheduled_to?: string
  /** Matches service, client or practitioner display name. Never clinical fields. */
  search?: string
}

export const serviceSessionsApi = {
  /**
   * Create a new service session
   */
  async create(sessionData: ServiceSessionCreate): Promise<ServiceSession> {
    return apiClient.post<ServiceSession>("/service-sessions", sessionData)
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
  async list(params?: ServiceSessionListParams): Promise<PaginatedResponse<ServiceSession>> {
    return apiClient.get<PaginatedResponse<ServiceSession>>("/service-sessions", params)
  },

  /**
   * The sessions immediately before and after this one.
   *
   * One hop each way. The stored link points backwards, so the forward half
   * has to be looked up rather than read off the session.
   */
  async chain(sessionId: string): Promise<SessionChain> {
    return apiClient.get<SessionChain>(`/service-sessions/${sessionId}/chain`)
  },

  /**
   * Which of the named practitioners already have a booking over this span.
   *
   * Reports only bookings held in this system. It is not a claim about an
   * externally affiliated practitioner's own diary, which is not visible here.
   */
  async availability(params: {
    at: string
    service_id: string
    provider_id: string[]
  }): Promise<AvailabilityResponse> {
    return apiClient.get<AvailabilityResponse>("/service-sessions/availability", params)
  },

  /**
   * Bookings whose date has passed that nobody has confirmed or closed.
   *
   * A separate endpoint rather than `list` with a status filter and a
   * `scheduled_to: now`: "awaiting confirmation" is its own concept
   * (Scheduled/Rescheduled past their date), not a generic query. Oldest first.
   */
  async awaitingConfirmation(params?: {
    provider_id?: string
    client_id?: string
    page?: number
    limit?: number
  }): Promise<PaginatedResponse<ServiceSession>> {
    return apiClient.get<PaginatedResponse<ServiceSession>>(
      "/service-sessions/awaiting-confirmation",
      params,
    )
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
  async reschedule(
    sessionId: string,
    data: ServiceSessionRescheduleRequest,
  ): Promise<ServiceSession> {
    return apiClient.post<ServiceSession>(`/service-sessions/${sessionId}/reschedule`, data)
  },

  /**
   * Complete service session. BE requires `{duration: int>0, notes: str≥1}`.
   */
  async complete(
    sessionId: string,
    data: ServiceSessionCompleteRequest,
  ): Promise<ServiceSessionCompleteResult> {
    return apiClient.post<ServiceSessionCompleteResult>(
      `/service-sessions/${sessionId}/complete`,
      data,
    )
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
  async updateFeedback(
    sessionId: string,
    data: ServiceSessionUpdateFeedback,
  ): Promise<ServiceSession> {
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
