/**
 * In-memory store for Care Callback campaigns (dev-fixture mode).
 *
 * Campaign fixtures (`fixtureListCampaigns`/`fixtureGetCampaign`/`fixtureCreateCampaign`)
 * mirror the real `CallbackCampaign` wire shape and back the real campaign list/detail/
 * create pages in dev.
 *
 * The k-anon aggregate rollup (`fixtureAggregateCampaign`) is a separate, self-contained
 * simulation with no BE counterpart (see care-callbacks.ts header) — it keeps its own
 * private case/outcome shapes rather than the real `OutreachRecord`, since the real BE
 * has no equivalent aggregate-with-k-floor endpoint to model against.
 */

import type { CallbackCampaign, CallbackCampaignAggregate, CallbackQuestionSummary } from '@/types/entities'
import { CareCallbackCampaignStatus } from '@/types/enums'

import { fixtureGetQuestionnaireByCode } from './questionnaires-fixture'

const TENANT = 'tenant-fixture'
const NOW_ISO = '2026-05-08T08:00:00Z'

/** k-anonymity floor — SAD §15 / Assumption A-19 = 10. Mirrored on the BE. */
export const K_ANON_FLOOR = 10

const CAMPAIGN_SEED: CallbackCampaign[] = [
  {
    id: 'cmp-001',
    tenant_id: TENANT,
    client_id: 'fixture-stanbic',
    name: 'Stanbic Q1 wave — anxiety/depression cohort',
    status: CareCallbackCampaignStatus.ACTIVE,
    period_start: '2026-05-01',
    period_end: '2026-05-22',
    target_count: 60,
    completed_count: 4,
    counsellor_pool: ['user-helen', 'user-mary', 'user-job'],
    sampling_notes: 'Stratified by diagnosis bucket; outreach to Q1 mood-related cohort.',
    created_by: 'user-helen',
    activated_at: '2026-05-01T08:00:00Z',
    completed_at: null,
    created_at: '2026-04-29T09:00:00Z',
    updated_at: NOW_ISO,
  },
  {
    id: 'cmp-002',
    tenant_id: TENANT,
    client_id: 'fixture-absa',
    name: 'ABSA renewal pack — 30-day post-CISM check-in',
    status: CareCallbackCampaignStatus.DRAFT,
    period_start: '2026-05-12',
    period_end: '2026-05-30',
    target_count: 14,
    completed_count: 0,
    counsellor_pool: ['user-helen'],
    sampling_notes: '30-day after-action follow-up for the March robbery cohort.',
    created_by: 'user-helen',
    activated_at: null,
    completed_at: null,
    created_at: '2026-05-04T11:30:00Z',
    updated_at: '2026-05-04T11:30:00Z',
  },
]

const campaignStore: CallbackCampaign[] = [...CAMPAIGN_SEED]

export interface CampaignCreateInput {
  client_id: string
  name: string
  period_start: string
  period_end: string
  target_count: number
  counsellor_pool: string[]
  sampling_notes?: string | null
}

export function fixtureListCampaigns(): CallbackCampaign[] {
  return [...campaignStore].sort((a, b) =>
    a.created_at < b.created_at ? 1 : a.created_at > b.created_at ? -1 : 0,
  )
}

export function fixtureGetCampaign(id: string): CallbackCampaign | undefined {
  return campaignStore.find((c) => c.id === id)
}

export function fixtureCreateCampaign(input: CampaignCreateInput): CallbackCampaign {
  const now = new Date().toISOString()
  const campaign: CallbackCampaign = {
    id: `cmp-${Math.random().toString(36).slice(2, 8)}`,
    tenant_id: TENANT,
    status: CareCallbackCampaignStatus.DRAFT,
    completed_count: 0,
    created_by: 'user-helen',
    activated_at: null,
    completed_at: null,
    sampling_notes: input.sampling_notes ?? null,
    created_at: now,
    updated_at: now,
    ...input,
  }
  campaignStore.unshift(campaign)
  return campaign
}

// ── k-anon aggregate simulation (self-contained; no BE equivalent) ─────────

type FixtureOutreachStatus = 'Queued' | 'InProgress' | 'Completed' | 'NoAnswer' | 'Declined' | 'CrisisEscalated'

interface FixtureCase {
  id: string
  campaign_id: string
  status: FixtureOutreachStatus
  outcome_id: string | null
}

interface FixtureOutcome {
  id: string
  case_id: string
  pre_answers: Record<string, string | number | string[] | null>
  post_answers: Record<string, string | number | string[] | null> | null
}

const FIXTURE_QUESTIONNAIRE_CODE = 'joseph-7var-v1'
const PHQ9_ITEM9_KEY = 'phq9_item9'

const CASE_SEED: FixtureCase[] = [
  { id: 'cse-001', campaign_id: 'cmp-001', status: 'Queued', outcome_id: null },
  { id: 'cse-002', campaign_id: 'cmp-001', status: 'InProgress', outcome_id: null },
  { id: 'cse-003', campaign_id: 'cmp-001', status: 'Completed', outcome_id: 'oc-001' },
  { id: 'cse-004', campaign_id: 'cmp-001', status: 'NoAnswer', outcome_id: null },
  { id: 'cse-005', campaign_id: 'cmp-001', status: 'CrisisEscalated', outcome_id: 'oc-002' },
]

const OUTCOME_SEED: FixtureOutcome[] = [
  {
    id: 'oc-001',
    case_id: 'cse-003',
    pre_answers: {
      mood_baseline: 6,
      sleep_quality: 5,
      appetite_change: 'unchanged',
      concentration: 1,
      social_withdrawal: 'no',
      work_function: 1,
      [PHQ9_ITEM9_KEY]: 0,
    },
    post_answers: {
      wos5_cheerful: 4,
      wos5_calm: 4,
      wos5_active: 3,
      wos5_rested: 4,
      wos5_interest: 4,
    },
  },
  {
    id: 'oc-002',
    case_id: 'cse-005',
    pre_answers: {
      mood_baseline: 2,
      sleep_quality: 3,
      appetite_change: 'decreased',
      concentration: 3,
      social_withdrawal: 'yes',
      work_function: 4,
      [PHQ9_ITEM9_KEY]: 2,
    },
    post_answers: null,
  },
]

/**
 * Aggregate rollup. Honours the k-anon floor: when fewer than `K_ANON_FLOOR` completed
 * cases, numeric fields are nulled and `k_floor_met=false`.
 */
export function fixtureAggregateCampaign(campaignId: string): CallbackCampaignAggregate {
  const cases = CASE_SEED.filter((c) => c.campaign_id === campaignId)
  const completed = cases.filter((c) => c.status === 'Completed')
  const completedOutcomes = completed
    .map((c) => OUTCOME_SEED.find((o) => o.id === c.outcome_id))
    .filter((o): o is FixtureOutcome => Boolean(o))

  const kFloorMet = completedOutcomes.length >= K_ANON_FLOOR

  const wos5Deltas = completedOutcomes
    .map((o) => deriveWos5Delta(o))
    .filter((n): n is number => n !== null)
  const wos5Mean = wos5Deltas.length > 0 ? wos5Deltas.reduce((a, b) => a + b, 0) / wos5Deltas.length : null

  const summaries = summariseQuestionnaire(completedOutcomes)

  return {
    campaign_id: campaignId,
    cases_total: cases.length,
    cases_completed: completed.length,
    cases_no_answer: cases.filter((c) => c.status === 'NoAnswer').length,
    cases_declined: cases.filter((c) => c.status === 'Declined').length,
    cases_crisis: cases.filter((c) => c.status === 'CrisisEscalated').length,
    wos5_delta_mean: kFloorMet ? wos5Mean : null,
    question_summaries: kFloorMet ? summaries : summaries.map(redactSummary),
    k_floor_met: kFloorMet,
  }
}

function deriveWos5Delta(o: FixtureOutcome): number | null {
  if (!o.post_answers) return null
  const post = Object.values(o.post_answers).filter((v): v is number => typeof v === 'number')
  if (post.length === 0) return null
  const postMean = post.reduce((a, b) => a + b, 0) / post.length
  return Number.isFinite(postMean) ? Number(postMean.toFixed(2)) : null
}

function summariseQuestionnaire(outcomes: FixtureOutcome[]): CallbackQuestionSummary[] {
  const questionnaire = fixtureGetQuestionnaireByCode(FIXTURE_QUESTIONNAIRE_CODE)
  if (!questionnaire) return []
  return questionnaire.questions.map((q) => {
    const values = outcomes
      .map((o) => o.pre_answers[q.key])
      .filter((v) => v !== undefined && v !== null)
    const numeric = values.filter((v): v is number => typeof v === 'number')
    if (numeric.length > 0 && numeric.length === values.length) {
      const mean = numeric.reduce((a, b) => a + b, 0) / numeric.length
      return {
        question_key: q.key,
        prompt: q.prompt,
        mean: Number(mean.toFixed(2)),
        histogram: null,
        n: numeric.length,
      }
    }
    const histogram: Record<string, number> = {}
    for (const v of values) {
      const k = Array.isArray(v) ? v.join('|') : String(v)
      histogram[k] = (histogram[k] ?? 0) + 1
    }
    return {
      question_key: q.key,
      prompt: q.prompt,
      mean: null,
      histogram,
      n: values.length,
    }
  })
}

function redactSummary(s: CallbackQuestionSummary): CallbackQuestionSummary {
  return { ...s, mean: null, histogram: null }
}
