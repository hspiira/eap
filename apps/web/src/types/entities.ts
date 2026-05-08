/**
 * Entity Type Definitions
 * TypeScript interfaces for all API entities
 */

import type {
  ActivityType,
  BaseStatus,
  ClientTier,
  ContactMethod,
  AccreditationStatus,
  IncidentSeverity,
  IncidentStatus,
  IncidentTimelineEventKind,
  PricingModel,
  ProviderRegion,
  ProviderTier,
  ContractStatus,
  DocumentStatus,
  DocumentType,
  KPICategory,
  Language,
  MeasurementUnit,
  PaymentFrequency,
  PaymentStatus,
  PersonType,
  RelationType,
  SessionStatus,
  StaffRole,
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
export interface Tenant extends BaseEntity {
  name: string
  code?: string | null // Tenant code (e.g., "acme-corp")
  status: TenantStatus
  subscription_tier?: string | null // Subscription tier (e.g., "Free", "Pro", "Enterprise")
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
 * Person (employee, dependent, service provider, platform staff)
 */
export interface Person extends BaseEntity {
  first_name: string
  last_name: string
  middle_name?: string | null
  person_type: PersonType
  date_of_birth?: string | null
  gender?: string | null
  status: BaseStatus
  user_id: string
  is_dual_role?: boolean
  secondary_person_type?: PersonType | null
  last_service_date?: string | null
  is_eligible_for_services?: boolean
  client_id?: string | null // For ClientEmployee and Dependent
  parent_person_id?: string | null // DEPRECATED: For Dependent - use dependent_info instead
  family_id?: string | null
  dependent_info?: DependentInfo | null // For Dependent - replaces parent_person_id usage
  contact_info?: ContactInfo | null
  address?: Address | null
  emergency_contact?: EmergencyContact | null
  employment_info?: EmploymentInfo | null
  license_info?: LicenseInfo | null
  staff_info?: StaffInfo | null
  secondary_roles?: PersonType[]
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
  contract_number?: string | null
  status: ContractStatus
  start_date: string
  end_date?: string | null
  renewal_date?: string | null
  billing_frequency?: PaymentFrequency | null
  billing_amount?: number | null
  currency?: string | null
  payment_status?: PaymentStatus | null
  metadata?: Record<string, unknown> | null
}

/**
 * Service
 */
export interface Service extends BaseEntity {
  name: string
  description?: string | null
  status: BaseStatus
  service_type?: string | null
  category?: string | null
  duration_minutes?: number | null
  group_settings?: {
    max_group_size?: number | null
    min_group_size?: number | null
    allow_group_sessions?: boolean
  } | null
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
  start_date?: string | null
  end_date?: string | null
  metadata?: Record<string, unknown> | null
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
