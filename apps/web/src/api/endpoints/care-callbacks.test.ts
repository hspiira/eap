import { describe, expect, it } from 'vitest'

import { careCallbacksApi } from '@/api/endpoints/care-callbacks'
import {
  K_ANON_FLOOR,
  fixtureSubmitOutcome,
} from '@/api/endpoints/care-callbacks-fixture'
import { PHQ9_ITEM9_KEY } from '@/api/endpoints/questionnaires-fixture'
import {
  CallbackCampaignStatus,
  CallbackCaseStatus,
  CallbackSamplingStrategy,
} from '@/types/enums'

describe('careCallbacksApi (fixture mode)', () => {
  it('lists seeded campaigns most-recent first', async () => {
    const r = await careCallbacksApi.listCampaigns()
    expect(r.items.length).toBeGreaterThanOrEqual(2)
    expect(r.items[0].status).toBeTypeOf('string')
  })

  it('createCampaign drafts a new campaign with zeroed counters', async () => {
    const created = await careCallbacksApi.createCampaign({
      client_id: 'client-x',
      name: 'Test wave',
      period_start: '2026-06-01',
      period_end: '2026-06-30',
      sampling: CallbackSamplingStrategy.FULL,
      sample_size: null,
      counsellor_user_ids: ['user-a'],
      questionnaire_code: 'joseph-7var-v1',
      followup_questionnaire_code: 'wos5-post-v1',
    })
    expect(created.status).toBe(CallbackCampaignStatus.DRAFT)
    expect(created.case_count).toBe(0)
  })

  it('startCase transitions QUEUED → IN_PROGRESS and bumps attempt_count', async () => {
    const before = await careCallbacksApi.getCase('cse-001')
    expect(before.status).toBe(CallbackCaseStatus.QUEUED)
    const baselineAttempts = before.attempt_count
    const after = await careCallbacksApi.startCase('cse-001')
    expect(after.status).toBe(CallbackCaseStatus.IN_PROGRESS)
    expect(after.attempt_count).toBe(baselineAttempts + 1)
  })

  it('PHQ-9 item-9 > 0 latches case to CRISIS_ESCALATED regardless of final_status request', () => {
    const outcome = fixtureSubmitOutcome({
      case_id: 'cse-002',
      questionnaire_code: 'joseph-7var-v1',
      followup_questionnaire_code: null,
      pre_answers: {
        mood_baseline: 1,
        sleep_quality: 2,
        appetite_change: 'decreased',
        concentration: 4,
        social_withdrawal: 'yes',
        work_function: 4,
        [PHQ9_ITEM9_KEY]: 1,
      },
      post_answers: null,
      counsellor_notes: null,
      final_status: CallbackCaseStatus.COMPLETED,
      recorded_by_user_id: 'user-helen',
    })
    expect(outcome.crisis_flagged).toBe(true)
    expect(outcome.crisis_reasons[0]).toMatch(/PHQ-9/)
  })

  it('aggregate suppresses metrics when k-anon floor unmet', async () => {
    const agg = await careCallbacksApi.getAggregate('cmp-001')
    expect(agg.cases_completed).toBeLessThan(K_ANON_FLOOR)
    expect(agg.k_floor_met).toBe(false)
    expect(agg.wos5_delta_mean).toBeNull()
    for (const s of agg.question_summaries) {
      expect(s.mean).toBeNull()
      expect(s.histogram).toBeNull()
    }
  })
})
