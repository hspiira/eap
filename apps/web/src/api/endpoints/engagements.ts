/**
 * Engagement API (Phase 4 #1).
 *
 * BE base path is `/engagements` (confirmed via openapi.json).
 * Fixture is DEV-only.
 *
 * Status transitions use per-FSM action routes:
 *   ACTIVE    → POST /engagements/{id}/activate
 *   DELIVERED → POST /engagements/{id}/deliver
 *   CLOSED    → POST /engagements/{id}/close
 */

import type { DeliverableStatus} from '@/types/enums';
import { EngagementStatus } from '@/types/enums'

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
  return import.meta.env.DEV
}

function paginate<T>(items: T[]): PaginatedResponse<T> {
  return { items, total: items.length, page: 1, limit: items.length, has_more: false }
}

const FSM_ROUTES: Partial<Record<EngagementStatus, string>> = {
  [EngagementStatus.ACTIVE]: 'activate',
  [EngagementStatus.DELIVERED]: 'deliver',
  [EngagementStatus.CLOSED]: 'close',
}

export const engagementsApi = {
  // ── Engagements ──────────────────────────────────────────────────────────
  async list(): Promise<PaginatedResponse<Engagement>> {
    if (useFixture()) return Promise.resolve(paginate(fixtureListEngagements()))
    return apiClient.get<PaginatedResponse<Engagement>>('/engagements')
  },

  async getById(id: string): Promise<Engagement> {
    if (useFixture()) {
      const found = fixtureGetEngagement(id)
      if (!found) throw new Error(`Engagement ${id} not found`)
      return Promise.resolve(found)
    }
    return apiClient.get<Engagement>(`/engagements/${id}`)
  },

  async create(input: EngagementCreateInput): Promise<Engagement> {
    if (useFixture()) return Promise.resolve(fixtureCreateEngagement(input))
    return apiClient.post<Engagement>('/engagements', input)
  },

  async transition(id: string, to: EngagementStatus): Promise<Engagement> {
    if (useFixture()) return Promise.resolve(fixtureTransitionEngagement(id, to))
    const action = FSM_ROUTES[to]
    if (!action) throw new Error(`No FSM route for status: ${to}`)
    return apiClient.post<Engagement>(`/engagements/${id}/${action}`, {})
  },

  /** Static FSM helper — valid in fixture and live modes. */
  allowedTransitions(from: EngagementStatus): EngagementStatus[] {
    return fixtureAllowedTransitions(from)
  },

  // ── Deliverables ─────────────────────────────────────────────────────────
  async listDeliverables(engagementId: string): Promise<EngagementDeliverable[]> {
    if (useFixture()) return Promise.resolve(fixtureListDeliverables(engagementId))
    return apiClient.get<EngagementDeliverable[]>(`/engagements/${engagementId}/deliverables`)
  },

  async createDeliverable(input: DeliverableCreateInput): Promise<EngagementDeliverable> {
    if (useFixture()) return Promise.resolve(fixtureCreateDeliverable(input))
    return apiClient.post<EngagementDeliverable>(
      `/engagements/${input.engagement_id}/deliverables`,
      input,
    )
  },

  async updateDeliverableStatus(
    engagementId: string,
    deliverableId: string,
    status: DeliverableStatus,
  ): Promise<EngagementDeliverable> {
    if (useFixture()) return Promise.resolve(fixtureUpdateDeliverableStatus(deliverableId, status))
    return apiClient.patch<EngagementDeliverable>(
      `/engagements/${engagementId}/deliverables/${deliverableId}`,
      { status },
    )
  },

  // ── Time entries ─────────────────────────────────────────────────────────
  async listTimeEntries(engagementId: string): Promise<EngagementTimeEntry[]> {
    if (useFixture()) return Promise.resolve(fixtureListTimeEntries(engagementId))
    return apiClient.get<EngagementTimeEntry[]>(`/engagements/${engagementId}/hours`)
  },

  async logTime(input: TimeEntryCreateInput): Promise<EngagementTimeEntry> {
    if (useFixture()) return Promise.resolve(fixtureCreateTimeEntry(input))
    return apiClient.post<EngagementTimeEntry>(`/engagements/${input.engagement_id}/hours`, input)
  },

  // ── Timeline ──────────────────────────────────────────────────────────────
  async getTimeline(engagementId: string): Promise<EngagementTimelineEvent[]> {
    if (useFixture()) return Promise.resolve(fixtureGetTimeline(engagementId))
    return apiClient.get<EngagementTimelineEvent[]>(`/engagements/${engagementId}/summary`)
  },
}

export type {
  DeliverableCreateInput,
  EngagementCreateInput,
  TimeEntryCreateInput,
} from './engagements-fixture'
