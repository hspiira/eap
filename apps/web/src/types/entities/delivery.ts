import type {
  BaseStatus,
  ClientType,
  DocumentStatus,
  DocumentType,
  KPICategory,
  MeasurementUnit,
  SessionCategory,
  SessionClinicalStatus,
  SessionStatus,
  SessionType,
} from '../enums'
import type { BaseEntity } from './base'

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
/** Mirrors BE `ServiceSessionResponse` — field names and types are wire-true. */
export interface ServiceSession extends BaseEntity {
  service_id: string
  person_id: string
  provider_id?: string | null
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
  /** Plain text on the wire — there is no structured rating object. */
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
  assignable_type: 'Client' | 'Contract'
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
