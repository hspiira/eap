/**
 * Eligible Members API Endpoints
 *
 * Mirrors BE `app/api/routes/eligible_members.py`. Enrolling an eligible
 * member auto-creates the matching clinical subject on the BE.
 */

import apiClient from '../client'

export type MemberRelation =
  | 'Employee'
  | 'Spouse'
  | 'Child'
  | 'DomesticPartner'
  | 'DependentOther'

export type EligibilityStatus = 'Active' | 'Suspended' | 'Terminated' | 'Pending'

export interface EligibleMemberEnrol {
  client_id: string
  employer_member_id: string
  relation: MemberRelation
  primary_employee_member_id?: string | null
  coverage_start?: string | null
  coverage_end?: string | null
  work_email?: string | null
  personal_email?: string | null
  display_label?: string | null
}

export interface EligibleMember {
  id: string
  tenant_id: string
  client_id: string
  employer_member_id: string
  relation: MemberRelation
  status: EligibilityStatus
  primary_employee_member_id: string | null
  coverage_start: string | null
  coverage_end: string | null
  display_label: string | null
  last_imported_at: string | null
  suspended_at: string | null
  terminated_at: string | null
  created_at: string
  updated_at: string
}

export interface EligibleMemberListParams {
  client_id: string
  status?: EligibilityStatus
  relation?: MemberRelation
  limit?: number
  offset?: number
}

export const eligibleMembersApi = {
  /** Enrol one member. Auto-creates the linked clinical subject on the BE. */
  async enrol(data: EligibleMemberEnrol): Promise<EligibleMember> {
    return apiClient.post<EligibleMember>('/eligible-members', data)
  },

  /** List eligible members for a client. */
  async list(params: EligibleMemberListParams): Promise<EligibleMember[]> {
    return apiClient.get<EligibleMember[]>(
      '/eligible-members',
      params as unknown as Record<string, unknown>,
    )
  },

  async getById(memberId: string): Promise<EligibleMember> {
    return apiClient.get<EligibleMember>(`/eligible-members/${memberId}`)
  },
}
