import { describe, expect, it } from 'vitest'

import { pricingApi } from '@/api/endpoints/pricing'
import { PricingModel } from '@/types/enums'

describe('pricingApi.preview (fixture mode)', () => {
  it('Retainer: emits the monthly retainer line', async () => {
    const lines = await pricingApi.preview(
      { model: PricingModel.RETAINER, monthly_fee: 50_000 },
      { projected_sessions: 10 },
    )
    expect(lines).toHaveLength(1)
    expect(lines[0].subtotal).toBe(50_000)
  })

  it('Retainer: adds an overflow line when sessions exceed cap', async () => {
    const lines = await pricingApi.preview(
      {
        model: PricingModel.RETAINER,
        monthly_fee: 50_000,
        session_cap: 5,
        overflow_rate: 1_500,
      },
      { projected_sessions: 8 },
    )
    expect(lines).toHaveLength(2)
    expect(lines[1].quantity).toBe(3)
    expect(lines[1].subtotal).toBe(4_500)
  })

  it('Framework: drawdown computes correctly and notes remaining deposit', async () => {
    const lines = await pricingApi.preview(
      { model: PricingModel.FRAMEWORK, deposit: 10_000, drawdown_balance: 10_000, unit_rate: 1_000 },
      { projected_sessions: 5 },
    )
    expect(lines).toHaveLength(1)
    expect(lines[0].subtotal).toBe(5_000)
    expect(lines[0].note).toMatch(/remaining deposit/i)
  })

  it('Framework: flags overdrawn deposits', async () => {
    const lines = await pricingApi.preview(
      { model: PricingModel.FRAMEWORK, deposit: 1_000, drawdown_balance: 1_000, unit_rate: 1_000 },
      { projected_sessions: 5 },
    )
    expect(lines[0].note).toMatch(/overdrawn/i)
  })

  it('FFS: pure pay-per-session math', async () => {
    const lines = await pricingApi.preview(
      { model: PricingModel.FFS, unit_rate: 2_500 },
      { projected_sessions: 12 },
    )
    expect(lines[0].subtotal).toBe(30_000)
  })

  it('Admin+Utilisation: emits both lines and flags below-floor admin fee', async () => {
    const lines = await pricingApi.preview(
      {
        model: PricingModel.ADMIN_UTILISATION,
        monthly_admin_fee: 8_000,
        admin_floor: 10_000,
        utilisation_rate: 1_200,
      },
      { projected_sessions: 6 },
    )
    expect(lines).toHaveLength(2)
    expect(lines[0].note).toMatch(/below admin floor/i)
    expect(lines[1].subtotal).toBe(7_200)
  })

  it('Value-Add: shows bundled-services line with monthly fee', async () => {
    const lines = await pricingApi.preview({
      model: PricingModel.VALUE_ADD,
      monthly_fee: 75_000,
      bundled_services: ['CISM', 'Reports'],
    })
    expect(lines).toHaveLength(1)
    expect(lines[0].label).toMatch(/value-add bundle.*2 services/i)
    expect(lines[0].subtotal).toBe(75_000)
  })
})
