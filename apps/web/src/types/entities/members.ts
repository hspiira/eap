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
  last_imported_at?: string | null
  suspended_at?: string | null
  terminated_at?: string | null
  created_at: string
  updated_at: string
}
