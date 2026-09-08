import type {
  EligibilityStatus,
  MemberGender,
  MemberRelation,
  NextOfKinRelationship,
} from "../enums"

export interface MemberNextOfKin {
  id: string
  tenant_id: string
  member_id: string
  name: string
  relationship: NextOfKinRelationship
  phone?: string | null
  email?: string | null
  is_primary: boolean
  created_at: string
  updated_at: string
}

/** Employer-side member covered by a client's wellness programme. */
export interface Member {
  id: string
  tenant_id: string
  client_id: string
  client_name?: string | null
  employer_member_id: string
  relation: MemberRelation
  status: EligibilityStatus
  primary_employee_member_id?: string | null
  work_email?: string | null
  personal_email?: string | null
  display_label?: string | null
  date_of_birth?: string | null
  gender?: MemberGender | null
  phone?: string | null
  staff_number?: string | null
  national_id?: string | null
  passport_number?: string | null
  last_imported_at?: string | null
  suspended_at?: string | null
  terminated_at?: string | null
  created_at: string
  updated_at: string
  user_id?: string | null
  coverage_start?: string | null
  coverage_end?: string | null
  /** Active status within the coverage window, computed by the API. */
  is_currently_eligible?: boolean
}

/** Roster counts for the current filter context. */
export interface MemberStats {
  total: number
  active: number
  suspended: number
  pending: number
  terminated: number
  with_account: number
}
