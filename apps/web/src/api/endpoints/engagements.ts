/**
 * Engagement API (Phase 4 #1). Fixture-driven until BE Phase 4 #1 lands.
 * Toggle with `VITE_ENGAGEMENTS_USE_FIXTURE=false`.
 */

import type { DeliverableStatus, EngagementStatus } from '@/types/enums'

import apiClient from '../client'
import type {
  Engagement,
  EngagementDeliverable,
  EngagementTimeEntry,
  EngagementTimelineEvent,
  PaginatedResponse,
} from '../types'
import {
  type DeliverableCreateInput,
  type EngagementCreateInput,
  fixtureAllowedTransitions,
  fixtureCreateDeliverable,
  fixtureCreateEngagement,
  fixtureCreateTimeEntry,
  fixtureGetEngagement,
  fixtureGetTimeline,
  fixtureListDeliverables,
  fixtureListEngagements,
  fixtureListTimeEntries,
  fixtureTransitionEngagement,
  fixtureUpdateDeliverableStatus,
  type TimeEntryCreateInput,
} from './engagements-fixture'

function useFixture(): boolean {
  if (typeof import.meta === 'undefined') return true
  return import.meta.env?.VITE_ENGAGEMENTS_USE_FIXTURE !== 'false'
}

function paginate<T>(items: T[]): PaginatedResponse<T> {
  return { items, total: items.length, page: 1, limit: items.length, has_more: false }
}

export const engagementsApi = {
  // ── Engagements ──────────────────────────────────────────────────────────
  async list(): Promise<PaginatedResponse<Engagement>> {
    if (useFixture()) return Promise.resolve(paginate(fixtureListEngagements()))
    return apiClient.get<PaginatedResponse<Engagement>>('/v1/engagements')
  },

  async getById(id: string): Promise<Engagement> {
    if (useFixture()) {
      const found = fixtureGetEngagement(id)
      if (!found) throw new Error(`Engagement ${id} not found`)
      return Promise.resolve(found)
    }
    return apiClient.get<Engagement>(`/v1/engagements/${id}`)
  },

  async create(input: EngagementCreateInput): Promise<Engagement> {
    if (useFixture()) return Promise.resolve(fixtureCreateEngagement(input))
    return apiClient.post<Engagement>('/v1/engagements', input)
  },

  async transition(id: string, to: EngagementStatus): Promise<Engagement> {
    if (useFixture()) return Promise.resolve(fixtureTransitionEngagement(id, to))
    return apiClient.post<Engagement>(`/v1/engagements/${id}/transition`, { to })
  },

  /** Static FSM helper — valid in fixture and BE modes. */
  allowedTransitions(from: EngagementStatus): EngagementStatus[] {
    return fixtureAllowedTransitions(from)
  },

  // ── Deliverables ────────────────────────────────────────────────────────
  async listDeliverables(engagementId: string): Promise<EngagementDeliverable[]> {
    if (useFixture()) return Promise.resolve(fixtureListDeliverables(engagementId))
    return apiClient.get<EngagementDeliverable[]>(`/v1/engagements/${engagementId}/deliverables`)
  },

  async createDeliverable(input: DeliverableCreateInput): Promise<EngagementDeliverable> {
    if (useFixture()) return Promise.resolve(fixtureCreateDeliverable(input))
    return apiClient.post<EngagementDeliverable>(
      `/v1/engagements/${input.engagement_id}/deliverables`,
      input,
    )
  },

  async updateDeliverableStatus(
    id: string,
    status: DeliverableStatus,
  ): Promise<EngagementDeliverable> {
    if (useFixture()) return Promise.resolve(fixtureUpdateDeliverableStatus(id, status))
    return apiClient.post<EngagementDeliverable>(`/v1/deliverables/${id}/status`, { status })
  },

  // ── Time entries ────────────────────────────────────────────────────────
  async listTimeEntries(engagementId: string): Promise<EngagementTimeEntry[]> {
    if (useFixture()) return Promise.resolve(fixtureListTimeEntries(engagementId))
    return apiClient.get<EngagementTimeEntry[]>(`/v1/engagements/${engagementId}/time-entries`)
  },

  async logTime(input: TimeEntryCreateInput): Promise<EngagementTimeEntry> {
    if (useFixture()) return Promise.resolve(fixtureCreateTimeEntry(input))
    return apiClient.post<EngagementTimeEntry>(
      `/v1/engagements/${input.engagement_id}/time-entries`,
      input,
    )
  },

  // ── Timeline ────────────────────────────────────────────────────────────
  async getTimeline(engagementId: string): Promise<EngagementTimelineEvent[]> {
    if (useFixture()) return Promise.resolve(fixtureGetTimeline(engagementId))
    return apiClient.get<EngagementTimelineEvent[]>(`/v1/engagements/${engagementId}/timeline`)
  },
}

export type {
  DeliverableCreateInput,
  EngagementCreateInput,
  TimeEntryCreateInput,
} from './engagements-fixture'
