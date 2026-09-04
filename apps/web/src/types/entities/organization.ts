import type { ActivityType, BaseStatus, ClientTier } from "../enums"
import type { BaseEntity, ContactInfo } from "./base"

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
  aliases?: string[]
  metadata?: Record<string, unknown> | null
}

/**
 * Industry
 */
export interface Industry extends BaseEntity {
  name: string
  code?: string | null
  description?: string | null
  parent_industry_id?: string | null
  is_active?: boolean
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
