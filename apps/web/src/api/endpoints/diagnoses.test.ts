import { describe, expect, it } from 'vitest'

import { diagnosesApi } from '@/api/endpoints/diagnoses'

describe('diagnosesApi (fixture mode)', () => {
  it('getTypes returns all diagnosis types', async () => {
    const types = await diagnosesApi.getTypes()
    expect(types.length).toBeGreaterThan(0)
    for (const t of types) {
      expect(t.id).toBeTruthy()
      expect(t.code).toBeTruthy()
      expect(t.name).toBeTruthy()
    }
  })

  it('getTree returns types with nested diagnoses', async () => {
    const tree = await diagnosesApi.getTree()
    expect(tree.types.length).toBeGreaterThan(0)
    for (const t of tree.types) {
      expect(Array.isArray(t.diagnoses)).toBe(true)
      for (const d of t.diagnoses) {
        expect(d.type_id).toBe(t.id)
      }
    }
  })

  it('getTree includes mood disorders with F32 codes', async () => {
    const tree = await diagnosesApi.getTree()
    const mood = tree.types.find((t) => t.id === 'type-mood')
    expect(mood).toBeDefined()
    expect(mood!.diagnoses.some((d) => d.code === 'F32')).toBe(true)
    expect(mood!.diagnoses.some((d) => d.code === 'F32.1')).toBe(true)
  })

  it('list returns flat diagnoses across all types when no filter', async () => {
    const all = await diagnosesApi.list()
    expect(all.length).toBeGreaterThan(5)
    for (const d of all) {
      expect(d.type_id).toBeTruthy()
      expect(d.code).toBeTruthy()
      expect(d.name).toBeTruthy()
    }
  })

  it('list filters by type_code', async () => {
    const anxiety = await diagnosesApi.list({ type_code: 'ICD10-F4x' })
    expect(anxiety.length).toBeGreaterThan(0)
    for (const d of anxiety) expect(d.type_id).toBe('type-anxiety')
  })

  it('list returns empty for unknown type_code', async () => {
    const none = await diagnosesApi.list({ type_code: 'UNKNOWN' })
    expect(none).toHaveLength(0)
  })

  it('each diagnosis has required fields', async () => {
    const tree = await diagnosesApi.getTree()
    const all = tree.types.flatMap((t) => t.diagnoses)
    for (const d of all) {
      expect(typeof d.id).toBe('string')
      expect(typeof d.code).toBe('string')
      expect(typeof d.name).toBe('string')
      expect(typeof d.type_id).toBe('string')
      expect(typeof d.sort_order).toBe('number')
    }
  })
})
