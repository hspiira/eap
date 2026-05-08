import { describe, expect, it } from 'vitest'

import { incidentsApi } from '@/api/endpoints/incidents'
import { IncidentSeverity, IncidentStatus } from '@/types/enums'

describe('incidentsApi (fixture mode)', () => {
  it('lists seeded incidents most-recent first', async () => {
    const r = await incidentsApi.list()
    expect(r.items.length).toBeGreaterThanOrEqual(2)
    for (let i = 1; i < r.items.length; i++) {
      expect(r.items[i - 1].occurred_at >= r.items[i].occurred_at).toBe(true)
    }
  })

  it('getById returns the seeded record', async () => {
    const inc = await incidentsApi.getById('inc-001')
    expect(inc.severity).toBe(IncidentSeverity.CRITICAL)
    expect(inc.status).toBe(IncidentStatus.IN_PROGRESS)
  })

  it('getById throws for unknown id', async () => {
    await expect(incidentsApi.getById('nope')).rejects.toThrow()
  })

  it('getTimeline returns events in chronological order', async () => {
    const events = await incidentsApi.getTimeline('inc-001')
    expect(events.length).toBeGreaterThanOrEqual(2)
    for (let i = 1; i < events.length; i++) {
      expect(events[i - 1].at <= events[i].at).toBe(true)
    }
  })

  it('create appends to the list and seeds a Created timeline event', async () => {
    const before = (await incidentsApi.list()).items.length
    const created = await incidentsApi.create({
      client_id: 'client-x',
      title: 'Test incident',
      description: 'Something happened.',
      severity: IncidentSeverity.LOW,
      occurred_at: new Date().toISOString(),
      affected_population: 5,
    })
    expect(created.status).toBe(IncidentStatus.OPEN)

    const after = (await incidentsApi.list()).items.length
    expect(after).toBe(before + 1)

    const tl = await incidentsApi.getTimeline(created.id)
    expect(tl[0].kind).toBe('Created')
  })

  it('appendNote pushes a Note event', async () => {
    const created = await incidentsApi.create({
      client_id: 'client-x',
      title: 'Note test',
      description: 'Description here.',
      severity: IncidentSeverity.MEDIUM,
      occurred_at: new Date().toISOString(),
      affected_population: 1,
    })
    const event = await incidentsApi.appendNote(created.id, 'Follow-up scheduled.')
    expect(event.kind).toBe('Note')
    expect(event.message).toBe('Follow-up scheduled.')

    const tl = await incidentsApi.getTimeline(created.id)
    expect(tl.some((e) => e.kind === 'Note')).toBe(true)
  })
})
