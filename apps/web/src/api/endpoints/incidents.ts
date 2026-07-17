/**
 * Critical incidents (CISM v1) API.
 *
 * BE base path is `/critical-incidents` (confirmed via openapi.json).
 * Fixture is DEV-only. The full CISM UI (P2 #5) will add:
 *   POST /{id}/phases  — phase-add form (Demobilisation, Defusing, ...)
 *   GET  /{id}/after-action — printable after-action report
 */

import { useFixtures } from '@/lib/fixtures'
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

export const incidentsApi = {
  async list(): Promise<PaginatedResponse<Incident>> {
    if (useFixtures()) {
      const items = fixtureGetAll()
      return Promise.resolve({ items, total: items.length, page: 1, limit: items.length, has_more: false })
    }
    return apiClient.get<PaginatedResponse<Incident>>('/critical-incidents')
  },

  async getById(id: string): Promise<Incident> {
    if (useFixtures()) {
      const found = fixtureGetById(id)
      if (!found) throw new Error(`Incident ${id} not found`)
      return Promise.resolve(found)
    }
    return apiClient.get<Incident>(`/critical-incidents/${id}`)
  },

  async create(data: IncidentCreate): Promise<Incident> {
    if (useFixtures()) return Promise.resolve(fixtureCreate(data))
    return apiClient.post<Incident>('/critical-incidents', data)
  },

  /** Returns fixture timeline; live path will use GET /{id}/after-action in P2 #5. */
  async getTimeline(incidentId: string): Promise<IncidentTimelineEvent[]> {
    if (useFixtures()) return Promise.resolve(fixtureGetTimeline(incidentId))
    return apiClient.get<IncidentTimelineEvent[]>(`/critical-incidents/${incidentId}/after-action`)
  },

  /** Adds a note/phase entry. Live path uses POST /{id}/phases in P2 #5. */
  async appendNote(incidentId: string, message: string): Promise<IncidentTimelineEvent> {
    if (useFixtures()) return Promise.resolve(fixtureAppendNote(incidentId, message))
    return apiClient.post<IncidentTimelineEvent>(`/critical-incidents/${incidentId}/phases`, { message })
  },
}
