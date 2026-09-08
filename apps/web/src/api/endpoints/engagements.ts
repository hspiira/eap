/**
 * Engagement API (Phase 4 #1).
 *
 * BE base path is `/engagements`. The list envelope, filters, sort and paging
 * are the API's; the fixture applies the same ones to its own store
 * (MODULES_REPAIR_PLAN API-01).
 *
 * Deliverables and hours are children of the engagement aggregate: the API
 * embeds both in the detail response and exposes only mutations on the child
 * paths. There is no GET for either, and `/summary` is a summary, not an event
 * feed (MODULES_REPAIR_PLAN ENG-01).
 *
 * Status transitions use per-FSM action routes:
 *   ACTIVE    → POST /engagements/{id}/activate
 *   DELIVERED → POST /engagements/{id}/deliver
 *   INVOICED  → POST /engagements/{id}/invoice
 *   CLOSED    → POST /engagements/{id}/close
 */

import type { DeliverableCreate, EngagementCreate, HoursLogCreate } from "@/api/generated"
import { useFixtures } from "@/lib/fixtures"
import type { DeliverableStatusValue, EngagementStatusValue } from "@/types/entities"
import { EngagementStatus } from "@/types/enums"

import apiClient from "../client"
import type {
  Engagement,
  EngagementDeliverable,
  EngagementList,
  EngagementSummary,
  EngagementTimeEntry,
  ListParams,
} from "../types"
import {
  fixtureAllowedTransitions,
  fixtureCreateDeliverable,
  fixtureCreateEngagement,
  fixtureCreateTimeEntry,
  fixtureGetEngagement,
  fixtureGetSummary,
  fixtureListEngagements,
  fixtureTransitionEngagement,
  fixtureUpdateDeliverableStatus,
} from "./engagements-fixture"

/** Mirrors the query params on `GET /engagements` in the BE OpenAPI schema. */
export interface EngagementListParams extends ListParams {
  status?: EngagementStatusValue
  client_id?: string
}

const FSM_ROUTES: Partial<Record<EngagementStatusValue, string>> = {
  [EngagementStatus.ACTIVE]: "activate",
  [EngagementStatus.DELIVERED]: "deliver",
  [EngagementStatus.INVOICED]: "invoice",
  [EngagementStatus.CLOSED]: "close",
}

export const engagementsApi = {
  // ── Engagements ──────────────────────────────────────────────────────────
  async list(params?: EngagementListParams): Promise<EngagementList> {
    if (useFixtures()) return Promise.resolve(fixtureListEngagements(params))
    return apiClient.get<EngagementList>("/engagements", params)
  },

  async getById(id: string): Promise<Engagement> {
    if (useFixtures()) {
      const found = fixtureGetEngagement(id)
      if (!found) throw new Error(`Engagement ${id} not found`)
      return Promise.resolve(found)
    }
    return apiClient.get<Engagement>(`/engagements/${id}`)
  },

  async create(input: EngagementCreate): Promise<Engagement> {
    if (useFixtures()) return Promise.resolve(fixtureCreateEngagement(input))
    return apiClient.post<Engagement>("/engagements", input)
  },

  async transition(id: string, to: EngagementStatusValue): Promise<Engagement> {
    if (useFixtures()) return Promise.resolve(fixtureTransitionEngagement(id, to))
    const action = FSM_ROUTES[to]
    if (!action) throw new Error(`No FSM route for status: ${to}`)
    return apiClient.post<Engagement>(`/engagements/${id}/${action}`, {})
  },

  /** Static FSM helper: valid in fixture and live modes. */
  allowedTransitions(from: EngagementStatusValue): EngagementStatusValue[] {
    return fixtureAllowedTransitions(from)
  },

  /** Totals, deliverable mix and hours-by-user. A summary, not an event feed. */
  async getSummary(id: string): Promise<EngagementSummary> {
    if (useFixtures()) return Promise.resolve(fixtureGetSummary(id))
    return apiClient.get<EngagementSummary>(`/engagements/${id}/summary`)
  },

  // ── Deliverables ─────────────────────────────────────────────────────────
  async createDeliverable(
    engagementId: string,
    input: DeliverableCreate,
  ): Promise<EngagementDeliverable> {
    if (useFixtures()) return Promise.resolve(fixtureCreateDeliverable(engagementId, input))
    return apiClient.post<EngagementDeliverable>(`/engagements/${engagementId}/deliverables`, input)
  },

  async updateDeliverableStatus(
    engagementId: string,
    deliverableId: string,
    status: DeliverableStatusValue,
  ): Promise<EngagementDeliverable> {
    if (useFixtures())
      return Promise.resolve(fixtureUpdateDeliverableStatus(engagementId, deliverableId, status))
    return apiClient.patch<EngagementDeliverable>(
      `/engagements/${engagementId}/deliverables/${deliverableId}`,
      { status },
    )
  },

  // ── Hours ────────────────────────────────────────────────────────────────
  async logTime(engagementId: string, input: HoursLogCreate): Promise<EngagementTimeEntry> {
    if (useFixtures()) return Promise.resolve(fixtureCreateTimeEntry(engagementId, input))
    return apiClient.post<EngagementTimeEntry>(`/engagements/${engagementId}/hours`, input)
  },
}

export type { DeliverableCreate, EngagementCreate, HoursLogCreate }
