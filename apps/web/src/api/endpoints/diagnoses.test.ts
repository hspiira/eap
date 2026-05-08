import { describe, expect, it } from 'vitest'

import { diagnosesApi } from '@/api/endpoints/diagnoses'

describe('diagnosesApi (fixture mode)', () => {
  it('returns top-level roots when no parent_id passed', async () => {
    const r = await diagnosesApi.list({ parent_id: null })
    expect(r.items.length).toBeGreaterThan(0)
    for (const d of r.items) expect(d.parent_id).toBeNull()
  })

  it('lists children of a given node', async () => {
    const r = await diagnosesApi.list({ parent_id: 'icd10-f3x' })
    expect(r.items.length).toBeGreaterThan(0)
    for (const d of r.items) expect(d.parent_id).toBe('icd10-f3x')
  })

  it('search matches by code and label', async () => {
    const byCode = await diagnosesApi.list({ search: 'F32' })
    expect(byCode.items.some((d) => d.code === 'F32')).toBe(true)

    const byLabel = await diagnosesApi.list({ search: 'anxiety' })
    expect(byLabel.items.length).toBeGreaterThan(0)
  })

  it('search is case-insensitive', async () => {
    const lower = await diagnosesApi.list({ search: 'depressive' })
    const upper = await diagnosesApi.list({ search: 'DEPRESSIVE' })
    expect(lower.items.length).toBe(upper.items.length)
    expect(lower.items.length).toBeGreaterThan(0)
  })

  it('respects max_level when given', async () => {
    const r = await diagnosesApi.list({ max_level: 1 })
    for (const d of r.items) expect(d.level).toBeLessThanOrEqual(1)
  })

  it('builds hierarchical path with codes + labels', async () => {
    const r = await diagnosesApi.list({ search: 'F32.1' })
    const hit = r.items.find((d) => d.code === 'F32.1')
    expect(hit?.path).toMatch(/F.*\/.*F30.F39.*\/.*F32.*\/.*F32\.1/)
  })

  it('returns has_children = true on category nodes', async () => {
    const f3x = (await diagnosesApi.list({ search: 'F30' })).items.find(
      (d) => d.id === 'icd10-f3x',
    )
    expect(f3x?.has_children).toBe(true)
  })

  it('getById returns the node', async () => {
    const node = await diagnosesApi.getById('icd10-f43-ptsd')
    expect(node.code).toBe('F43.1')
  })

  it('getById throws for unknown id', async () => {
    await expect(diagnosesApi.getById('does-not-exist')).rejects.toThrow()
  })
})
