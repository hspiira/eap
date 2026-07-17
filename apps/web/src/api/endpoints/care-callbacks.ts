/**
 * Care callback API — Phase 3 #1.
 *
 * BE base paths (confirmed via openapi.json):
 *   Campaigns → `/care-callback-campaigns`
 *   Cases     → `/outreach-records`          (was `care-callback-cases`)
 *
 * Fixture is DEV-only.
 *
 * Note: `startCase` maps to `POST /outreach-records/{id}/assign` for now;
 * the full FSM split (P3 #1) will refine this into per-state transitions.
 */

import { useFixtures } from '@/lib/fixtures'
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
    if (useFixtures()) return Promise.resolve(paginate(fixtureListCampaigns()))
    return apiClient.get<PaginatedResponse<CallbackCampaign>>('/care-callback-campaigns')
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

  async getAggregate(campaignId: string): Promise<CallbackCampaignAggregate> {
    if (useFixtures()) return Promise.resolve(fixtureAggregateCampaign(campaignId))
    return apiClient.get<CallbackCampaignAggregate>(
      `/care-callback-campaigns/${campaignId}/summary`,
    )
  },

  // ── Cases (worklist) ─────────────────────────────────────────────────────
  async listCases(params: CaseListParams = {}): Promise<PaginatedResponse<CallbackCase>> {
    if (useFixtures()) return Promise.resolve(paginate(fixtureListCases(params)))
    return apiClient.get<PaginatedResponse<CallbackCase>>(
      '/outreach-records',
      params,
    )
  },

  async getCase(id: string): Promise<CallbackCase> {
    if (useFixtures()) {
      const found = fixtureGetCase(id)
      if (!found) throw new Error(`Case ${id} not found`)
      return Promise.resolve(found)
    }
    return apiClient.get<CallbackCase>(`/outreach-records/${id}`)
  },

  async startCase(id: string): Promise<CallbackCase> {
    if (useFixtures()) return Promise.resolve(fixtureStartCase(id))
    return apiClient.post<CallbackCase>(`/outreach-records/${id}/assign`, {})
  },

  // ── Outcomes ─────────────────────────────────────────────────────────────
  async submitOutcome(input: OutcomeSubmitInput): Promise<CallbackOutcome> {
    if (useFixtures()) return Promise.resolve(fixtureSubmitOutcome(input))
    return apiClient.post<CallbackOutcome>(`/outreach-records/${input.case_id}/outcome`, input)
  },

  async getOutcomeForCase(caseId: string): Promise<CallbackOutcome | null> {
    if (useFixtures()) return Promise.resolve(fixtureGetOutcomeForCase(caseId) ?? null)
    return apiClient.get<CallbackOutcome | null>(`/outreach-records/${caseId}/outcome`)
  },
}

export type { CampaignCreateInput, OutcomeSubmitInput } from './care-callbacks-fixture'
