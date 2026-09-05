import type { EligibilityStatus, MemberRelation } from "../enums"

/** Employer-side member covered by a client's wellness programme. */
export interface Member {
  id: string
  tenant_id: string
  client_id: string
  employer_member_id: string
  relation: MemberRelation
  status: EligibilityStatus
  primary_employee_member_id?: string | null
  coverage_start?: string | null
  coverage_end?: string | null
  work_email?: string | null
  personal_email?: string | null
  display_label?: string | null
  last_imported_at?: string | null
  suspended_at?: string | null
  terminated_at?: string | null
  created_at: string
  updated_at: string
  is_currently_eligible: boolean
}
