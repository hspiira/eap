/**
 * In-memory store for the Phase 3 flagship — Counsellor-Initiated Care Calls.
 *
 * Models three layers:
 *   - `CallbackCampaign`: audience + sampling + counsellor pool.
 *   - `CallbackCase`: one person × campaign worklist row.
 *   - `CallbackOutcome`: triage submission with crisis flag.
 *
 * Replaced by BE endpoints when Phase 3 BE #1 lands. Fixture is intentionally tiny
 * — large enough to exercise every UI state, small enough to reason about.
 */

import type {
  CallbackCampaign,
  CallbackCampaignAggregate,
  CallbackCase,
  CallbackOutcome,
  CallbackQuestionSummary,
} from '@/types/entities'
import {
  CallbackCampaignStatus,
  CallbackCaseStatus,
  CallbackSamplingStrategy,
} from '@/types/enums'

import {
  evaluateCrisisRules,
  fixtureGetQuestionnaireByCode,
  PHQ9_ITEM9_KEY,
} from './questionnaires-fixture'

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
    description:
      'Outreach to employees seen in Q1 with mood-related diagnoses. Joseph 7-var pre + WOS-5 post.',
    status: CallbackCampaignStatus.ACTIVE,
    period_start: '2026-05-01',
    period_end: '2026-05-22',
    sampling: CallbackSamplingStrategy.STRATIFIED,
    sample_size: 60,
    counsellor_user_ids: ['user-helen', 'user-mary', 'user-job'],
    questionnaire_code: 'joseph-7var-v1',
    followup_questionnaire_code: 'wos5-post-v1',
    case_count: 12,
    cases_completed: 4,
    cases_in_progress: 1,
    created_at: '2026-04-29T09:00:00Z',
    updated_at: NOW_ISO,
  },
  {
    id: 'cmp-002',
    tenant_id: TENANT,
    client_id: 'fixture-absa',
    name: 'ABSA renewal pack — 30-day post-CISM check-in',
    description:
      '30-day after-action follow-up for the March robbery cohort. Voluntary participation.',
    status: CallbackCampaignStatus.SCHEDULED,
    period_start: '2026-05-12',
    period_end: '2026-05-30',
    sampling: CallbackSamplingStrategy.FULL,
    sample_size: null,
    counsellor_user_ids: ['user-helen'],
    questionnaire_code: 'joseph-7var-v1',
    followup_questionnaire_code: 'wos5-post-v1',
    case_count: 14,
    cases_completed: 0,
    cases_in_progress: 0,
    created_at: '2026-05-04T11:30:00Z',
    updated_at: '2026-05-04T11:30:00Z',
  },
]

const CASE_SEED: CallbackCase[] = [
  {
    id: 'cse-001',
    tenant_id: TENANT,
    campaign_id: 'cmp-001',
    person_id: 'pers-001',
    person_display_name: 'Employee #4821',
    source_session_id: 'sess-pl-1',
    assigned_user_id: 'user-helen',
    status: CallbackCaseStatus.QUEUED,
    started_at: null,
    closed_at: null,
    next_attempt_at: null,
    attempt_count: 0,
    outcome_id: null,
    crisis_flagged: false,
    created_at: '2026-05-01T08:00:00Z',
    updated_at: '2026-05-01T08:00:00Z',
  },
  {
    id: 'cse-002',
    tenant_id: TENANT,
    campaign_id: 'cmp-001',
    person_id: 'pers-002',
    person_display_name: 'Employee #5102',
    source_session_id: 'sess-pl-2',
    assigned_user_id: 'user-helen',
    status: CallbackCaseStatus.IN_PROGRESS,
    started_at: '2026-05-07T14:10:00Z',
    closed_at: null,
    next_attempt_at: null,
    attempt_count: 1,
    outcome_id: null,
    crisis_flagged: false,
    created_at: '2026-05-01T08:00:00Z',
    updated_at: '2026-05-07T14:10:00Z',
  },
  {
    id: 'cse-003',
    tenant_id: TENANT,
    campaign_id: 'cmp-001',
    person_id: 'pers-003',
    person_display_name: 'Employee #1188',
    source_session_id: 'sess-pl-3',
    assigned_user_id: 'user-helen',
    status: CallbackCaseStatus.COMPLETED,
    started_at: '2026-05-05T09:30:00Z',
    closed_at: '2026-05-05T09:55:00Z',
    next_attempt_at: null,
    attempt_count: 1,
    outcome_id: 'oc-001',
    crisis_flagged: false,
    created_at: '2026-05-01T08:00:00Z',
    updated_at: '2026-05-05T09:55:00Z',
  },
  {
    id: 'cse-004',
    tenant_id: TENANT,
    campaign_id: 'cmp-001',
    person_id: 'pers-004',
    person_display_name: 'Employee #6601',
    source_session_id: 'sess-pl-4',
    assigned_user_id: 'user-mary',
    status: CallbackCaseStatus.NO_ANSWER,
    started_at: '2026-05-03T11:00:00Z',
    closed_at: '2026-05-03T11:05:00Z',
    next_attempt_at: '2026-05-10T11:00:00Z',
    attempt_count: 2,
    outcome_id: null,
    crisis_flagged: false,
    created_at: '2026-05-01T08:00:00Z',
    updated_at: '2026-05-03T11:05:00Z',
  },
  {
    id: 'cse-005',
    tenant_id: TENANT,
    campaign_id: 'cmp-001',
    person_id: 'pers-005',
    person_display_name: 'Employee #7720',
    source_session_id: 'sess-pl-5',
    assigned_user_id: 'user-mary',
    status: CallbackCaseStatus.CRISIS_ESCALATED,
    started_at: '2026-05-06T10:15:00Z',
    closed_at: '2026-05-06T10:40:00Z',
    next_attempt_at: null,
    attempt_count: 1,
    outcome_id: 'oc-002',
    crisis_flagged: true,
    created_at: '2026-05-01T08:00:00Z',
    updated_at: '2026-05-06T10:40:00Z',
  },
]

const OUTCOME_SEED: CallbackOutcome[] = [
  {
    id: 'oc-001',
    case_id: 'cse-003',
    questionnaire_code: 'joseph-7var-v1',
    followup_questionnaire_code: 'wos5-post-v1',
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
    counsellor_notes: 'Coping well; no further escalation needed.',
    crisis_flagged: false,
    crisis_reasons: [],
    recorded_at: '2026-05-05T09:55:00Z',
    recorded_by_user_id: 'user-helen',
  },
  {
    id: 'oc-002',
    case_id: 'cse-005',
    questionnaire_code: 'joseph-7var-v1',
    followup_questionnaire_code: 'wos5-post-v1',
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
    counsellor_notes: 'Crisis protocol invoked. Warm handoff to on-call psychiatrist.',
    crisis_flagged: true,
    crisis_reasons: ['PHQ-9 item 9 > 0 — self-harm screen positive'],
    recorded_at: '2026-05-06T10:40:00Z',
    recorded_by_user_id: 'user-mary',
  },
]

const campaignStore: CallbackCampaign[] = [...CAMPAIGN_SEED]
const caseStore: CallbackCase[] = [...CASE_SEED]
const outcomeStore: CallbackOutcome[] = [...OUTCOME_SEED]

export interface CampaignCreateInput {
  client_id: string
  name: string
  description?: string | null
  period_start: string
  period_end: string
  sampling: CallbackSamplingStrategy
  sample_size?: number | null
  counsellor_user_ids: string[]
  questionnaire_code: string
  followup_questionnaire_code?: string | null
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
    status: CallbackCampaignStatus.DRAFT,
    case_count: 0,
    cases_completed: 0,
    cases_in_progress: 0,
    created_at: now,
    updated_at: now,
    sample_size: input.sample_size ?? null,
    description: input.description ?? null,
    followup_questionnaire_code: input.followup_questionnaire_code ?? null,
    ...input,
  }
  campaignStore.unshift(campaign)
  return campaign
}

/** Worklist filter — drives the per-counsellor inbox. */
export function fixtureListCases(filter: {
  campaign_id?: string
  assigned_user_id?: string
  status?: CallbackCaseStatus
}): CallbackCase[] {
  return caseStore
    .filter((c) => (filter.campaign_id ? c.campaign_id === filter.campaign_id : true))
    .filter((c) => (filter.assigned_user_id ? c.assigned_user_id === filter.assigned_user_id : true))
    .filter((c) => (filter.status ? c.status === filter.status : true))
    .sort((a, b) => (a.created_at < b.created_at ? -1 : 1))
}

export function fixtureGetCase(id: string): CallbackCase | undefined {
  return caseStore.find((c) => c.id === id)
}

export function fixtureStartCase(caseId: string): CallbackCase {
  const target = caseStore.find((c) => c.id === caseId)
  if (!target) throw new Error(`Case ${caseId} not found`)
  if (target.status === CallbackCaseStatus.COMPLETED || target.status === CallbackCaseStatus.CRISIS_ESCALATED) {
    return target
  }
  target.status = CallbackCaseStatus.IN_PROGRESS
  target.started_at = target.started_at ?? new Date().toISOString()
  target.attempt_count += 1
  target.updated_at = new Date().toISOString()
  recomputeCampaignCounts(target.campaign_id)
  return target
}

export interface OutcomeSubmitInput {
  case_id: string
  questionnaire_code: string
  followup_questionnaire_code?: string | null
  pre_answers: Record<string, string | number | string[] | null>
  post_answers?: Record<string, string | number | string[] | null> | null
  counsellor_notes?: string | null
  /** Final case status to transition to (`COMPLETED`, `NO_ANSWER`, `DECLINED`). */
  final_status: CallbackCaseStatus
  recorded_by_user_id: string
}

export function fixtureSubmitOutcome(input: OutcomeSubmitInput): CallbackOutcome {
  const target = caseStore.find((c) => c.id === input.case_id)
  if (!target) throw new Error(`Case ${input.case_id} not found`)
  const reasons = evaluateCrisisRules(input.pre_answers)
  const crisis = reasons.length > 0
  const now = new Date().toISOString()
  const outcome: CallbackOutcome = {
    id: `oc-${Math.random().toString(36).slice(2, 8)}`,
    case_id: input.case_id,
    questionnaire_code: input.questionnaire_code,
    followup_questionnaire_code: input.followup_questionnaire_code ?? null,
    pre_answers: input.pre_answers,
    post_answers: input.post_answers ?? null,
    counsellor_notes: input.counsellor_notes ?? null,
    crisis_flagged: crisis,
    crisis_reasons: reasons,
    recorded_at: now,
    recorded_by_user_id: input.recorded_by_user_id,
  }
  outcomeStore.push(outcome)
  target.outcome_id = outcome.id
  target.crisis_flagged = crisis
  target.status = crisis ? CallbackCaseStatus.CRISIS_ESCALATED : input.final_status
  target.closed_at = now
  target.updated_at = now
  recomputeCampaignCounts(target.campaign_id)
  return outcome
}

export function fixtureGetOutcomeForCase(caseId: string): CallbackOutcome | undefined {
  return outcomeStore.find((o) => o.case_id === caseId)
}

function recomputeCampaignCounts(campaignId: string) {
  const campaign = campaignStore.find((c) => c.id === campaignId)
  if (!campaign) return
  const cases = caseStore.filter((c) => c.campaign_id === campaignId)
  campaign.case_count = cases.length
  campaign.cases_completed = cases.filter(
    (c) =>
      c.status === CallbackCaseStatus.COMPLETED || c.status === CallbackCaseStatus.CRISIS_ESCALATED,
  ).length
  campaign.cases_in_progress = cases.filter((c) => c.status === CallbackCaseStatus.IN_PROGRESS).length
  campaign.updated_at = new Date().toISOString()
}

/**
 * Aggregate rollup. Honours the k-anon floor: when fewer than `K_ANON_FLOOR` completed
 * cases, numeric fields are nulled and `k_floor_met=false`. The renewal pack renderer
 * will surface an explicit "insufficient data" state in that case.
 */
export function fixtureAggregateCampaign(campaignId: string): CallbackCampaignAggregate {
  const campaign = campaignStore.find((c) => c.id === campaignId)
  if (!campaign) throw new Error(`Campaign ${campaignId} not found`)
  const cases = caseStore.filter((c) => c.campaign_id === campaignId)
  const completed = cases.filter((c) => c.status === CallbackCaseStatus.COMPLETED)
  const completedOutcomes = completed
    .map((c) => outcomeStore.find((o) => o.id === c.outcome_id))
    .filter((o): o is CallbackOutcome => Boolean(o))

  const kFloorMet = completedOutcomes.length >= K_ANON_FLOOR

  const wos5Deltas = completedOutcomes
    .map((o) => deriveWos5Delta(o))
    .filter((n): n is number => n !== null)
  const wos5Mean = wos5Deltas.length > 0 ? wos5Deltas.reduce((a, b) => a + b, 0) / wos5Deltas.length : null

  const summaries = summariseQuestionnaire(campaign.questionnaire_code, completedOutcomes)

  return {
    campaign_id: campaignId,
    cases_total: cases.length,
    cases_completed: completed.length,
    cases_no_answer: cases.filter((c) => c.status === CallbackCaseStatus.NO_ANSWER).length,
    cases_declined: cases.filter((c) => c.status === CallbackCaseStatus.DECLINED).length,
    cases_crisis: cases.filter((c) => c.status === CallbackCaseStatus.CRISIS_ESCALATED).length,
    wos5_delta_mean: kFloorMet ? wos5Mean : null,
    question_summaries: kFloorMet ? summaries : summaries.map(redactSummary),
    k_floor_met: kFloorMet,
  }
}

function deriveWos5Delta(o: CallbackOutcome): number | null {
  if (!o.post_answers) return null
  const post = Object.values(o.post_answers).filter((v): v is number => typeof v === 'number')
  if (post.length === 0) return null
  const postMean = post.reduce((a, b) => a + b, 0) / post.length
  return Number.isFinite(postMean) ? Number(postMean.toFixed(2)) : null
}

function summariseQuestionnaire(code: string, outcomes: CallbackOutcome[]): CallbackQuestionSummary[] {
  const questionnaire = fixtureGetQuestionnaireByCode(code)
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
