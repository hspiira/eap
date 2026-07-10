/**
 * Service Assignments API Endpoints
 *
 * Create/Update payload shapes are sourced from the BE OpenAPI schema via
 * `@/api/generated`. Do not extend ServiceAssignmentCreate locally — if the
 * shape needs to change, update the BE Pydantic schema and re-run
 * `pnpm openapi:sync`.
 */

import type { ServiceAssignmentCreate, ServiceAssignmentUpdate } from '@/api/generated'

import apiClient from '../client'
import type { ListParams, PaginatedResponse, ServiceAssignment } from '../types'

export type { ServiceAssignmentCreate, ServiceAssignmentUpdate }

export const serviceAssignmentsApi = {
  /**
   * Create a new service assignment
   */
  async create(assignmentData: ServiceAssignmentCreate): Promise<ServiceAssignment> {
    return apiClient.post<ServiceAssignment>('/service-assignments', assignmentData)
  },

  /**
   * Get service assignment by ID
   */
  async getById(assignmentId: string): Promise<ServiceAssignment> {
    return apiClient.get<ServiceAssignment>(`/service-assignments/${assignmentId}`)
  },

  /**
   * List service assignments
   */
  async list(params?: ListParams): Promise<PaginatedResponse<ServiceAssignment>> {
    return apiClient.get<PaginatedResponse<ServiceAssignment>>('/service-assignments', params as Record<string, unknown>)
  },

  /**
   * Update service assignment
   */
  async update(assignmentId: string, data: ServiceAssignmentUpdate): Promise<ServiceAssignment> {
    return apiClient.patch<ServiceAssignment>(`/service-assignments/${assignmentId}`, data)
  },

  /**
   * Activate service assignment
   */
  async activate(assignmentId: string): Promise<ServiceAssignment> {
    return apiClient.post<ServiceAssignment>(`/service-assignments/${assignmentId}/activate`, {})
  },

  /**
   * Deactivate service assignment
   */
  async deactivate(assignmentId: string): Promise<ServiceAssignment> {
    return apiClient.post<ServiceAssignment>(`/service-assignments/${assignmentId}/deactivate`, {})
  },

  /**
   * Archive service assignment
   */
  async archive(assignmentId: string): Promise<ServiceAssignment> {
    return apiClient.post<ServiceAssignment>(`/service-assignments/${assignmentId}/archive`, {})
  },

  /**
   * Restore service assignment from archive
   */
  async restore(assignmentId: string): Promise<ServiceAssignment> {
    return apiClient.post<ServiceAssignment>(`/service-assignments/${assignmentId}/restore`, {})
  },
}
