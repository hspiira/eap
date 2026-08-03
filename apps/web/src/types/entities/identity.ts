import type {
  AccessScope,
  AuthProvider,
  BaseStatus,
  Language,
  PersonType,
  RelationType,
  StaffRole,
  TenantRole,
  TenantStatus,
  UserStatus,
  WorkStatus,
} from '../enums'
import type { Address, BaseEntity, ContactInfo, EmergencyContact } from './base'
import type { ProviderProfile } from './providers'

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
  role?: TenantRole | null
  azure_oid?: string | null
  display_name?: string | null
  auth_provider?: AuthProvider
  access_scopes?: AccessScope[]
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
  /** Set when person_type === ServiceProvider. Carries panel/tier/accreditation. */
  provider_profile?: ProviderProfile | null
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
