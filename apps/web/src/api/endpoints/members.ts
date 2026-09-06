import type { Member, MemberNextOfKin, ServiceSession } from "@/types/entities"
import type {
  EligibilityStatus,
  MemberGender,
  MemberRelation,
  NextOfKinRelationship,
} from "@/types/enums"

import apiClient from "../client"
import type { ListParams, PaginatedResponse } from "../types"

export interface MemberCreateRequest {
  client_id: string
  /** Optional. Left blank, the API issues the next {client code}-### code. */
  employer_member_id?: string | null
  relation: MemberRelation
  primary_employee_member_id?: string | null
  work_email?: string | null
  personal_email?: string | null
  display_label: string
  date_of_birth?: string | null
  gender?: MemberGender | null
  phone?: string | null
  staff_number?: string | null
  national_id?: string | null
  passport_number?: string | null
}

export type MemberUpdateRequest = Partial<Omit<MemberCreateRequest, "client_id">>

export interface MemberListParams extends ListParams {
  client_id?: string
  status?: EligibilityStatus
  relation?: MemberRelation
}

export interface MemberNextOfKinRequest {
  name: string
  relationship: NextOfKinRelationship
  phone?: string | null
  email?: string | null
  is_primary?: boolean
}

export const membersApi = {
  async importRoster(file: File, dryRun = true): Promise<{
    imported: number
    skipped: number
    failed: number
    rows: Array<{
      row: number
      client_code: string | null
      client_name: string | null
      employer_member_id: string | null
      display_label: string | null
      state: string
      message?: string | null
    }>
  }> {
    const body = new FormData()
    body.append("file", file)
    return apiClient.post(`/members/import?dry_run=${dryRun}`, body)
  },

  async list(params?: MemberListParams): Promise<PaginatedResponse<Member>> {
    return apiClient.get<PaginatedResponse<Member>>("/members", params)
  },

  async getById(id: string): Promise<Member> {
    return apiClient.get<Member>(`/members/${id}`)
  },

  async listSessions(id: string, params?: ListParams): Promise<PaginatedResponse<ServiceSession>> {
    return apiClient.get<PaginatedResponse<ServiceSession>>(`/members/${id}/sessions`, params)
  },

  async linkAccount(id: string, userId: string): Promise<Member> {
    return apiClient.put<Member>(`/members/${id}/account`, { user_id: userId })
  },

  async unlinkAccount(id: string): Promise<Member> {
    return apiClient.delete<Member>(`/members/${id}/account`)
  },

  async merge(
    targetId: string,
    sourceId: string,
  ): Promise<{ member: Member; source_member_id: string; transferred: Record<string, number> }> {
    return apiClient.post(`/members/${targetId}/merge`, { source_member_id: sourceId })
  },

  async listBeneficiaries(id: string): Promise<Member[]> {
    return apiClient.get<Member[]>(`/members/${id}/beneficiaries`)
  },

  async listNextOfKin(id: string): Promise<MemberNextOfKin[]> {
    return apiClient.get<MemberNextOfKin[]>(`/members/${id}/next-of-kin`)
  },

  async createNextOfKin(id: string, data: MemberNextOfKinRequest): Promise<MemberNextOfKin> {
    return apiClient.post<MemberNextOfKin>(`/members/${id}/next-of-kin`, data)
  },

  async updateNextOfKin(
    memberId: string,
    contactId: string,
    data: MemberNextOfKinRequest,
  ): Promise<MemberNextOfKin> {
    return apiClient.patch<MemberNextOfKin>(`/members/${memberId}/next-of-kin/${contactId}`, data)
  },

  async deleteNextOfKin(memberId: string, contactId: string): Promise<void> {
    await apiClient.delete(`/members/${memberId}/next-of-kin/${contactId}`)
  },

  async create(data: MemberCreateRequest): Promise<Member> {
    return apiClient.post<Member>("/members", data)
  },

  async update(id: string, data: MemberUpdateRequest): Promise<Member> {
    return apiClient.patch<Member>(`/members/${id}`, data)
  },

  async suspend(id: string): Promise<Member> {
    return apiClient.post<Member>(`/members/${id}/suspend`)
  },

  async reinstate(id: string): Promise<Member> {
    return apiClient.post<Member>(`/members/${id}/reinstate`)
  },

  async terminate(id: string): Promise<Member> {
    return apiClient.post<Member>(`/members/${id}/terminate`)
  },

  async exportCsv(
    params: {
      member_ids?: string[]
      client_id?: string
      status?: EligibilityStatus
      relation?: MemberRelation
      search?: string
    } = {},
  ): Promise<Blob> {
    return apiClient.getBlob("/members/export", params)
  },
}
