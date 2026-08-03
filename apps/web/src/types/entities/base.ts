import type {
  ContactMethod,
} from '../enums'

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
 * Emergency contact
 */
export interface EmergencyContact {
  name?: string | null
  phone?: string | null
  email?: string | null
}
