/**
 * Incidents (CISM v1) API. Fixture-backed until BE Phase 2 #5 lands.
 * Toggle with `VITE_INCIDENTS_USE_FIXTURE=false` once the BE endpoint is live.
 */

import type { IncidentSeverity } from '@/types/enums'

import apiClient from '../client'
import type { Incident, IncidentTimelineEvent, PaginatedResponse } from '../types'
import {
  fixtureAppendNote,
  fixtureCreate,
  fixtureGetAll,
  fixtureGetById,
  fixtureGetTimeline,
} from './incidents-fixture'

export interface IncidentCreate {
  client_id: string
  title: string
  description: string
  severity: IncidentSeverity
  occurred_at: string
  affected_population: number
}

function useFixture(): boolean {
  if (typeof import.meta === 'undefined') return true
  return import.meta.env?.VITE_INCIDENTS_USE_FIXTURE !== 'false'
}

export const incidentsApi = {
  async list(): Promise<PaginatedResponse<Incident>> {
    if (useFixture()) {
      const items = fixtureGetAll()
      return Promise.resolve({
        items,
        total: items.length,
        page: 1,
        limit: items.length,
        has_more: false,
      })
    }
    return apiClient.get<PaginatedResponse<Incident>>('/v1/incidents')
  },

  async getById(id: string): Promise<Incident> {
    if (useFixture()) {
      const found = fixtureGetById(id)
      if (!found) throw new Error(`Incident ${id} not found`)
      return Promise.resolve(found)
    }
    return apiClient.get<Incident>(`/v1/incidents/${id}`)
  },

  async getTimeline(incidentId: string): Promise<IncidentTimelineEvent[]> {
    if (useFixture()) return Promise.resolve(fixtureGetTimeline(incidentId))
    return apiClient.get<IncidentTimelineEvent[]>(`/v1/incidents/${incidentId}/timeline`)
  },

  async create(data: IncidentCreate): Promise<Incident> {
    if (useFixture()) return Promise.resolve(fixtureCreate(data))
    return apiClient.post<Incident>('/v1/incidents', data)
  },

  async appendNote(incidentId: string, message: string): Promise<IncidentTimelineEvent> {
    if (useFixture()) return Promise.resolve(fixtureAppendNote(incidentId, message))
    return apiClient.post<IncidentTimelineEvent>(`/v1/incidents/${incidentId}/notes`, { message })
  },
}
