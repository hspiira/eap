import type {
  ContractStatus,
  PaymentFrequency,
  PaymentStatus,
  PricingModel,
} from '../enums'
import type { BaseEntity } from './base'

/** Contract term. Mirrors BE `DateRangeSchema`; both bounds are ISO datetimes. */
export interface ContractPeriod {
  start_date: string
  end_date: string
}

/** Money on the wire. `amount` is a decimal *string* — parse before arithmetic. */
export interface ContractMoney {
  amount: string
  currency: string
}

/**
 * Contract — mirrors BE `ContractResponse` field-for-field.
 *
 * This type previously declared a shape the BE has never sent: top-level
 * `start_date`/`end_date` (they are nested under `period`), plus `renewal_date`,
 * `contract_number`, `billing_frequency`, `billing_amount` and `currency`, none
 * of which exist on the response. Every one of them read `undefined` at runtime,
 * which is why the term columns rendered blank and the renewal filter matched
 * nothing. Keep this aligned with `ContractResponse` in the OpenAPI schema.
 */
export interface Contract extends BaseEntity {
  client_id: string
  status: ContractStatus
  /** The contract term. Use `period.start_date` / `period.end_date`. */
  period: ContractPeriod
  billing_rate: ContractMoney
  payment_frequency: PaymentFrequency
  payment_status: PaymentStatus
  is_auto_renew: boolean
  /** Server-computed: whether the contract is currently within its term. */
  is_active: boolean
  /** Server-computed: days left in the term. */
  days_remaining: number
  /** ISO date. */
  last_billing_date?: string | null
  /** ISO date. */
  next_billing_date?: string | null
  signed_by?: string | null
  /** ISO datetime. */
  signed_at?: string | null
  termination_reason?: string | null
}

/**
 * Contract pricing config (D-Pricing v1). Discriminated by `model`.
 */
export type ContractPricing =
  | RetainerPricing
  | FrameworkPricing
  | FFSPricing
  | AdminUtilisationPricing
  | ValueAddPricing

export interface RetainerPricing {
  model: PricingModel.RETAINER
  monthly_fee: number
  /** Optional max sessions covered before overflow rate. */
  session_cap?: number | null
  overflow_rate?: number | null
}

export interface FrameworkPricing {
  model: PricingModel.FRAMEWORK
  deposit: number
  /** Remaining balance, computed by BE; FE displays it read-only. */
  drawdown_balance: number
  unit_rate: number
}

export interface FFSPricing {
  model: PricingModel.FFS
  unit_rate: number
}

export interface AdminUtilisationPricing {
  model: PricingModel.ADMIN_UTILISATION
  monthly_admin_fee: number
  /** Hard floor on monthly admin fee — flags warnings if pricing dips below. */
  admin_floor: number
  utilisation_rate: number
}

export interface ValueAddPricing {
  model: PricingModel.VALUE_ADD
  monthly_fee: number
  bundled_services: string[]
}

export interface RateCardItem {
  service_id: string
  service_name: string
  rate: number
}

/**
 * Invoice-line preview row returned from BE per contract pricing config.
 */
export interface InvoiceLinePreview {
  label: string
  quantity: number
  unit: string
  unit_rate: number
  subtotal: number
  /** Rendered footnote for context (e.g. "below admin floor"). */
  note?: string | null
}
