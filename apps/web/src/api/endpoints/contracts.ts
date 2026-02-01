/**
 * Contracts API Endpoints
 */

import apiClient from '../client'
import type { Contract, PaginatedResponse, ListParams } from '../types'
import type { ContractStatus, PaymentFrequency, PaymentStatus } from '@/types/enums'

export interface ContractCreate {
  client_id: string
  contract_number?: string | null
  start_date: string
  end_date?: string | null
  renewal_date?: string | null
  billing_frequency?: PaymentFrequency | null
  billing_amount?: number | null
  currency?: string | null
  payment_status?: PaymentStatus | null
  metadata?: Record<string, unknown> | null
}

export const contractsApi = {
  /**
   * Create a new contract
   */
  async create(contractData: ContractCreate): Promise<Contract> {
    return apiClient.post<Contract>('/contracts', contractData)
  },

  /**
   * Get contract by ID
   */
  async getById(contractId: string): Promise<Contract> {
    return apiClient.get<Contract>(`/contracts/${contractId}`)
  },

  /**
   * List contracts
   */
  async list(params?: ListParams): Promise<PaginatedResponse<Contract>> {
    return apiClient.get<PaginatedResponse<Contract>>('/contracts', params as Record<string, unknown>)
  },

  /**
   * Update contract
   */
  async update(contractId: string, data: Partial<ContractCreate>): Promise<Contract> {
    return apiClient.patch<Contract>(`/contracts/${contractId}`, data)
  },
}
