import type { Member, MemberNextOfKin } from "@/types/entities"
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
  async list(params?: MemberListParams): Promise<PaginatedResponse<Member>> {
    return apiClient.get<PaginatedResponse<Member>>("/members", params)
  },

  async getById(id: string): Promise<Member> {
    return apiClient.get<Member>(`/members/${id}`)
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
