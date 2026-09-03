/**
 * Activities API Endpoints
 */

import type { ActivityType } from '@/types/enums'

import apiClient from '../client'
import type { Activity, ListParams, PaginatedResponse } from '../types'

export interface ActivityCreate {
  client_id: string
  activity_type: ActivityType
  title?: string | null
  description?: string | null
  occurred_at: string
  user_id?: string | null
  metadata?: Record<string, unknown> | null
}

/** Mirrors the query params on `GET /activities/` in the BE OpenAPI schema. */
export interface ActivityListParams extends ListParams {
  client_id?: string
  activity_type?: ActivityType
  created_by?: string
  is_important?: boolean
}

export const activitiesApi = {
  async create(data: ActivityCreate): Promise<Activity> {
    return apiClient.post<Activity>('/activities', data)
  },

  async getById(activityId: string): Promise<Activity> {
    return apiClient.get<Activity>(`/activities/${activityId}`)
  },

  async list(params?: ActivityListParams): Promise<PaginatedResponse<Activity>> {
    return apiClient.get<PaginatedResponse<Activity>>('/activities', params)
  },

  async update(activityId: string, data: Partial<ActivityCreate>): Promise<Activity> {
    return apiClient.patch<Activity>(`/activities/${activityId}`, data)
  },
}
