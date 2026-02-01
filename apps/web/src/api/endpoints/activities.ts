/**
 * Activities API Endpoints
 */

import apiClient from '../client'
import type { Activity, PaginatedResponse, ListParams } from '../types'
import type { ActivityType } from '@/types/enums'

export interface ActivityCreate {
  client_id: string
  activity_type: ActivityType
  title?: string | null
  description?: string | null
  occurred_at: string
  user_id?: string | null
  metadata?: Record<string, unknown> | null
}

export const activitiesApi = {
  async create(data: ActivityCreate): Promise<Activity> {
    return apiClient.post<Activity>('/activities', data)
  },

  async getById(activityId: string): Promise<Activity> {
    return apiClient.get<Activity>(`/activities/${activityId}`)
  },

  async list(params?: ListParams): Promise<PaginatedResponse<Activity>> {
    return apiClient.get<PaginatedResponse<Activity>>('/activities', params as Record<string, unknown>)
  },

  async update(activityId: string, data: Partial<ActivityCreate>): Promise<Activity> {
    return apiClient.patch<Activity>(`/activities/${activityId}`, data)
  },
}
