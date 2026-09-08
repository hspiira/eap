/**
 * Survey campaign in-memory store. Replaced by BE Phase 3 #3 endpoints.
 *
 * Records carry the API's `SurveyCampaignResponse` shape, and listing goes
 * through the shared fixture pager, so fixture mode answers the same envelope
 * and applies the same filters as the API (MODULES_REPAIR_PLAN API-01).
 *
 * The aggregate computation respects a k-anon floor (= 10, matching
 * care-callbacks) so the FE never has to hide rows itself.
 */

import type { SurveyCampaignCreate } from "@/api/generated"
import type { Survey, SurveyAggregate, SurveyQuestionSummary } from "@/types/entities"
import { SurveyCampaignStatus, SurveySource } from "@/types/enums"

import { fixturePage, type FixturePageEnvelope } from "./fixture-page"
import type { SurveyListParams } from "./surveys"

const TENANT = "tenant-fixture"
const CREATED_BY = "user-fixture"

/** k-anon floor for survey aggregates. Mirrors care-callbacks. */
export const SURVEY_K_FLOOR = 10

/**
 * Synthetic responses keyed off the survey id. We expose a stable seed so the FE can
 * exercise the "k-floor met" path on `srv-001` and the "insufficient data" path on `srv-002`.
 */
const RESPONSES: Record<string, SurveyResponse[]> = {
  "srv-001": buildResponses(28),
  "srv-002": buildResponses(4),
}

interface SurveyResponse {
  satisfaction: number // 1-5
  nps_bucket: "promoter" | "passive" | "detractor"
  delivery_quality: number // 1-5
  recommend: "yes" | "no"
}

function buildResponses(n: number): SurveyResponse[] {
  const items: SurveyResponse[] = []
  for (let i = 0; i < n; i++) {
    const sat = ((i * 7) % 5) + 1
    items.push({
      satisfaction: sat,
      nps_bucket: sat >= 4 ? "promoter" : sat <= 2 ? "detractor" : "passive",
      delivery_quality: ((i * 3) % 5) + 1,
      recommend: i % 4 === 0 ? "no" : "yes",
    })
  }
  return items
}

/**
 * The questions a live campaign may report on. `nps_bucket` is deliberately
 * absent: the fixture should exercise the rule that an answer outside the
 * approved set is counted as unapproved and its text discarded, not quietly
 * reported.
 */
const APPROVED_QUESTIONS = [
  {
    key: "satisfaction",
    label: "How satisfied were you with the support you received?",
    choices: ["1", "2", "3", "4", "5"],
  },
  { key: "recommend", label: "Would you recommend the service?", choices: ["yes", "no"] },
]

const SEED: Survey[] = [
  {
    id: "srv-001",
    tenant_id: TENANT,
    client_id: "fixture-stanbic",
    name: "Stanbic Q1 EAP satisfaction",
    status: SurveyCampaignStatus.ACTIVE,
    approved_questions: APPROVED_QUESTIONS,
    source: SurveySource.GOOGLE_FORMS,
    external_form_id: "1FAIpQLSf-stanbic-q1",
    period_start: "2026-04-15",
    period_end: "2026-05-31",
    anonymous: true,
    activated_at: "2026-04-15T09:00:00Z",
    closed_at: null,
    response_count: RESPONSES["srv-001"].length,
    created_by: CREATED_BY,
    created_at: "2026-04-12T10:00:00Z",
    updated_at: "2026-05-07T18:00:00Z",
  },
  {
    id: "srv-002",
    tenant_id: TENANT,
    client_id: "fixture-absa",
    name: "ABSA branch debrief: March cohort",
    status: SurveyCampaignStatus.ACTIVE,
    approved_questions: APPROVED_QUESTIONS,
    source: SurveySource.GOOGLE_FORMS,
    external_form_id: "1FAIpQLSf-absa-march",
    period_start: "2026-04-01",
    period_end: "2026-05-15",
    anonymous: true,
    activated_at: "2026-04-01T09:00:00Z",
    closed_at: null,
    response_count: RESPONSES["srv-002"].length,
    created_by: CREATED_BY,
    created_at: "2026-04-01T09:00:00Z",
    updated_at: "2026-05-07T18:00:00Z",
  },
]

const surveyStore: Survey[] = [...SEED]

/** The API's own create shape. The secret is input only; it is never returned. */
export type SurveyCreateInput = SurveyCampaignCreate

export function fixtureListSurveys(params?: SurveyListParams): FixturePageEnvelope<Survey> {
  return fixturePage(surveyStore, params, {
    search: ["name", "client_id", "source"],
    equals: ["status", "client_id"],
    defaultSort: "created_at",
  })
}

export function fixtureGetSurvey(id: string): Survey | undefined {
  return surveyStore.find((s) => s.id === id)
}

export function fixtureCreateSurvey(input: SurveyCreateInput): Survey {
  const now = new Date().toISOString()
  const survey: Survey = {
    id: `srv-${Math.random().toString(36).slice(2, 8)}`,
    tenant_id: TENANT,
    client_id: input.client_id,
    name: input.name,
    status: SurveyCampaignStatus.DRAFT,
    approved_questions: [],
    source: input.source,
    external_form_id: input.external_form_id,
    period_start: input.period_start ?? null,
    period_end: input.period_end ?? null,
    anonymous: input.anonymous ?? true,
    activated_at: null,
    closed_at: null,
    response_count: 0,
    created_by: CREATED_BY,
    created_at: now,
    updated_at: now,
  }
  surveyStore.unshift(survey)
  return survey
}

function fixtureTransition(id: string, status: SurveyCampaignStatus): Survey {
  const target = surveyStore.find((s) => s.id === id)
  if (!target) throw new Error(`Survey ${id} not found`)
  const now = new Date().toISOString()
  target.status = status
  target.updated_at = now
  if (status === SurveyCampaignStatus.ACTIVE) target.activated_at = now
  if (status === SurveyCampaignStatus.CLOSED) target.closed_at = now
  return target
}

export function fixtureActivateSurvey(id: string): Survey {
  return fixtureTransition(id, SurveyCampaignStatus.ACTIVE)
}

export function fixtureCloseSurvey(id: string): Survey {
  return fixtureTransition(id, SurveyCampaignStatus.CLOSED)
}

export function fixtureSurveyAggregate(id: string): SurveyAggregate {
  const survey = surveyStore.find((s) => s.id === id)
  if (!survey) throw new Error(`Survey ${id} not found`)
  const responses = RESPONSES[id] ?? []
  const k_floor_met = responses.length >= SURVEY_K_FLOOR

  const satMean =
    responses.length > 0
      ? responses.reduce((acc, r) => acc + r.satisfaction, 0) / responses.length
      : null
  const promoters = responses.filter((r) => r.nps_bucket === "promoter").length
  const detractors = responses.filter((r) => r.nps_bucket === "detractor").length
  const nps =
    responses.length > 0 ? Math.round(((promoters - detractors) / responses.length) * 100) : null

  const summaries: SurveyQuestionSummary[] = [
    {
      question_key: "satisfaction",
      prompt: "Overall satisfaction with the engagement (1-5)",
      mean: k_floor_met ? Number(satMean!.toFixed(2)) : null,
      histogram: null,
      n: responses.length,
    },
    {
      question_key: "delivery_quality",
      prompt: "Quality of the counsellor / facilitator (1-5)",
      mean: k_floor_met
        ? Number(
            (responses.reduce((a, r) => a + r.delivery_quality, 0) / responses.length).toFixed(2),
          )
        : null,
      histogram: null,
      n: responses.length,
    },
    {
      question_key: "recommend",
      prompt: "Would you recommend the service to a colleague?",
      mean: null,
      histogram: k_floor_met ? buildHistogram(responses, (r) => r.recommend) : null,
      n: responses.length,
    },
  ]

  return {
    survey_id: id,
    response_count: responses.length,
    satisfaction_mean: k_floor_met ? Number(satMean!.toFixed(2)) : null,
    nps: k_floor_met ? nps : null,
    question_summaries: summaries,
    k_floor_met,
  }
}

function buildHistogram<T>(rows: T[], pick: (row: T) => string): Record<string, number> {
  const out: Record<string, number> = {}
  for (const r of rows) {
    const k = pick(r)
    out[k] = (out[k] ?? 0) + 1
  }
  return out
}
