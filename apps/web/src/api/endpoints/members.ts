import type {
  Member,
  MemberEmployment,
  MemberNextOfKin,
  MemberStats,
  ServiceSession,
} from "@/types/entities"
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
  /** Optional. The employer's own reference (e.g. a roster Staff_ID). Never the member code. */
  import_source_id?: string | null
  work_email?: string | null
  personal_email?: string | null
  display_label: string
  date_of_birth?: string | null
  gender?: MemberGender | null
  phone?: string | null
  staff_number?: string | null
  national_id?: string | null
  passport_number?: string | null
  employment?: MemberEmployment | null
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

export type MemberImportBatchStatus = "Staged" | "Applied" | "Abandoned"

/** One staged roster upload. Row data lives server-side; nothing is replayed from the browser. */
export interface MemberImportBatch {
  id: string
  tenant_id: string
  file_name: string
  file_hash: string
  row_count: number
  status: MemberImportBatchStatus
  outcome_counts: Record<string, number>
  staged_by: string
  applied_by?: string | null
  applied_at?: string | null
  created_at: string
}

export type MemberImportRowOutcome = "New" | "Duplicate" | "Invalid" | "Failed"
export type MemberImportRowDecision = "import" | "skip"

export interface MemberImportRow {
  id: string
  row_number: number
  client_code: string | null
  client_name?: string | null
  import_source_id: string | null
  staff_number?: string | null
  display_label: string | null
  outcome: MemberImportRowOutcome
  decision: MemberImportRowDecision
  message?: string | null
  imported_member_id?: string | null
}

export interface MemberImportRowListResponse {
  items: MemberImportRow[]
  total: number
  page: number
  limit: number
  has_more: boolean
}

/** What happened when a staged batch's importable rows were written. */
export interface MemberImportApplyResult {
  batch_id: string
  imported: number
  failed: number
  skipped_already_imported: number
  not_importable: number
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

  /** Stage a roster upload. Writes no members; review and applyImport do that. */
  async stageImport(file: File): Promise<MemberImportBatch> {
    const body = new FormData()
    body.append("file", file)
    return apiClient.postFormData<MemberImportBatch>("/members/import", body)
  },

  async getImportBatch(batchId: string): Promise<MemberImportBatch> {
    return apiClient.get<MemberImportBatch>(`/members/import/${batchId}`)
  },

  async listImportRows(
    batchId: string,
    params?: { outcome?: MemberImportRowOutcome; page?: number; limit?: number },
  ): Promise<MemberImportRowListResponse> {
    return apiClient.get<MemberImportRowListResponse>(`/members/import/${batchId}/rows`, params)
  },

  /** Override one still-new row's Import/Skip decision before applying. */
  async setImportRowDecision(
    batchId: string,
    rowId: string,
    decision: MemberImportRowDecision,
  ): Promise<MemberImportRow> {
    return apiClient.patch<MemberImportRow>(`/members/import/${batchId}/rows/${rowId}`, {
      decision,
    })
  },

  async abandonImport(batchId: string, reason: string): Promise<MemberImportBatch> {
    return apiClient.post<MemberImportBatch>(`/members/import/${batchId}/abandon`, { reason })
  },

  /** Write every still-importable row, one at a time, then close the batch. */
  async applyImport(batchId: string): Promise<MemberImportApplyResult> {
    return apiClient.post<MemberImportApplyResult>(`/members/import/${batchId}/apply`)
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
