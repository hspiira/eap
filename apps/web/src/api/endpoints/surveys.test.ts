import { describe, expect, it } from 'vitest'

import { surveysApi } from '@/api/endpoints/surveys'
import { SURVEY_K_FLOOR } from '@/api/endpoints/surveys-fixture'
import { SurveySource, SurveyStatus } from '@/types/enums'

describe('surveysApi (fixture mode)', () => {
  it('lists seeded surveys most-recent first', async () => {
    const r = await surveysApi.list()
    expect(r.items.length).toBeGreaterThanOrEqual(2)
  })

  it('aggregate exposes metrics when k-floor met (srv-001)', async () => {
    const agg = await surveysApi.getAggregate('srv-001')
    expect(agg.response_count).toBeGreaterThanOrEqual(SURVEY_K_FLOOR)
    expect(agg.k_floor_met).toBe(true)
    expect(agg.satisfaction_mean).not.toBeNull()
    expect(agg.nps).not.toBeNull()
  })

  it('aggregate suppresses metrics when k-floor unmet (srv-002)', async () => {
    const agg = await surveysApi.getAggregate('srv-002')
    expect(agg.response_count).toBeLessThan(SURVEY_K_FLOOR)
    expect(agg.k_floor_met).toBe(false)
    expect(agg.satisfaction_mean).toBeNull()
    expect(agg.nps).toBeNull()
    for (const s of agg.question_summaries) {
      expect(s.mean).toBeNull()
      expect(s.histogram).toBeNull()
    }
  })

  it('create drafts a survey with webhook URL + token', async () => {
    const created = await surveysApi.create({
      client_id: 'client-x',
      name: 'New survey',
      description: null,
      source: SurveySource.GOOGLE_FORMS,
      period_start: '2026-06-01',
      period_end: '2026-06-30',
    })
    expect(created.status).toBe(SurveyStatus.DRAFT)
    expect(created.webhook_url).toContain(created.id)
    expect(created.webhook_token.startsWith('sk-')).toBe(true)
  })

  it('rotateWebhookToken changes the token in place', async () => {
    const before = await surveysApi.getById('srv-001')
    const beforeToken = before.webhook_token
    const after = await surveysApi.rotateWebhookToken('srv-001')
    expect(after.webhook_token).not.toBe(beforeToken)
    expect(after.webhook_token.startsWith('sk-')).toBe(true)
  })

  it('close transitions the survey to CLOSED', async () => {
    const closed = await surveysApi.close('srv-002')
    expect(closed.status).toBe(SurveyStatus.CLOSED)
    expect(closed.closed_at).not.toBeNull()
  })
})
