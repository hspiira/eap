/**
 * Care Callback API — the Phase 3 flagship surface.
 *
 * Fixture-driven until BE Phase 3 #1 lands. Toggle with
 * `VITE_CARE_CALLBACKS_USE_FIXTURE=false` to switch the FE to the live endpoints.
 */

import type { CallbackCaseStatus } from '@/types/enums'

import apiClient from '../client'
import type {
  CallbackCampaign,
  CallbackCampaignAggregate,
  CallbackCase,
  CallbackOutcome,
  PaginatedResponse,
} from '../types'
import {
  type CampaignCreateInput,
  fixtureAggregateCampaign,
  fixtureCreateCampaign,
  fixtureGetCampaign,
  fixtureGetCase,
  fixtureGetOutcomeForCase,
  fixtureListCampaigns,
  fixtureListCases,
  fixtureStartCase,
  fixtureSubmitOutcome,
  type OutcomeSubmitInput,
} from './care-callbacks-fixture'

function useFixture(): boolean {
  if (typeof import.meta === 'undefined') return true
  return import.meta.env?.VITE_CARE_CALLBACKS_USE_FIXTURE !== 'false'
}

function paginate<T>(items: T[]): PaginatedResponse<T> {
  return { items, total: items.length, page: 1, limit: items.length, has_more: false }
}

export interface CaseListParams {
  campaign_id?: string
  assigned_user_id?: string
  status?: CallbackCaseStatus
}

export const careCallbacksApi = {
  // ── Campaigns ────────────────────────────────────────────────────────────
  async listCampaigns(): Promise<PaginatedResponse<CallbackCampaign>> {
    if (useFixture()) return Promise.resolve(paginate(fixtureListCampaigns()))
    return apiClient.get<PaginatedResponse<CallbackCampaign>>('/v1/care-callback-campaigns')
  },

  async getCampaign(id: string): Promise<CallbackCampaign> {
    if (useFixture()) {
      const found = fixtureGetCampaign(id)
      if (!found) throw new Error(`Campaign ${id} not found`)
      return Promise.resolve(found)
    }
    return apiClient.get<CallbackCampaign>(`/v1/care-callback-campaigns/${id}`)
  },

  async createCampaign(input: CampaignCreateInput): Promise<CallbackCampaign> {
    if (useFixture()) return Promise.resolve(fixtureCreateCampaign(input))
    return apiClient.post<CallbackCampaign>('/v1/care-callback-campaigns', input)
  },

  async getAggregate(campaignId: string): Promise<CallbackCampaignAggregate> {
    if (useFixture()) return Promise.resolve(fixtureAggregateCampaign(campaignId))
    return apiClient.get<CallbackCampaignAggregate>(
      `/v1/care-callback-campaigns/${campaignId}/aggregate`,
    )
  },

  // ── Cases (worklist) ─────────────────────────────────────────────────────
  async listCases(params: CaseListParams = {}): Promise<PaginatedResponse<CallbackCase>> {
    if (useFixture()) return Promise.resolve(paginate(fixtureListCases(params)))
    return apiClient.get<PaginatedResponse<CallbackCase>>(
      '/v1/care-callback-cases',
      params as Record<string, unknown>,
    )
  },

  async getCase(id: string): Promise<CallbackCase> {
    if (useFixture()) {
      const found = fixtureGetCase(id)
      if (!found) throw new Error(`Case ${id} not found`)
      return Promise.resolve(found)
    }
    return apiClient.get<CallbackCase>(`/v1/care-callback-cases/${id}`)
  },

  async startCase(id: string): Promise<CallbackCase> {
    if (useFixture()) return Promise.resolve(fixtureStartCase(id))
    return apiClient.post<CallbackCase>(`/v1/care-callback-cases/${id}/start`, {})
  },

  // ── Outcomes ────────────────────────────────────────────────────────────
  async submitOutcome(input: OutcomeSubmitInput): Promise<CallbackOutcome> {
    if (useFixture()) return Promise.resolve(fixtureSubmitOutcome(input))
    return apiClient.post<CallbackOutcome>(
      `/v1/care-callback-cases/${input.case_id}/outcome`,
      input,
    )
  },

  async getOutcomeForCase(caseId: string): Promise<CallbackOutcome | null> {
    if (useFixture()) return Promise.resolve(fixtureGetOutcomeForCase(caseId) ?? null)
    return apiClient.get<CallbackOutcome | null>(
      `/v1/care-callback-cases/${caseId}/outcome`,
    )
  },
}

export type { CampaignCreateInput, OutcomeSubmitInput } from './care-callbacks-fixture'
