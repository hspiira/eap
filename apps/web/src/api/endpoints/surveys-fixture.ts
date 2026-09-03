/**
 * Survey campaign in-memory store. Replaced by BE Phase 3 #3 endpoints.
 *
 * The aggregate computation respects a k-anon floor (= 10, matching care-callbacks)
 * so the FE never has to hide rows itself — it just renders what the BE returns.
 */

import type {
  Survey,
  SurveyAggregate,
  SurveyQuestionSummary,
} from '@/types/entities'
import { SurveySource, SurveyStatus } from '@/types/enums'

const TENANT = 'tenant-fixture'

/** k-anon floor for survey aggregates. Mirrors care-callbacks. */
export const SURVEY_K_FLOOR = 10

/**
 * Synthetic responses keyed off the survey id. We expose a stable seed so the FE can
 * exercise the "k-floor met" path on `srv-001` and the "insufficient data" path on `srv-002`.
 */
const RESPONSES: Record<string, SurveyResponse[]> = {
  'srv-001': buildResponses(28),
  'srv-002': buildResponses(4),
}

interface SurveyResponse {
  satisfaction: number // 1-5
  nps_bucket: 'promoter' | 'passive' | 'detractor'
  delivery_quality: number // 1-5
  recommend: 'yes' | 'no'
}

function buildResponses(n: number): SurveyResponse[] {
  const items: SurveyResponse[] = []
  for (let i = 0; i < n; i++) {
    const sat = ((i * 7) % 5) + 1
    items.push({
      satisfaction: sat,
      nps_bucket: sat >= 4 ? 'promoter' : sat <= 2 ? 'detractor' : 'passive',
      delivery_quality: ((i * 3) % 5) + 1,
      recommend: i % 4 === 0 ? 'no' : 'yes',
    })
  }
  return items
}

const SEED: Survey[] = [
  {
    id: 'srv-001',
    tenant_id: TENANT,
    client_id: 'fixture-stanbic',
    name: 'Stanbic Q1 EAP satisfaction',
    description:
      'Anonymous post-engagement survey deployed via Google Forms. Response window covers the Q1 outreach wave.',
    status: SurveyStatus.COLLECTING,
    source: SurveySource.GOOGLE_FORMS,
    webhook_url: 'https://api.evexia.local/v1/surveys/srv-001/responses',
    webhook_token: 'sk-stanbic-q1-7f0c1a',
    period_start: '2026-04-15',
    period_end: '2026-05-31',
    first_response_at: '2026-04-17T08:34:00Z',
    closed_at: null,
    response_count: RESPONSES['srv-001'].length,
    created_at: '2026-04-12T10:00:00Z',
    updated_at: '2026-05-07T18:00:00Z',
  },
  {
    id: 'srv-002',
    tenant_id: TENANT,
    client_id: 'fixture-absa',
    name: 'ABSA branch debrief — March cohort',
    description:
      'Short pulse survey for the post-CISM cohort. Webhook live but volume below the k-anon floor.',
    status: SurveyStatus.COLLECTING,
    source: SurveySource.GOOGLE_FORMS,
    webhook_url: 'https://api.evexia.local/v1/surveys/srv-002/responses',
    webhook_token: 'sk-absa-march-d0a31b',
    period_start: '2026-04-01',
    period_end: '2026-05-15',
    first_response_at: '2026-04-08T12:10:00Z',
    closed_at: null,
    response_count: RESPONSES['srv-002'].length,
    created_at: '2026-04-01T09:00:00Z',
    updated_at: '2026-05-07T18:00:00Z',
  },
]

const surveyStore: Survey[] = [...SEED]

export interface SurveyCreateInput {
  client_id: string
  name: string
  description?: string | null
  source: SurveySource
  period_start: string
  period_end: string
}

export function fixtureListSurveys(): Survey[] {
  return [...surveyStore].sort((a, b) =>
    a.created_at < b.created_at ? 1 : a.created_at > b.created_at ? -1 : 0,
  )
}

export function fixtureGetSurvey(id: string): Survey | undefined {
  return surveyStore.find((s) => s.id === id)
}

export function fixtureCreateSurvey(input: SurveyCreateInput): Survey {
  const now = new Date().toISOString()
  const id = `srv-${Math.random().toString(36).slice(2, 8)}`
  const survey: Survey = {
    id,
    tenant_id: TENANT,
    client_id: input.client_id,
    name: input.name,
    description: input.description ?? null,
    status: SurveyStatus.DRAFT,
    source: input.source,
    webhook_url: `https://api.evexia.local/v1/surveys/${id}/responses`,
    webhook_token: `sk-${Math.random().toString(36).slice(2, 10)}`,
    period_start: input.period_start,
    period_end: input.period_end,
    first_response_at: null,
    closed_at: null,
    response_count: 0,
    created_at: now,
    updated_at: now,
  }
  surveyStore.unshift(survey)
  return survey
}

export function fixtureCloseSurvey(id: string): Survey {
  const target = surveyStore.find((s) => s.id === id)
  if (!target) throw new Error(`Survey ${id} not found`)
  target.status = SurveyStatus.CLOSED
  target.closed_at = new Date().toISOString()
  target.updated_at = target.closed_at
  return target
}

export function fixtureRotateWebhookToken(id: string): Survey {
  const target = surveyStore.find((s) => s.id === id)
  if (!target) throw new Error(`Survey ${id} not found`)
  target.webhook_token = `sk-${Math.random().toString(36).slice(2, 10)}`
  target.updated_at = new Date().toISOString()
  return target
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
  const promoters = responses.filter((r) => r.nps_bucket === 'promoter').length
  const detractors = responses.filter((r) => r.nps_bucket === 'detractor').length
  const nps = responses.length > 0 ? Math.round(((promoters - detractors) / responses.length) * 100) : null

  const summaries: SurveyQuestionSummary[] = [
    {
      question_key: 'satisfaction',
      prompt: 'Overall satisfaction with the engagement (1-5)',
      mean: k_floor_met ? Number(satMean!.toFixed(2)) : null,
      histogram: null,
      n: responses.length,
    },
    {
      question_key: 'delivery_quality',
      prompt: 'Quality of the counsellor / facilitator (1-5)',
      mean: k_floor_met
        ? Number(
            (responses.reduce((a, r) => a + r.delivery_quality, 0) / responses.length).toFixed(2),
          )
        : null,
      histogram: null,
      n: responses.length,
    },
    {
      question_key: 'recommend',
      prompt: 'Would you recommend the service to a colleague?',
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
