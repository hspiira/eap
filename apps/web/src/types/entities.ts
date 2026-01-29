/**
 * Entity Type Definitions
 * TypeScript interfaces for all API entities
 */

import type {
  BaseStatus,
  UserStatus,
  TenantStatus,
  ContractStatus,
  SessionStatus,
  DocumentStatus,
  PersonType,
  WorkStatus,
  ContactMethod,
  Language,
  PaymentStatus,
  PaymentFrequency,
  DocumentType,
  KPICategory,
  MeasurementUnit,
  ActivityType,
  RelationType,
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
  client_id?: string | null // For ClientEmployee and Dependent
  parent_person_id?: string | null // DEPRECATED: For Dependent - use dependent_info instead
  family_id?: string | null
  dependent_info?: DependentInfo | null // For Dependent - replaces parent_person_id usage
  contact_info?: ContactInfo | null
  address?: Address | null
  emergency_contact?: {
    name?: string | null
    relationship?: string | null
    phone?: string | null
  } | null
  employment_info?: {
    client_id?: string | null
    employee_code?: string | null
    employee_id?: string | null
    department?: string | null
    position?: string | null
    hire_date?: string | null
    work_status?: WorkStatus | null
    end_date?: string | null
  } | null
  license_info?: {
    license_number?: string | null
    license_type?: string | null
    issuing_authority?: string | null
    issue_date?: string | null
    expiry_date?: string | null
  } | null
  staff_info?: {
    role?: string | null
    department?: string | null
  } | null
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
  is_verified: boolean
  status: BaseStatus
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
  feedback?: {
    rating?: number | null
    comments?: string | null
  } | null
  metadata?: Record<string, unknown> | null
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
