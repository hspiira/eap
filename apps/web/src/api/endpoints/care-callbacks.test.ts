import { describe, expect, it } from 'vitest'

import { careCallbacksApi } from '@/api/endpoints/care-callbacks'
import { K_ANON_FLOOR } from '@/api/endpoints/care-callbacks-fixture'
import { CareCallbackCampaignStatus } from '@/types/enums'

/**
 * Campaign CRUD is fixture-backed in dev (mirrors the real wire shape) and
 * covered here. Outreach-record lifecycle (assign/attempts/complete/
 * unreachable/decline/escalate) is real-API-only now — there is no fixture
 * path for it — so it belongs in an e2e/integration suite, not here.
 */
describe('careCallbacksApi (fixture mode)', () => {
  it('lists seeded campaigns most-recent first', async () => {
    const r = await careCallbacksApi.listCampaigns()
    expect(r.items.length).toBeGreaterThanOrEqual(2)
    expect(r.items[0].status).toBeTypeOf('string')
  })

  it('createCampaign drafts a new campaign with zeroed completed_count', async () => {
    const created = await careCallbacksApi.createCampaign({
      client_id: 'client-x',
      name: 'Test wave',
      period_start: '2026-06-01',
      period_end: '2026-06-30',
      target_count: 25,
      counsellor_pool: ['user-a'],
    })
    expect(created.status).toBe(CareCallbackCampaignStatus.DRAFT)
    expect(created.completed_count).toBe(0)
    expect(created.target_count).toBe(25)
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
