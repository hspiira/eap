/**
 * Entity Type Definitions
 * TypeScript interfaces for all API entities
 */

import type {
  AccreditationStatus,
  ActivityType,
  BaseStatus,
  CallbackCampaignStatus,
  CallbackCaseStatus,
  CallbackSamplingStrategy,
  ClientTier,
  ContactMethod,
  ContractStatus,
  DeliverableStatus,
  DocumentStatus,
  DocumentType,
  EngagementStatus,
  EngagementTimelineEventKind,
  EngagementType,
  IncidentSeverity,
  IncidentStatus,
  IncidentTimelineEventKind,
  KPICategory,
  Language,
  MeasurementUnit,
  PaymentFrequency,
  PaymentStatus,
  PersonType,
  PricingModel,
  ProviderRegion,
  ProviderTier,
  QuestionnaireAdministration,
  QuestionnaireQuestionType,
  RelationType,
  SessionStatus,
  StaffRole,
  SurveySource,
  SurveyStatus,
  TenantStatus,
  UserStatus,
  WorkStatus,
} from './enums'

/**
 * Common fields present in all entities
 */
export interface BaseEntity {
  id: string // CUID format, max 25 chars
  tenant_id: string
  created_at: string // ISO 8601 datetime
  updated_at: string // ISO 8601 datetime
  deleted_at?: string | null // ISO 8601 datetime
}

/**
 * Address information
 */
export interface Address {
  street?: string | null
  city?: string | null
  state?: string | null
  postal_code?: string | null
  country?: string | null
}

/**
 * Contact information
 */
export interface ContactInfo {
  email?: string | null
  phone?: string | null
  mobile?: string | null
  preferred_method?: ContactMethod | null
}

/**
 * Dependent information
 */
export interface DependentInfo {
  primary_employee_id: string
  relationship: RelationType
  guardian_id?: string | null
}

/**
 * Employment information (client employee)
 */
export interface EmploymentInfo {
  client_id?: string | null
  employee_code?: string | null
  employee_id?: string | null
  department?: string | null
  role?: string | null
  start_date?: string | null
  status?: WorkStatus | null
  end_date?: string | null
}

/**
 * License information
 */
export interface LicenseInfo {
  number?: string | null
  issuing_authority?: string | null
  expiry_date?: string | null
}

/**
 * Staff information (platform staff)
 */
export interface StaffInfo {
  role?: StaffRole | null
  client_id?: string | null
  department?: string | null
  can_manage_clients?: boolean
  can_manage_services?: boolean
  can_view_reports?: boolean
}

/**
 * Emergency contact
 */
export interface EmergencyContact {
  name?: string | null
  phone?: string | null
  email?: string | null
}

/**
 * Tenant/Organization
 */
export interface TenantSettings {
  max_users: number
  max_clients: number
  features_enabled: string[]
  custom_branding: boolean
}

export interface Tenant extends BaseEntity {
  name: string
  code?: string | null
  status: TenantStatus
  subscription_tier?: string | null
  settings?: TenantSettings | null
  is_active?: boolean
  azure_tenant_id?: string | null
  azure_sso_enabled?: boolean
  industry_id?: string | null
  tax_id?: string | null
  registration_number?: string | null
  address?: Address | null
  contact_info?: ContactInfo | null
  metadata?: Record<string, unknown> | null
  status_changed_at?: string | null
}

/**
 * User account
 */
export interface User extends BaseEntity {
  email: string
  status: UserStatus
  is_email_verified: boolean
  email_verified_at?: string | null
  is_two_factor_enabled: boolean
  preferred_language?: Language | null
  timezone?: string | null
  date_format?: string | null
  week_starts_on?: string | null
  email_notifications?: boolean | null
  assignment_alerts?: boolean | null
  session_reminders?: boolean | null
  weekly_digest?: boolean | null
  last_login_at?: string | null
  status_changed_at?: string | null
  is_active: boolean
}

/**
 * Person — BE-canonical: a thin link between a User and a Client (via
 * employment_info) or a primary employee (via dependent_info).
 *
 * BE `PersonResponse` only carries: `id, tenant_id, user_id, person_type,
 * status, is_dual_role, is_eligible_for_services, secondary_person_type,
 * last_service_date, family_id, employment_info?, dependent_info?,
 * emergency_contact?, license_info?, staff_info?`.
 *
 * The legacy demographic fields (first_name/last_name/contact_info/address)
 * are NOT on the BE response. They remain optional here only so legacy
 * display callers compile while we migrate them to email/role-derived display
 * via `displayName(person, user?)`. **Do not introduce new code that reads
 * these.**
 */
export interface Person extends BaseEntity {
  person_type: PersonType
  status: BaseStatus
  user_id: string
  is_dual_role?: boolean
  secondary_person_type?: PersonType | null
  last_service_date?: string | null
  is_eligible_for_services?: boolean
  family_id?: string | null
  dependent_info?: DependentInfo | null
  employment_info?: EmploymentInfo | null
  license_info?: LicenseInfo | null
  staff_info?: StaffInfo | null
  emergency_contact?: EmergencyContact | null
  /** @deprecated Not on BE response. Display via `displayName(person, user)`. */
  first_name?: string
  /** @deprecated Not on BE response. Display via `displayName(person, user)`. */
  last_name?: string
  /** @deprecated Not on BE response. */
  middle_name?: string | null
  /** @deprecated Not on BE response (PII; out of scope for v1). */
  date_of_birth?: string | null
  /** @deprecated Not on BE response. */
  gender?: string | null
  /** @deprecated Use `employment_info.client_id` instead. */
  client_id?: string | null
  /** @deprecated Use `dependent_info` instead. */
  parent_person_id?: string | null
  /** @deprecated Not on BE Person response — contact lives on the linked User. */
  contact_info?: ContactInfo | null
  /** @deprecated Not on BE Person response. */
  address?: Address | null
  /** @deprecated Use `secondary_person_type` instead. */
  secondary_roles?: PersonType[]
  /** @deprecated Not on BE response. */
  metadata?: Record<string, unknown> | null
}

/**
 * Client contact info (phone, email, address line)
 */
export interface ClientContactInfo {
  phone?: string | null
  email?: string | null
  address?: string | null
}

/**
 * Client billing address
 */
export interface ClientBillingAddress {
  street?: string | null
  city?: string | null
  country?: string | null
  postal_code?: string | null
}

/**
 * Client organization
 */
export interface Client extends BaseEntity {
  name: string
  code: string // Required, 3-5 chars (e.g. used for employee codes like MNT)
  is_verified?: boolean // Backend may omit; treat as false when absent
  status: BaseStatus
  tier?: ClientTier | null
  contact_info: ClientContactInfo // Required for creation
  billing_address?: ClientBillingAddress | null
  industry_id?: string | null
  parent_client_id?: string | null
  preferred_contact_method?: string | null
  metadata?: Record<string, unknown> | null
}

/**
 * Client stats (child count, contracts, verification)
 */
export interface ClientStats {
  child_count?: number
  contract_count?: number
  is_verified?: boolean
}

/**
 * Contract
 */
export interface Contract extends BaseEntity {
  client_id: string
  status: ContractStatus
  /** ISO datetime per BE `ContractResponse.start_date`. */
  start_date: string
  /** ISO datetime; required on BE create but response may show legacy nullable rows. */
  end_date?: string | null
  /** Per BE `ContractResponse.is_auto_renew`. */
  is_auto_renew?: boolean
  /** Per BE `ContractResponse.payment_frequency`. Aliased into the legacy `billing_frequency` slot for back-compat. */
  billing_frequency?: PaymentFrequency | null
  /** Per BE `ContractResponse.billing_rate.amount` (string-decimal on the wire). */
  billing_amount?: number | null
  /** Per BE `ContractResponse.billing_rate.currency`. */
  currency?: string | null
  /** @deprecated Not on BE — payment status moved to invoice/utilisation events. */
  payment_status?: PaymentStatus | null
  /** @deprecated Not on BE — renewal handled via dedicated `renew` route. */
  renewal_date?: string | null
  /** @deprecated Not on BE response. */
  contract_number?: string | null
  /** @deprecated Not on BE response. */
  metadata?: Record<string, unknown> | null
}

/**
 * Service
 */
export interface Service extends BaseEntity {
  name: string
  description?: string | null
  status: BaseStatus
  category?: string | null
  duration_minutes?: number | null
  /** Whether this is a group service per BE `ServiceResponse.is_group_service`. */
  is_group_service?: boolean
  /** Group session capacity cap per BE `ServiceResponse.max_participants`. */
  max_participants?: number | null
  /** @deprecated Not on BE — kept temporarily for legacy callers; will be removed. */
  service_type?: string | null
  /** @deprecated Use `is_group_service` + `max_participants`. */
  group_settings?: {
    max_group_size?: number | null
    min_group_size?: number | null
    allow_group_sessions?: boolean
  } | null
  /** @deprecated Not on BE response. */
  metadata?: Record<string, unknown> | null
}

/**
 * Service Session
 */
export interface ServiceSession extends BaseEntity {
  service_id: string
  person_id: string
  service_provider_id?: string | null
  contract_id?: string | null
  status: SessionStatus
  scheduled_at: string
  completed_at?: string | null
  location?: string | null
  notes?: string | null
  diagnosis_id?: string | null
  /** Free-text diagnosis. Deprecated path — only used when VITE_DIAGNOSIS_FREETEXT_FALLBACK is on. */
  diagnosis_text?: string | null
  feedback?: {
    rating?: number | null
    comments?: string | null
  } | null
  metadata?: Record<string, unknown> | null
}

/**
 * Contract pricing config (D-Pricing v1). Discriminated by `model`.
 */
export type ContractPricing =
  | RetainerPricing
  | FrameworkPricing
  | FFSPricing
  | AdminUtilisationPricing
  | ValueAddPricing

export interface RetainerPricing {
  model: PricingModel.RETAINER
  monthly_fee: number
  /** Optional max sessions covered before overflow rate. */
  session_cap?: number | null
  overflow_rate?: number | null
}

export interface FrameworkPricing {
  model: PricingModel.FRAMEWORK
  deposit: number
  /** Remaining balance, computed by BE; FE displays it read-only. */
  drawdown_balance: number
  unit_rate: number
}

export interface FFSPricing {
  model: PricingModel.FFS
  unit_rate: number
}

export interface AdminUtilisationPricing {
  model: PricingModel.ADMIN_UTILISATION
  monthly_admin_fee: number
  /** Hard floor on monthly admin fee — flags warnings if pricing dips below. */
  admin_floor: number
  utilisation_rate: number
}

export interface ValueAddPricing {
  model: PricingModel.VALUE_ADD
  monthly_fee: number
  bundled_services: string[]
}

export interface RateCardItem {
  service_id: string
  service_name: string
  rate: number
}

/**
 * Invoice-line preview row returned from BE per contract pricing config.
 */
export interface InvoiceLinePreview {
  label: string
  quantity: number
  unit: string
  unit_rate: number
  subtotal: number
  /** Rendered footnote for context (e.g. "below admin floor"). */
  note?: string | null
}

/**
 * Service provider (counsellor / agency / clinic) — D-Provider v1.
 */
export interface Provider extends BaseEntity {
  name: string
  tier: ProviderTier
  region: ProviderRegion
  email?: string | null
  phone?: string | null
  accreditation: ProviderAccreditation
  non_compete_clauses: ProviderNonCompete[]
  /** Tier transitions, most-recent first. */
  tier_audit?: ProviderTierTransition[]
}

export interface ProviderAccreditation {
  body: string
  registration_number: string
  status: AccreditationStatus
  issued_at: string
  expires_at: string
}

export interface ProviderNonCompete {
  id: string
  client_id: string
  client_name: string
  /** Effective range — both ISO dates. */
  start_date: string
  end_date: string
  /** Region scope of the non-compete. Empty array = global. */
  regions: ProviderRegion[]
  notes?: string | null
}

export interface ProviderTierTransition {
  id: string
  from_tier: ProviderTier | null
  to_tier: ProviderTier
  at: string
  actor: string
  reason: string
}

/**
 * Critical Incident (CISM v1).
 */
export interface Incident extends BaseEntity {
  client_id: string
  title: string
  description: string
  severity: IncidentSeverity
  status: IncidentStatus
  occurred_at: string
  affected_population: number
  /** Service-session IDs linked from the incident timeline. */
  linked_session_ids?: string[]
  resolution_notes?: string | null
}

export interface IncidentTimelineEvent {
  id: string
  incident_id: string
  kind: IncidentTimelineEventKind
  at: string
  actor: string
  message: string
  /** When `kind === SESSION_LINKED`, references the linked service session. */
  session_id?: string | null
}

/**
 * Diagnosis taxonomy node (ICD-10 subset for v1).
 * Children are expanded lazily via diagnosesApi.list({ parent_id }).
 */
export interface Diagnosis {
  id: string
  code: string
  label: string
  parent_id: string | null
  level: number
  has_children: boolean
  /** Slash-joined full path of labels, useful for combobox display. */
  path: string
}

/**
 * Service Assignment
 */
export interface ServiceAssignment extends BaseEntity {
  contract_id: string
  service_id: string
  status: BaseStatus
  /** Internal notes per BE `ServiceAssignmentResponse.notes`. */
  notes?: string | null
}

/**
 * Document
 */
export interface Document extends BaseEntity {
  name: string
  document_type: DocumentType
  status: DocumentStatus
  file_path?: string | null
  file_size?: number | null
  mime_type?: string | null
  version?: number | null
  confidentiality_level?: string | null
  expiry_date?: string | null
  published_at?: string | null
  metadata?: Record<string, unknown> | null
}

/**
 * KPI
 */
export interface KPI extends BaseEntity {
  name: string
  description?: string | null
  category: KPICategory
  measurement_unit: MeasurementUnit
  target_value?: number | null
  current_value?: number | null
  metadata?: Record<string, unknown> | null
}

/**
 * KPI Assignment
 */
export interface KPIAssignment extends BaseEntity {
  kpi_id: string
  assignable_type: 'Client' | 'Contract'
  assignable_id: string
  target_value?: number | null
  start_date?: string | null
  end_date?: string | null
}

/**
 * Contact (client contact person)
 */
export interface Contact extends BaseEntity {
  client_id: string
  first_name: string
  last_name: string
  title?: string | null
  is_primary: boolean
  status: BaseStatus
  contact_info?: ContactInfo | null
  metadata?: Record<string, unknown> | null
}

/**
 * Activity (client interaction log)
 */
export interface Activity extends BaseEntity {
  client_id: string
  activity_type: ActivityType
  title?: string | null
  description?: string | null
  occurred_at: string
  user_id?: string | null
  metadata?: Record<string, unknown> | null
}

/**
 * Industry
 */
export interface Industry extends BaseEntity {
  name: string
  code?: string | null
  parent_id?: string | null
  level?: number | null
  metadata?: Record<string, unknown> | null
}

/**
 * Client Tag
 */
export interface ClientTag extends BaseEntity {
  name: string
  color?: string | null
  description?: string | null
}

/**
 * Questionnaire (dynamic survey definition; drives the triage renderer in Phase 3 #1).
 * BE owns the canonical Joseph 7-variable + WOS-5 instruments; FE renders dispatch on
 * `Question.type`.
 */
export interface Questionnaire {
  id: string
  code: string
  title: string
  description?: string | null
  /** Pre-session, post-session, or standalone administration. */
  administration: QuestionnaireAdministration
  questions: QuestionnaireQuestion[]
  /** Locked instruments are clinical (Joseph 7-var, WOS-5, PHQ-9 item-9) and cannot be edited from the UI. */
  is_locked: boolean
}

export interface QuestionnaireQuestion {
  id: string
  /** Stable key emitted in answers; also used for crisis-flag rules (e.g. `phq9_item9`). */
  key: string
  prompt: string
  type: QuestionnaireQuestionType
  required: boolean
  /** For SCALE: numeric range and labels (e.g. WOS-5 0-5). */
  scale_min?: number | null
  scale_max?: number | null
  scale_min_label?: string | null
  scale_max_label?: string | null
  /** For SINGLE_CHOICE / MULTI_CHOICE / YES_NO. */
  options?: QuestionnaireOption[]
  help_text?: string | null
}

export interface QuestionnaireOption {
  value: string
  label: string
  /** When non-null, picking this option contributes to the question's score. */
  score?: number | null
}

/**
 * Counsellor-Initiated Care Call campaign (Phase 3 flagship).
 *
 * One campaign defines audience + sampling + period + counsellor pool. The BE generates
 * `CallbackCase` rows — one per sampled person — into each counsellor's worklist.
 */
export interface CallbackCampaign extends BaseEntity {
  client_id: string
  name: string
  description?: string | null
  status: CallbackCampaignStatus
  /** ISO date — first day cases are opened for outreach. */
  period_start: string
  /** ISO date — outreach window closes; cases not yet completed roll into reporting as no-answer. */
  period_end: string
  sampling: CallbackSamplingStrategy
  /** Honoured when `sampling !== FULL`. */
  sample_size?: number | null
  /** User IDs of counsellors assigned to the pool. The pool drives case round-robin. */
  counsellor_user_ids: string[]
  /** Slug of the questionnaire used for triage (must match a `Questionnaire.code`). */
  questionnaire_code: string
  /** Optional WOS-5 follow-up administered after the call (`Questionnaire.code`). */
  followup_questionnaire_code?: string | null
  /** Set when the campaign was generated. Read-only for the FE. */
  case_count: number
  cases_completed: number
  cases_in_progress: number
}

/**
 * One person × campaign assignment. The counsellor works the queue, runs triage, and
 * records an outcome. Crisis flags raise `CRISIS_ESCALATED` and notify the supervisor.
 */
export interface CallbackCase extends BaseEntity {
  campaign_id: string
  person_id: string
  /** Denormalised for worklist rendering. The BE strips PII at the report layer. */
  person_display_name: string
  /** ID of the source service-session that made the person eligible for this campaign. */
  source_session_id?: string | null
  assigned_user_id: string
  status: CallbackCaseStatus
  /** Set when the counsellor opens the case. */
  started_at?: string | null
  /** Set on `COMPLETED` / `NO_ANSWER` / `DECLINED` / `CRISIS_ESCALATED`. */
  closed_at?: string | null
  /** ISO date — when the next attempt is allowed for `NO_ANSWER` cases. */
  next_attempt_at?: string | null
  attempt_count: number
  /** Set when an outcome has been recorded. */
  outcome_id?: string | null
  /** Latched when the questionnaire emits a crisis answer (e.g. PHQ-9 item-9 > 0). */
  crisis_flagged: boolean
}

/**
 * Triage outcome for a single case. Answers are `key → primitive` (numeric scale, choice id, free text).
 * BE stores the canonical aggregate; FE only ever submits a fresh outcome.
 */
export interface CallbackOutcome {
  id: string
  case_id: string
  questionnaire_code: string
  followup_questionnaire_code?: string | null
  /** Pre-call answers (Joseph 7-variable + PHQ-9 item-9). */
  pre_answers: Record<string, string | number | string[] | null>
  /** Optional post-call follow-up (WOS-5 post). May be empty if call did not complete. */
  post_answers?: Record<string, string | number | string[] | null> | null
  /** Free-text counsellor notes — must NEVER appear in aggregated reports. */
  counsellor_notes?: string | null
  /** True when at least one rule fired (e.g. PHQ-9 item-9 > 0). */
  crisis_flagged: boolean
  /** Human-readable list of triggered rules; rendered in the case timeline. */
  crisis_reasons: string[]
  recorded_at: string
  recorded_by_user_id: string
}

/**
 * Aggregated, no-PII rollup for a finished campaign — what the per-client renewal pack
 * (Phase 3 #3) consumes. BE enforces a k-anon floor (assumption A-19 = 10) and returns
 * `null` cells when the floor is unmet.
 */
export interface CallbackCampaignAggregate {
  campaign_id: string
  cases_total: number
  cases_completed: number
  cases_no_answer: number
  cases_declined: number
  cases_crisis: number
  /** Mean WOS-5 delta across completed cases; null when k-floor unmet. */
  wos5_delta_mean?: number | null
  /** Per-question summary (mean scale value or option histogram). */
  question_summaries: CallbackQuestionSummary[]
  /** True when k-anon floor is satisfied — gate dashboards on this. */
  k_floor_met: boolean
}

export interface CallbackQuestionSummary {
  question_key: string
  prompt: string
  /** For SCALE / numeric: mean of recorded answers. */
  mean?: number | null
  /** For choice questions: option_value → count. */
  histogram?: Record<string, number> | null
  /** Number of completed answers contributing to this row. */
  n: number
}

/**
 * Survey campaign (Phase 3 #2).
 *
 * The Evexía BE doesn't host the form — clients run Google Forms / Typeform / etc., and
 * the survey provider POSTs each response to the webhook URL stored on this entity.
 * Aggregates compute server-side and respect the same k-anon floor as care-callbacks.
 */
export interface Survey extends BaseEntity {
  client_id: string
  name: string
  description?: string | null
  status: SurveyStatus
  source: SurveySource
  /** Webhook URL the BE exposes; copied into the form's "send response to URL" field. */
  webhook_url: string
  /** Shared secret the survey provider must include in the `X-Evexia-Token` header. */
  webhook_token: string
  /** Inclusive collection window. */
  period_start: string
  period_end: string
  /** Set when status flips to COLLECTING. Read-only. */
  first_response_at?: string | null
  /** Set when status flips to CLOSED. Read-only. */
  closed_at?: string | null
  response_count: number
}

/**
 * Aggregated, no-PII rollup for a survey. K-anon floor mirrors care-callbacks (= 10).
 */
export interface SurveyAggregate {
  survey_id: string
  response_count: number
  /** Mean satisfaction (1-5) across all responses; null when k-floor unmet. */
  satisfaction_mean?: number | null
  /** Net Promoter Score buckets — promoters minus detractors as %; null when k-floor unmet. */
  nps?: number | null
  /** Per-question summaries — same shape as the care-callback aggregate. */
  question_summaries: SurveyQuestionSummary[]
  k_floor_met: boolean
}

export interface SurveyQuestionSummary {
  question_key: string
  prompt: string
  mean?: number | null
  histogram?: Record<string, number> | null
  n: number
}

/**
 * Consultancy engagement (Phase 4 #1). Tracks scope, deliverables, hours-logged, and a
 * status FSM. Hours roll up from the time entries; deliverables have an independent
 * status so a single engagement can be partially delivered.
 */
export interface Engagement extends BaseEntity {
  client_id: string
  name: string
  description?: string | null
  status: EngagementStatus
  engagement_type: EngagementType
  /** ISO date — when scoping was signed off and work began. */
  start_date: string
  /** ISO date — agreed delivery date. Slips trigger a yellow indicator in the list. */
  due_date?: string | null
  /** Set when status transitions to CLOSED. */
  closed_at?: string | null
  /** Hourly rate snapshot at engagement-create time. BE owns canonical rate cards. */
  hourly_rate?: number | null
  currency?: string | null
  /** Hours budgeted; null = open-ended. */
  budget_hours?: number | null
  /** Sum of `EngagementTimeEntry.hours` for this engagement. Read-only. */
  hours_logged: number
  /** Lead consultant on the engagement (Person.id from PlatformStaff). */
  lead_user_id?: string | null
}

export interface EngagementDeliverable {
  id: string
  engagement_id: string
  title: string
  description?: string | null
  status: DeliverableStatus
  /** ISO date — agreed delivery date for *this* deliverable. */
  due_date?: string | null
  /** Set when status transitions to SUBMITTED / ACCEPTED. */
  submitted_at?: string | null
  accepted_at?: string | null
  /** Optional document URL or note. */
  artefact_url?: string | null
  created_at: string
  updated_at: string
}

export interface EngagementTimeEntry {
  id: string
  engagement_id: string
  user_id: string
  /** ISO date — the day the work happened. */
  occurred_on: string
  hours: number
  description?: string | null
  /** Optional reference to a deliverable. */
  deliverable_id?: string | null
  created_at: string
}

export interface EngagementTimelineEvent {
  id: string
  engagement_id: string
  kind: EngagementTimelineEventKind
  at: string
  actor: string
  message: string
  /** When kind === DELIVERABLE_*, references the deliverable. */
  deliverable_id?: string | null
}

/**
 * Audit Log
 */
export interface AuditLog {
  id: string
  tenant_id?: string | null
  user_id?: string | null
  action_type: string
  resource_type: string
  resource_id: string
  changes?: Record<string, unknown> | null
  ip_address?: string | null
  user_agent?: string | null
  created_at: string
}
