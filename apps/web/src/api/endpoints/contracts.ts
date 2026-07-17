/**
 * Contracts API Endpoints
 *
 * Shapes mirror BE OpenAPI. Notable BE design choices:
 * - `billing_rate` is a structured `MoneySchema` ({amount: str, currency: 3-letter}),
 *   NOT primitive `billing_amount` + `currency`.
 * - `payment_frequency` is required on create.
 * - `start_date` / `end_date` are full datetimes (ISO with time), not just dates.
 * - `is_auto_renew` defaults to false; renewal_date is computed from period.
 * - Pricing model selection (RETAINER / FRAMEWORK / FFS / etc.) is set via a
 *   separate `PATCH /contracts/{id}/pricing` route — see `pricing.ts`.
 */

import type {
  ContractCreate,
  ContractRenewRequest,
  ContractTerminateRequest,
  ContractUpdate,
} from '@/api/generated'

import apiClient from '../client'
import type { Contract, ListParams, PaginatedResponse } from '../types'

export type { ContractCreate, ContractRenewRequest, ContractTerminateRequest, ContractUpdate }

/** Mirrors the query params on `GET /contracts/` in the BE OpenAPI schema. */
export interface ContractListParams extends ListParams {
  client_id?: string
  payment_status?: string
  is_auto_renew?: boolean
  /** ISO 8601 instant; inclusive lower bound on the end of the term. */
  ends_from?: string
  /** ISO 8601 instant; inclusive upper bound on the end of the term. */
  ends_to?: string
}

export const contractsApi = {
  async create(contractData: ContractCreate): Promise<Contract> {
    return apiClient.post<Contract>('/contracts', contractData)
  },

  async getById(contractId: string): Promise<Contract> {
    return apiClient.get<Contract>(`/contracts/${contractId}`)
  },

  async list(params?: ContractListParams): Promise<PaginatedResponse<Contract>> {
    return apiClient.get<PaginatedResponse<Contract>>('/contracts', params)
  },

  /** BE `ContractUpdate` accepts only `{billing_rate?, payment_frequency?, is_auto_renew?}`. */
  async update(contractId: string, data: ContractUpdate): Promise<Contract> {
    return apiClient.patch<Contract>(`/contracts/${contractId}`, data)
  },

  async activate(contractId: string): Promise<Contract> {
    return apiClient.post<Contract>(`/contracts/${contractId}/activate`, {})
  },

  async renew(contractId: string, data: ContractRenewRequest): Promise<Contract> {
    return apiClient.post<Contract>(`/contracts/${contractId}/renew`, data)
  },

  async terminate(contractId: string, data: ContractTerminateRequest): Promise<Contract> {
    return apiClient.post<Contract>(`/contracts/${contractId}/terminate`, data)
  },
}
