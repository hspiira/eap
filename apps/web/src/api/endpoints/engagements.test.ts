import { describe, expect, it } from 'vitest'

import { engagementsApi } from '@/api/endpoints/engagements'
import {
  DeliverableStatus,
  EngagementStatus,
  EngagementType,
} from '@/types/enums'

describe('engagementsApi (fixture mode)', () => {
  it('lists seeded engagements', async () => {
    const r = await engagementsApi.list()
    expect(r.items.length).toBeGreaterThanOrEqual(2)
  })

  it('FSM blocks invalid transitions and allows valid ones', async () => {
    const created = await engagementsApi.create({
      client_id: 'c-1',
      name: 'Smoke FSM',
      engagement_type: EngagementType.ADVISORY,
      start_date: '2026-05-01',
    })
    expect(created.status).toBe(EngagementStatus.SCOPING)

    await expect(
      engagementsApi.transition(created.id, EngagementStatus.CLOSED),
    ).rejects.toThrow(/Cannot transition/)

    const active = await engagementsApi.transition(created.id, EngagementStatus.ACTIVE)
    expect(active.status).toBe(EngagementStatus.ACTIVE)
    const delivered = await engagementsApi.transition(created.id, EngagementStatus.DELIVERED)
    expect(delivered.status).toBe(EngagementStatus.DELIVERED)
  })

  it('logTime rolls hours up into the engagement totals', async () => {
    const created = await engagementsApi.create({
      client_id: 'c-1',
      name: 'Hours rollup',
      engagement_type: EngagementType.ADVISORY,
      start_date: '2026-05-01',
      budget_hours: 10,
    })
    expect(created.hours_logged).toBe(0)

    await engagementsApi.logTime({
      engagement_id: created.id,
      user_id: 'user-helen',
      occurred_on: '2026-05-02',
      hours: 3.5,
    })
    await engagementsApi.logTime({
      engagement_id: created.id,
      user_id: 'user-helen',
      occurred_on: '2026-05-03',
      hours: 2,
    })

    const fresh = await engagementsApi.getById(created.id)
    expect(fresh.hours_logged).toBeCloseTo(5.5)
  })

  it('createDeliverable + status update emits timeline events', async () => {
    const created = await engagementsApi.create({
      client_id: 'c-1',
      name: 'Deliverable test',
      engagement_type: EngagementType.POLICY_DRAFT,
      start_date: '2026-05-01',
    })
    const dlv = await engagementsApi.createDeliverable({
      engagement_id: created.id,
      title: 'Draft v1',
    })
    expect(dlv.status).toBe(DeliverableStatus.PENDING)

    const submitted = await engagementsApi.updateDeliverableStatus(
      created.id,
      dlv.id,
      DeliverableStatus.SUBMITTED,
    )
    expect(submitted.submitted_at).not.toBeNull()

    const timeline = await engagementsApi.getTimeline(created.id)
    expect(timeline.some((e) => e.kind === 'Deliverable Added')).toBe(true)
    expect(timeline.some((e) => e.kind === 'Deliverable Updated')).toBe(true)
  })
})
