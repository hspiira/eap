import type { Member } from "@/types/entities"
import type { EligibilityStatus, MemberRelation } from "@/types/enums"

import apiClient from "../client"
import type { ListParams, PaginatedResponse } from "../types"

export interface MemberCreateRequest {
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

export type MemberUpdateRequest = Partial<Omit<MemberCreateRequest, "client_id">>

export interface MemberListParams extends ListParams {
  client_id?: string
  status?: EligibilityStatus
  relation?: MemberRelation
}

export interface MemberDuplicateCandidate {
  member: Member
  matched_on: string[]
}

export const membersApi = {
  async list(params?: MemberListParams): Promise<PaginatedResponse<Member>> {
    return apiClient.get<PaginatedResponse<Member>>("/members", params)
  },

  async getById(id: string): Promise<Member> {
    return apiClient.get<Member>(`/members/${id}`)
  },

  async listBeneficiaries(id: string): Promise<Member[]> {
    return apiClient.get<Member[]>(`/members/${id}/beneficiaries`)
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

  async scanDuplicates(client_id?: string): Promise<{ candidates: MemberDuplicateCandidate[] }> {
    return apiClient.get<{ candidates: MemberDuplicateCandidate[] }>(
      "/members/duplicates",
      client_id ? { client_id } : undefined,
    )
  },
}
