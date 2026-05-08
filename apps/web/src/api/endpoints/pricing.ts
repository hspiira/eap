/**
 * Pricing preview API. Computes invoice lines from a `ContractPricing` config — the BE
 * will replace this with a real engine when Phase 2 #4 ships. Same shape, same
 * return values; flip `VITE_PRICING_USE_FIXTURE=false` to swap.
 */

import apiClient from '../client'
import type { ContractPricing, InvoiceLinePreview } from '../types'

import { PricingModel } from '@/types/enums'

export interface PricingPreviewParams {
  /** Optional projected sessions / utilisation per month for preview math. */
  projected_sessions?: number
}

function useFixture(): boolean {
  if (typeof import.meta === 'undefined') return true
  return import.meta.env?.VITE_PRICING_USE_FIXTURE !== 'false'
}

function previewLocally(
  pricing: ContractPricing,
  params: PricingPreviewParams,
): InvoiceLinePreview[] {
  const sessions = params.projected_sessions ?? 20

  switch (pricing.model) {
    case PricingModel.RETAINER: {
      const lines: InvoiceLinePreview[] = [
        {
          label: 'Monthly retainer',
          quantity: 1,
          unit: 'month',
          unit_rate: pricing.monthly_fee,
          subtotal: pricing.monthly_fee,
        },
      ]
      if (pricing.session_cap != null && sessions > pricing.session_cap && pricing.overflow_rate) {
        const overflow = sessions - pricing.session_cap
        lines.push({
          label: `Overflow sessions (above cap of ${pricing.session_cap})`,
          quantity: overflow,
          unit: 'session',
          unit_rate: pricing.overflow_rate,
          subtotal: overflow * pricing.overflow_rate,
        })
      }
      return lines
    }
    case PricingModel.FRAMEWORK: {
      const drawdown = sessions * pricing.unit_rate
      const remaining = pricing.drawdown_balance - drawdown
      return [
        {
          label: 'Framework drawdown',
          quantity: sessions,
          unit: 'session',
          unit_rate: pricing.unit_rate,
          subtotal: drawdown,
          note:
            remaining < 0
              ? `Deposit overdrawn by ${Math.abs(remaining).toFixed(2)} — top up required`
              : `Remaining deposit: ${remaining.toFixed(2)}`,
        },
      ]
    }
    case PricingModel.FFS: {
      return [
        {
          label: 'Sessions delivered',
          quantity: sessions,
          unit: 'session',
          unit_rate: pricing.unit_rate,
          subtotal: sessions * pricing.unit_rate,
        },
      ]
    }
    case PricingModel.ADMIN_UTILISATION: {
      const utilCharge = sessions * pricing.utilisation_rate
      const adminBelowFloor = pricing.monthly_admin_fee < pricing.admin_floor
      return [
        {
          label: 'Monthly admin fee',
          quantity: 1,
          unit: 'month',
          unit_rate: pricing.monthly_admin_fee,
          subtotal: pricing.monthly_admin_fee,
          note: adminBelowFloor
            ? `Below admin floor of ${pricing.admin_floor.toFixed(2)} — pricing requires approval`
            : null,
        },
        {
          label: 'Utilisation charge',
          quantity: sessions,
          unit: 'session',
          unit_rate: pricing.utilisation_rate,
          subtotal: utilCharge,
        },
      ]
    }
    case PricingModel.VALUE_ADD: {
      return [
        {
          label: `Value-add bundle (${pricing.bundled_services.length} services)`,
          quantity: 1,
          unit: 'month',
          unit_rate: pricing.monthly_fee,
          subtotal: pricing.monthly_fee,
        },
      ]
    }
    default: {
      const _exhaustive: never = pricing
      return _exhaustive
    }
  }
}

export const pricingApi = {
  async preview(
    pricing: ContractPricing,
    params: PricingPreviewParams = {},
  ): Promise<InvoiceLinePreview[]> {
    if (useFixture()) return Promise.resolve(previewLocally(pricing, params))
    return apiClient.post<InvoiceLinePreview[]>('/v1/pricing/preview', { pricing, ...params })
  },
}
