import type { Member } from "@/types/entities"
import { EligibilityStatus, MemberRelation } from "@/types/enums"

export function makeMember(overrides: Partial<Member> = {}): Member {
  return {
    id: "member-1",
    tenant_id: "tenant-1",
    client_id: "client-1",
    employer_member_id: "HR-1",
    display_label: "Amina Namukasa",
    relation: MemberRelation.EMPLOYEE,
    status: EligibilityStatus.ACTIVE,
    primary_employee_member_id: null,
    work_email: null,
    personal_email: null,
    date_of_birth: null,
    gender: null,
    phone: null,
    last_imported_at: null,
    suspended_at: null,
    terminated_at: null,
    created_at: "2026-01-01T00:00:00Z",
    updated_at: "2026-01-01T00:00:00Z",
    ...overrides,
  }
}
