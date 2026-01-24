/**
 * KPIs API Endpoints
 */

import apiClient from '../client'
import type { KPI, KPIAssignment, PaginatedResponse, ListParams } from '../types'
import type { KPICategory, MeasurementUnit } from '@/types/enums'

export interface KPICreate {
  name: string
  description?: string | null
  category: KPICategory
  measurement_unit: MeasurementUnit
  target_value?: number | null
  metadata?: Record<string, unknown> | null
}

export interface KPIAssignmentCreate {
  assignable_type: 'Client' | 'Contract'
  assignable_id: string
  target_value?: number | null
  start_date?: string | null
  end_date?: string | null
}

export const kpisApi = {
  /**
   * Create a new KPI
   */
  async create(kpiData: KPICreate): Promise<KPI> {
    return apiClient.post<KPI>('/kpis', kpiData)
  },

  /**
   * Get KPI by ID
   */
  async getById(kpiId: string): Promise<KPI> {
    return apiClient.get<KPI>(`/kpis/${kpiId}`)
  },

  /**
   * List KPIs
   */
  async list(params?: ListParams): Promise<PaginatedResponse<KPI>> {
    return apiClient.get<PaginatedResponse<KPI>>('/kpis', params as Record<string, unknown>)
  },

  /**
   * Update KPI
   */
  async update(kpiId: string, data: Partial<KPICreate>): Promise<KPI> {
    return apiClient.patch<KPI>(`/kpis/${kpiId}`, data)
  },

  /**
   * Assign KPI to client or contract
   */
  async assign(kpiId: string, assignmentData: KPIAssignmentCreate): Promise<KPIAssignment> {
    return apiClient.post<KPIAssignment>(`/kpis/${kpiId}/assign`, assignmentData)
  },

  /**
   * Get KPI assignments
   */
  async getAssignments(kpiId: string): Promise<KPIAssignment[]> {
    return apiClient.get<KPIAssignment[]>(`/kpis/${kpiId}/assignments`)
  },
}
