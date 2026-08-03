/**
 * Care Callbacks API — counsellor-initiated outreach campaigns.
 *
 * BE base paths (confirmed via openapi.json, app/api/routes/care_callbacks.py):
 *   Campaigns → `/care-callback-campaigns`
 *   Outreach  → `/outreach-records` (nested-list only: no bare GET /outreach-records)
 *   Triage    → `/triage/instruments*`, `/outreach-records/{id}/triage*`
 *
 * No `require_clinical_scope` on any of these — Care Callbacks is not behind
 * the clinical privacy wall (person_id is a real reference, unlike Case's
 * pseudonymous clinical_subject_id).
 *
 * `getAggregate` stays fixture-only: the k-anon aggregate report widget
 * (Aggregate tab, wave-summary report) was built against an invented shape
 * with no BE counterpart. `getSummary` below hits the real
 * GET .../summary endpoint with the real CallbackCampaignSummary shape.
 *
 * Triage scoring endpoints are wired here for completeness but have no FE
 * consumer yet — the case-detail page defers instrument-driven scoring
 * (Phase 10).
 */

import { useFixtures } from '@/lib/fixtures'
import type { TriageInstrumentCode, TriageRiskLevel } from '@/types/enums'

import apiClient from '../client'
import type { CallbackCampaign, CallbackCampaignAggregate, CallbackCampaignSummary, OutreachRecord } from '../types'
import {
  fixtureAggregateCampaign,
  fixtureCreateCampaign,
  fixtureGetCampaign,
  fixtureListCampaigns,
} from './care-callbacks-fixture'

export interface CampaignCreateInput {
  client_id: string
  name: string
  period_start: string
  period_end: string
  target_count: number
  counsellor_pool: string[]
  sampling_notes?: string | null
}

export interface OutreachListParams {
  page?: number
  limit?: number
}

export interface OutreachTerminateInput {
  notes?: string | null
}

export interface OutreachEscalateInput {
  notes: string
}

export interface TriageInstrumentItem {
  code: string
  text: string
  min_value: number
  max_value: number
}

export interface TriageInstrument {
  code: TriageInstrumentCode
  version: string
  title: string
  items: TriageInstrumentItem[]
}

export interface TriageScoreInput {
  instrument_code: TriageInstrumentCode
  responses: Record<string, number>
}

export interface TriageScoreResult {
  instrument_code: TriageInstrumentCode
  instrument_version: string
  risk_level: TriageRiskLevel
  crisis_flag: boolean
  crisis_reason?: string | null
  scores: Record<string, unknown>
  derived: Record<string, unknown>
  stage_of_change?: string | null
}

export const careCallbacksApi = {
  // ── Campaigns ────────────────────────────────────────────────────────────
  /** Bare array on the wire — not a PaginatedResponse envelope. */
  async listCampaigns(): Promise<CallbackCampaign[]> {
    if (useFixtures()) return Promise.resolve(fixtureListCampaigns())
    return apiClient.get<CallbackCampaign[]>('/care-callback-campaigns')
  },

  async getCampaign(id: string): Promise<CallbackCampaign> {
    if (useFixtures()) {
      const found = fixtureGetCampaign(id)
      if (!found) throw new Error(`Campaign ${id} not found`)
      return Promise.resolve(found)
    }
    return apiClient.get<CallbackCampaign>(`/care-callback-campaigns/${id}`)
  },

  async createCampaign(input: CampaignCreateInput): Promise<CallbackCampaign> {
    if (useFixtures()) return Promise.resolve(fixtureCreateCampaign(input))
    return apiClient.post<CallbackCampaign>('/care-callback-campaigns', input)
  },

  /** Fixture-only k-anon rollup — no matching BE shape. See file header. */
  async getAggregate(campaignId: string): Promise<CallbackCampaignAggregate> {
    return Promise.resolve(fixtureAggregateCampaign(campaignId))
  },

  /** The real per-campaign summary (`GET .../summary`). */
  async getSummary(campaignId: string): Promise<CallbackCampaignSummary> {
    return apiClient.get<CallbackCampaignSummary>(
      `/care-callback-campaigns/${campaignId}/summary`,
    )
  },

  /** Only valid from Draft; requires a non-empty counsellor_pool (BE domain rule). */
  async activateCampaign(id: string): Promise<CallbackCampaign> {
    return apiClient.post<CallbackCampaign>(`/care-callback-campaigns/${id}/activate`, {})
  },

  /** Only valid from Active. */
  async completeCampaign(id: string): Promise<CallbackCampaign> {
    return apiClient.post<CallbackCampaign>(`/care-callback-campaigns/${id}/complete`, {})
  },

  /** Only valid from Draft or Completed — must complete an Active campaign first. */
  async archiveCampaign(id: string): Promise<CallbackCampaign> {
    return apiClient.post<CallbackCampaign>(`/care-callback-campaigns/${id}/archive`, {})
  },

  /** Only valid while Draft or Active. */
  async updateCounsellorPool(id: string, counsellorPool: string[]): Promise<CallbackCampaign> {
    return apiClient.patch<CallbackCampaign>(`/care-callback-campaigns/${id}/counsellor-pool`, {
      counsellor_pool: counsellorPool,
    })
  },

  /** Enrols persons into the campaign as new Pending outreach records. */
  async enrol(campaignId: string, personIds: string[]): Promise<void> {
    return apiClient.post<void>(`/care-callback-campaigns/${campaignId}/enrol`, {
      person_ids: personIds,
    })
  },

  // ── Outreach records ─────────────────────────────────────────────────────
  /**
   * Campaign-scoped only — the BE has no bare GET /outreach-records collection.
   * page/limit slice the result, but the response is a bare array with no
   * total/has_more — there's no way to tell if more pages exist.
   */
  async listOutreachForCampaign(
    campaignId: string,
    params: OutreachListParams = {},
  ): Promise<OutreachRecord[]> {
    return apiClient.get<OutreachRecord[]>(
      `/care-callback-campaigns/${campaignId}/outreach-records`,
      params,
    )
  },

  async getOutreach(id: string): Promise<OutreachRecord> {
    return apiClient.get<OutreachRecord>(`/outreach-records/${id}`)
  },

  /** Claims a Pending record. Not cross-checked against the campaign's counsellor_pool. */
  async assign(id: string, counsellorId: string): Promise<OutreachRecord> {
    return apiClient.post<OutreachRecord>(`/outreach-records/${id}/assign`, {
      counsellor_id: counsellorId,
    })
  },

  /**
   * Logs a contact attempt. No body. Must already be Assigned (rejects from
   * Pending); first attempt flips Assigned -> Contacted.
   */
  async recordAttempt(id: string): Promise<OutreachRecord> {
    return apiClient.post<OutreachRecord>(`/outreach-records/${id}/attempts`, {})
  },

  /** Must not be Pending or already terminal. */
  async complete(id: string, input: OutreachTerminateInput = {}): Promise<OutreachRecord> {
    return apiClient.post<OutreachRecord>(`/outreach-records/${id}/complete`, input)
  },

  async markUnreachable(id: string, input: OutreachTerminateInput = {}): Promise<OutreachRecord> {
    return apiClient.post<OutreachRecord>(`/outreach-records/${id}/unreachable`, input)
  },

  async markDeclined(id: string, input: OutreachTerminateInput = {}): Promise<OutreachRecord> {
    return apiClient.post<OutreachRecord>(`/outreach-records/${id}/decline`, input)
  },

  /** notes is required and non-empty — enforced by both the schema and the entity. */
  async escalate(id: string, input: OutreachEscalateInput): Promise<OutreachRecord> {
    return apiClient.post<OutreachRecord>(`/outreach-records/${id}/escalate`, input)
  },

  // ── Triage (catalogue + scoring; no FE form wired yet — Phase 10) ────────
  async listTriageInstruments(): Promise<TriageInstrument[]> {
    return apiClient.get<TriageInstrument[]>('/triage/instruments')
  },

  async getTriageInstrument(code: TriageInstrumentCode): Promise<TriageInstrument> {
    return apiClient.get<TriageInstrument>(`/triage/instruments/${code}`)
  },

  /** Validates responses against the instrument, scores server-side, and persists. */
  async scoreTriage(outreachId: string, input: TriageScoreInput): Promise<TriageScoreResult> {
    return apiClient.post<TriageScoreResult>(
      `/outreach-records/${outreachId}/triage/score`,
      input,
    )
  },
}

export type { CampaignCreateInput as FixtureCampaignCreateInput } from './care-callbacks-fixture'
