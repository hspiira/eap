import type {
  AccreditationStatus,
  BaseStatus,
  NonCompeteStatus,
  OrganisationApprovalStatus,
  PanelStatus,
  ProviderGender,
  ProviderIdentityProvenance,
  ProviderTier,
  UgandaRegion,
} from "../enums"
import type { LicenseInfo } from "./identity"

/**
 * Panel profile of a practitioner: mirrors BE `ProviderProfileSchema`.
 *
 * The API groups these fields because they are exactly the set a general
 * `PATCH /providers/{id}` refuses to write. Tier, panel status and the
 * accreditation fields move only through the lifecycle commands.
 */
export interface ProviderProfile {
  /** Null until a person assesses the practitioner; imports never guess it. */
  tier?: ProviderTier | null
  region?: UgandaRegion | null
  accreditation_status: AccreditationStatus
  panel_status: PanelStatus
  accreditation_authority?: string | null
  accreditation_expiry?: string | null
  /**
   * Legacy free-text list, read-only and not displayed. A practitioner's
   * specialties are the catalogue links from
   * `GET /provider-specialties/links`; this field becomes a projection of them
   * when the typed profile migration lands.
   */
  specialties: string[]
  bio?: string | null
  gender?: ProviderGender | null
}

/**
 * A practitioner: the individual who delivers a session. Mirrors BE
 * `ProviderResponse`.
 *
 * `display_name` is owned by the practitioner and always present. `email` is
 * their contact address, not a login, and `user_id` is an optional linked
 * account: a practitioner exists without either.
 */
export interface Provider {
  id: string
  tenant_id: string
  display_name: string
  email: string | null
  phone: string | null
  user_id: string | null
  status: BaseStatus
  /** Whether the name was entered for the practitioner or backfilled from an account. */
  identity_provenance: ProviderIdentityProvenance
  provider_profile: ProviderProfile
  license_info?: LicenseInfo | null
  created_at: string
  updated_at: string
}

/**
 * A supplier firm a practitioner can deliver through. Mirrors BE
 * `ProviderOrganisationResponse`.
 *
 * `is_active` and `approval_status` are independent: an organisation may
 * deliver only when it is active and approved.
 */
export interface ProviderOrganisation {
  id: string
  tenant_id: string
  name: string
  registration_number: string | null
  contact_email: string | null
  contact_phone: string | null
  is_active: boolean
  approval_status: OrganisationApprovalStatus
  created_at: string
  updated_at: string
}

/**
 * A dated record of a practitioner representing an organisation. Mirrors BE
 * `ProviderAffiliationResponse`.
 *
 * The interval is start-inclusive and end-exclusive: it covers
 * `valid_from <= t < valid_until`, and `valid_until` of null is open-ended.
 * The three `organisation_*` fields are the firm's current state joined on
 * read, for labelling a selector. They are not a historical snapshot.
 */
export interface ProviderAffiliation {
  id: string
  tenant_id: string
  provider_id: string
  organisation_id: string
  valid_from: string
  valid_until: string | null
  organisation_name: string
  organisation_is_active: boolean
  organisation_approval_status: OrganisationApprovalStatus
  created_at: string
  updated_at: string
}

/**
 * An entry of the global specialty vocabulary. Mirrors BE
 * `ProviderSpecialtyResponse`. Catalogue writes are platform-only; a tenant
 * selects active entries through its own provider links.
 */
export interface ProviderSpecialty {
  id: string
  code: string
  label: string
  is_active: boolean
}

/**
 * A tenant's link between one of its practitioners and a catalogue entry.
 *
 * `specialty_is_active` false means the entry was retired after this link was
 * made. The link is kept and still shown, but the entry cannot be selected
 * again.
 */
export interface ProviderSpecialtyLink {
  id: string
  tenant_id: string
  provider_id: string
  specialty_id: string
  specialty_code: string
  specialty_label: string
  specialty_is_active: boolean
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
 * Result of a pre-assignment eligibility check. Mirrors BE
 * `ProviderEligibilityResponse`.
 *
 * This is a preview. The booking write re-evaluates the same policy inside its
 * transaction, so a passing preview does not authorize anything.
 */
/** One failed check, with the stable code the API guarantees. */
export interface ProviderEligibilityFailure {
  code: string
  message: string
}

export interface ProviderEligibility {
  provider_id: string
  client_id: string | null
  scheduled_at: string
  panel_eligible: boolean
  binding_non_compete_count: number
  binding_non_compete_ids: string[]
  eligible: boolean
  reasons: string[]
  /** Prefer this over `reasons`: match on `code`, never on the message text. */
  failures: ProviderEligibilityFailure[]
}
