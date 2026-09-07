import type {
  BaseStatus,
  ClientType,
  DocumentStatus,
  DocumentType,
  KPICategory,
  MeasurementUnit,
  ServiceCategory,
  SessionAttendance,
  SessionCategory,
  SessionClinicalStatus,
  SessionDeliveryContext,
  SessionStatus,
  SessionType,
} from "../enums"
import type { BaseEntity } from "./base"

/**
 * Service
 */
export interface Service extends BaseEntity {
  name: string
  description?: string | null
  status: BaseStatus
  category?: ServiceCategory | null
  duration_minutes?: number | null
  /** Whether this is a group service per BE `ServiceResponse.is_group_service`. */
  is_group_service?: boolean
  /** Group session capacity cap per BE `ServiceResponse.max_participants`. */
  max_participants?: number | null
}

/**
 * Service Session
 */
/** Mirrors BE `ServiceSessionResponse`: field names and types are wire-true. */
export interface ServiceSession extends BaseEntity {
  service_id: string
  /**
   * Who the session was delivered to. `CompanyWide` is a health talk or site
   * visit: a real session delivered to a client with nobody individual to
   * name, so it carries a headcount and no member.
   */
  attendance: SessionAttendance
  /** Absent on a company-wide session. */
  member_id?: string | null
  /** Every session is attributed to a client, including one with no member. */
  client_id: string
  /** Display names resolved by the list endpoint; absent means unresolved. */
  client_name?: string | null
  member_display_label?: string | null
  provider_display_name?: string | null
  service_name?: string | null
  provider_id?: string | null
  /**
   * How the session was delivered. `Unknown` belongs to historical records
   * whose source does not say, and must be shown as unknown rather than
   * treated as direct delivery.
   */
  delivery_context?: SessionDeliveryContext | null
  /** The affiliation this session was delivered under, for `Organisation`. */
  provider_affiliation_id?: string | null
  /**
   * Read from the session's own stored affiliation, never from the
   * practitioner's current affiliations, so moving firms does not reattribute
   * a past session. Null for direct and unknown delivery.
   */
  provider_organisation_id?: string | null
  status: SessionStatus
  scheduled_at: string
  completed_at?: string | null
  duration?: number | null
  location?: string | null
  notes?: string | null
  category?: SessionCategory | null
  session_type?: SessionType | null
  client_type?: ClientType | null
  clinical_outcome?: SessionClinicalStatus | null
  headcount?: number | null
  issue_topic?: string | null
  partner_name?: string | null
  partner_relationship?: string | null
  rate_ugx?: number | null
  session_number?: number | null
  approved_by?: string | null
  diagnosis_id?: string | null
  diagnosis_type_id?: string | null
  cancellation_reason?: string | null
  reschedule_count?: number | null
  /** Plain text on the wire: there is no structured rating object. */
  feedback?: string | null
  is_active?: boolean
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

/** A diagnosis category (e.g. "Mood (affective) disorders"). */
export interface DiagnosisType {
  id: string
  code: string
  name: string
  description?: string | null
  sort_order: number
}

/** A single codable diagnosis within a DiagnosisType. */
export interface Diagnosis {
  id: string
  code: string
  name: string
  description?: string | null
  type_id: string
  sort_order: number
}

/** Full two-level tree returned by GET /diagnoses/tree. */
export interface DiagnosisTree {
  types: (DiagnosisType & { diagnoses: Diagnosis[] })[]
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
  assignable_type: "Client" | "Contract"
  assignable_id: string
  target_value?: number | null
  start_date?: string | null
  end_date?: string | null
}

/**
 * Document
 */
export interface Document extends BaseEntity {
  name: string
  description?: string | null
  document_type: DocumentType
  status: DocumentStatus
  version?: number | null
  is_latest?: boolean
  file_path?: string | null
  file_url?: string | null
  file_size?: number | null
  mime_type?: string | null
  previous_version_id?: string | null
  uploaded_by?: string | null
  client_id?: string | null
  contract_id?: string | null
  person_id?: string | null
  expires_at?: string | null
  is_confidential?: boolean
  published_at?: string | null
  archived_at?: string | null
  is_active?: boolean
}

/** Billable usage recorded against a contract. */
export interface UtilisationEvent extends BaseEntity {
  contract_id: string
  event_type: string
  occurred_on: string
  units: number
  service_code?: string | null
  source_id?: string | null
  notes?: string | null
}
