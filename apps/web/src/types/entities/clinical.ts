import type {
  AuthorizationStatus,
  CaseClosureReason,
  CaseReferralSource,
  CaseStatus,
  ClinicalNoteType,
  EligibilityStatus,
  PresentingProblem,
  RelationType,
  ServiceCategory,
} from '../enums'
import type { BaseEntity } from './base'

/**
 * The employer-known side of a person eligible for EAP services. Deliberately
 * NOT linked to clinical_subject_id in any response — see Case below.
 */
export interface EligibleMember {
  id: string
  tenant_id: string
  client_id: string
  employer_member_id: string
  relation: RelationType
  status: EligibilityStatus
  primary_employee_member_id?: string | null
  coverage_start: string
  coverage_end?: string | null
  /** Privacy-safe label sanctioned for display (e.g. masked/initials) — not a raw name. */
  display_label: string
  last_imported_at?: string | null
  suspended_at?: string | null
  terminated_at?: string | null
  created_at: string
  updated_at: string
}

/**
 * Mirrors BE `CaseResponse` — field names and nullability are wire-true.
 *
 * `clinical_subject_id` is a pseudonym, not a person reference — the privacy
 * wall (SAD Phase 5A) deliberately has no route resolving it back to a name.
 * Render it as an opaque subject reference. The counsellor who opens a case
 * (via an EligibleMember at open time) already knows who it's for; the
 * system does not let the case list re-derive that identity for browsing.
 */
export interface Case extends BaseEntity {
  clinical_subject_id: string
  client_id: string
  presenting_problem: PresentingProblem
  referral_source: CaseReferralSource
  status: CaseStatus
  opened_at: string
  assigned_counsellor_id?: string | null
  authorization_id?: string | null
  referred_by_user_id?: string | null
  referral_notes?: string | null
  closed_at?: string | null
  closure_reason?: CaseClosureReason | null
  closure_summary_note_id?: string | null
  intake_screener_admin_ids: string[]
  closure_screener_admin_ids: string[]
}

/** The three body shapes the BE accepts per note_type — see clinical-notes API. */
export interface DAPNoteBody {
  data: string
  assessment: string
  plan: string
}
export interface SOAPNoteBody {
  subjective: string
  objective: string
  assessment: string
  plan: string
}
export interface NarrativeNoteBody {
  summary: string
}
export type ClinicalNoteBody = DAPNoteBody | SOAPNoteBody | NarrativeNoteBody | Record<string, unknown>

export interface NoteAmendment {
  id: string
  author_id: string
  body: ClinicalNoteBody
  reason: string
  created_at: string
}

/** Mirrors BE `ClinicalNoteResponse`. */
export interface ClinicalNote {
  id: string
  tenant_id: string
  case_id: string
  clinical_subject_id: string
  note_type: ClinicalNoteType
  body: ClinicalNoteBody
  author_id: string
  session_id?: string | null
  signed_at?: string | null
  signed_by?: string | null
  locked_at?: string | null
  amendments: NoteAmendment[]
  created_at: string
  updated_at: string
}

/** Mirrors BE `AuthorizationResponse`. */
export interface Authorization {
  id: string
  tenant_id: string
  case_id: string
  clinical_subject_id: string
  programme_id: string
  service_category: ServiceCategory
  sessions_granted: number
  sessions_used: number
  sessions_remaining: number
  status: AuthorizationStatus
  granted_at: string
  expires_on?: string | null
  extension_requested_sessions?: number | null
  extended_at?: string | null
  closed_at?: string | null
  created_at: string
  updated_at: string
}

export interface ProgrammeCap {
  service_category: ServiceCategory
  per_issue_per_year: number
  per_year?: number | null
  per_household_per_year?: number | null
}

/** Mirrors BE `EAPProgrammeResponse`. */
export interface EAPProgramme {
  id: string
  tenant_id: string
  contract_id: string
  name: string
  effective_from: string
  effective_until?: string | null
  geographic_scope?: string | null
  description?: string | null
  eligible_dependent_relations: RelationType[]
  caps: ProgrammeCap[]
  created_at: string
  updated_at: string
}

