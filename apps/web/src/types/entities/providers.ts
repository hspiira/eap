import type {
  AccreditationStatus,
  NonCompeteStatus,
  PanelStatus,
  ProviderRegion,
  ProviderTier,
} from "../enums"
import type { LicenseInfo } from "./identity"

/**
 * Service provider (counsellor / agency / clinic): D-Provider v1.
 */
/**
 * Provider panel profile: mirrors BE `ProviderProfileSchema`.
 *
 * Providers are persisted independently from client members and platform staff.
 */
export interface ProviderProfile {
  tier: ProviderTier
  region: ProviderRegion
  accreditation_status: AccreditationStatus
  panel_status: PanelStatus
  accreditation_authority?: string | null
  accreditation_expiry?: string | null
  specialties: string[]
  bio?: string | null
}

/**
 * A non-compete clause restricting a provider from working with certain
 * clients. Mirrors BE `NonCompeteResponse`.
 */
export interface NonCompeteClause {
  id: string
  tenant_id: string
  provider_id: string
  status: NonCompeteStatus
  terms_summary: string
  effective_from: string
  effective_until: string | null
  signed_at: string | null
  signed_by: string | null
  revoked_at: string | null
  revoked_reason: string | null
  document_id: string | null
  created_at: string
  updated_at: string
}

/**
 * Provider view with its required panel profile.
 */
export interface Provider {
  id: string
  tenant_id: string
  user_id: string
  display_name?: string | null
  email: string
  status: string
  provider_profile: ProviderProfile
  license_info?: LicenseInfo | null
  created_at: string
  updated_at: string
}

/**
 * Result of a pre-assignment eligibility check. Mirrors BE `ProviderEligibilityResponse`.
 */
export interface ProviderEligibility {
  provider_id: string
  client_id: string | null
  panel_eligible: boolean
  binding_non_compete_count: number
  binding_non_compete_ids: string[]
  eligible: boolean
  reasons: string[]
}
