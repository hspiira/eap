/**
 * Eligible Members API — the employer-known side of a person eligible for
 * EAP services. Used to open a clinical case (member_id -> a pseudonymous
 * clinical_subject_id server-side); never linked back to it in any response.
 * BE only filters by client_id — no free-text search.
 */

import apiClient from '../client'
import type { EligibleMember } from '../types'

export const eligibleMembersApi = {
  async listForClient(clientId: string): Promise<EligibleMember[]> {
    return apiClient.get<EligibleMember[]>('/eligible-members', { client_id: clientId })
  },

  async getById(memberId: string): Promise<EligibleMember> {
    return apiClient.get<EligibleMember>(`/eligible-members/${memberId}`)
  },
}
