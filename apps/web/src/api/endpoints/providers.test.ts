import { describe, expect, it } from 'vitest'

import { providersApi } from '@/api/endpoints/providers'
import { ProviderRegion, ProviderTier } from '@/types/enums'

describe('providersApi (fixture mode)', () => {
  it('seeds at least 5 providers across regions', async () => {
    const r = await providersApi.list({ limit: 50 })
    expect(r.items.length).toBeGreaterThanOrEqual(5)
    const regions = new Set(r.items.map((p) => p.region))
    expect(regions.size).toBeGreaterThanOrEqual(4)
  })

  it('filters by tier', async () => {
    const t1 = await providersApi.list({ tier: ProviderTier.T1, limit: 50 })
    expect(t1.items.length).toBeGreaterThan(0)
    for (const p of t1.items) expect(p.tier).toBe(ProviderTier.T1)
  })

  it('filters by region', async () => {
    const eastern = await providersApi.list({ region: ProviderRegion.EASTERN, limit: 50 })
    for (const p of eastern.items) expect(p.region).toBe(ProviderRegion.EASTERN)
  })

  it('combines tier + region filters', async () => {
    const r = await providersApi.list({
      tier: ProviderTier.T2,
      region: ProviderRegion.NORTHERN,
      limit: 50,
    })
    for (const p of r.items) {
      expect(p.tier).toBe(ProviderTier.T2)
      expect(p.region).toBe(ProviderRegion.NORTHERN)
    }
  })

  it('search matches name or registration number', async () => {
    const byName = await providersApi.list({ search: 'nakato' })
    expect(byName.items.length).toBeGreaterThan(0)
    const byReg = await providersApi.list({ search: 'UCA/2017' })
    expect(byReg.items.length).toBeGreaterThan(0)
  })

  it('getById returns the seeded record', async () => {
    const p = await providersApi.getById('prov-005')
    expect(p.tier).toBe(ProviderTier.T1)
  })

  it('getById throws for unknown id', async () => {
    await expect(providersApi.getById('nope')).rejects.toThrow()
  })

  it('every provider has an accreditation', async () => {
    const r = await providersApi.list({ limit: 50 })
    for (const p of r.items) {
      expect(p.accreditation).toBeTruthy()
      expect(p.accreditation.body).toBeTruthy()
      expect(p.accreditation.registration_number).toBeTruthy()
    }
  })
})
