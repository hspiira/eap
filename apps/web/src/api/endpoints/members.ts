import type { Member, MemberNextOfKin, MemberStats, ServiceSession } from "@/types/entities"
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

/** The parsed CSV values the preview echoes back, replayed row by row on confirm. */
export interface MemberImportRowValues {
  client_code: string | null
  employer_member_id: string | null
  staff_number: string | null
  display_label: string | null
  work_email: string | null
  personal_email: string | null
  gender: string | null
  date_of_birth: string | null
  phone: string | null
  national_id: string | null
  passport_number: string | null
  status: string | null
  relation: string | null
  primary_employee_member_id: string | null
}

export interface MemberImportRow {
  row: number
  client_code: string | null
  client_name: string | null
  employer_member_id: string | null
  staff_number?: string | null
  display_label: string | null
  state: string
  message?: string | null
  default_action: "import" | "skip"
  values?: MemberImportRowValues | null
}

export type MemberImportRowState = "imported" | "skipped" | "duplicate" | "invalid" | "failed"

/** What the server did with one confirmed row. */
export interface MemberImportRowResult {
  row: number
  state: MemberImportRowState
  member_id?: string | null
  message?: string | null
}

export interface MemberImportIssue {
  row: number
  field?: string | null
  message: string
}

export interface MemberImportResult {
  imported: number
  skipped: number
  failed: number
  issues: MemberImportIssue[]
  rows: MemberImportRow[]
}

export interface MemberDuplicateMember {
  id: string
  client_id: string
  client_name?: string | null
  employer_member_id: string
  display_label: string
  relation: MemberRelation
}

export interface MemberDuplicateCandidate {
  first: MemberDuplicateMember
  second: MemberDuplicateMember
  reason: string
}

export const membersApi = {
  async getImportTemplate(): Promise<Blob> {
    return apiClient.getBlob("/members/import/template")
  },

  async scanDuplicates(): Promise<{ items: MemberDuplicateCandidate[]; scanned: number }> {
    return apiClient.get<{ items: MemberDuplicateCandidate[]; scanned: number }>(
      "/members/duplicates",
    )
  },

  async importRoster(
    file: File,
    dryRun = true,
    decisions?: Record<number, "import" | "skip">,
  ): Promise<MemberImportResult> {
    const body = new FormData()
    body.append("file", file)
    if (decisions) body.append("decisions_json", JSON.stringify(decisions))
    return apiClient.postFormData<MemberImportResult>(
      `/members/import?dry_run=${String(dryRun)}`,
      body,
    )
  },

  /** Import a slice of previewed rows. Each row is committed on its own server side. */
  async commitImport(
    rows: Array<{ row: number; values: MemberImportRowValues }>,
  ): Promise<{ results: MemberImportRowResult[] }> {
    return apiClient.post<{ results: MemberImportRowResult[] }>("/members/import/commit", { rows })
  },

  async list(params?: MemberListParams): Promise<PaginatedResponse<Member>> {
    return apiClient.get<PaginatedResponse<Member>>("/members", params)
  },

  /** Roster counts honouring the same filters as `list`. */
  async getStats(params?: Omit<MemberListParams, "page" | "limit">): Promise<MemberStats> {
    return apiClient.get<MemberStats>("/members/stats", params)
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
