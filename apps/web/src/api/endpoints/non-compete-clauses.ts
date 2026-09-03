/**
 * Non-Compete Clauses API.
 *
 * Mirrors BE `app/api/routes/non_compete_clauses.py`. A non-compete clause
 * restricts a provider from being assigned to certain clients during its
 * effective range. Lifecycle: Draft → Active (via sign) → Revoked / Expired.
 */

import apiClient from '../client'
import type { NonCompeteClause } from '../types'

export interface NonCompeteCreate {
  provider_id: string
  terms_summary: string
  /** ISO date (YYYY-MM-DD). */
  effective_from: string
  /** ISO date. Null = indefinite. */
  effective_until?: string | null
  /** Linked source document id (optional). */
  document_id?: string | null
}

export interface NonCompeteSign {
  /** UserId acknowledging the signature. */
  signed_by: string
}

export interface NonCompeteRevoke {
  reason: string
}

export const nonCompeteClausesApi = {
  /** Draft a new non-compete (status starts as Draft; needs `sign` to become Active). */
  async draft(data: NonCompeteCreate): Promise<NonCompeteClause> {
    return apiClient.post<NonCompeteClause>('/non-compete-clauses', data)
  },

  /** Sign a draft → moves to Active. */
  async sign(clauseId: string, data: NonCompeteSign): Promise<NonCompeteClause> {
    return apiClient.post<NonCompeteClause>(`/non-compete-clauses/${clauseId}/sign`, data)
  },

  /** Revoke an active clause. Permanent (status → Revoked). */
  async revoke(clauseId: string, data: NonCompeteRevoke): Promise<NonCompeteClause> {
    return apiClient.post<NonCompeteClause>(`/non-compete-clauses/${clauseId}/revoke`, data)
  },

  async getById(clauseId: string): Promise<NonCompeteClause> {
    return apiClient.get<NonCompeteClause>(`/non-compete-clauses/${clauseId}`)
  },

  /** All clauses for a provider (any status). */
  async listForProvider(providerId: string): Promise<NonCompeteClause[]> {
    return apiClient.get<NonCompeteClause[]>(`/non-compete-clauses/provider/${providerId}`)
  },
}
