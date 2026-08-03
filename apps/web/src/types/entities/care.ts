import type {
  CareCallbackCampaignStatus,
  IncidentSeverity,
  IncidentStatus,
  IncidentTimelineEventKind,
  OutreachStatus,
  QuestionnaireAdministration,
  QuestionnaireQuestionType,
  SurveySource,
  SurveyStatus,
  TriageRiskLevel,
} from '../enums'
import type { BaseEntity } from './base'

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
 * Counsellor-Initiated Care Callback campaign — mirrors BE `CareCallbackCampaignResponse`.
 *
 * A campaign defines a target audience size + period + counsellor pool for a client.
 * `POST /enrol` adds persons; each becomes a Pending `OutreachRecord` that a counsellor
 * must explicitly claim (assign) before working it — there is no auto round-robin.
 *
 * Known BE gap: `completed_count`/derived `progress_ratio` never update — nothing calls
 * the entity's `increment_completed()`. Derive "completed" from a campaign summary's
 * `outreach_by_status.Completed` instead of trusting this field.
 */
export interface CallbackCampaign extends BaseEntity {
  client_id: string
  name: string
  period_start: string
  period_end: string
  target_count: number
  completed_count: number
  counsellor_pool: string[]
  status: CareCallbackCampaignStatus
  sampling_notes?: string | null
  created_by: string
  activated_at?: string | null
  completed_at?: string | null
}

/** Mirrors BE `CampaignSummaryResponse` (`GET /care-callback-campaigns/{id}/summary`). */
export interface CallbackCampaignSummary {
  campaign_id: string
  client_id: string
  name: string
  status: CareCallbackCampaignStatus
  target_count: number
  completed_count: number
  progress_ratio: number
  outreach_total: number
  /** Keys are OutreachStatus values; a status with zero records is simply absent. */
  outreach_by_status: Partial<Record<OutreachStatus, number>>
  triage_completed: number
  crisis_flags: number
  period_start: string
  period_end: string
  generated_at: string
}

/**
 * One person's outreach within a campaign — mirrors BE `OutreachRecordResponse`.
 * Pending -> Assigned -> Contacted -> one of the four terminal statuses.
 * Unlike a clinical Case, `person_id` here is a real person reference — Care
 * Callbacks is not behind the clinical privacy wall.
 */
export interface OutreachRecord extends BaseEntity {
  campaign_id: string
  person_id: string
  counsellor_id?: string | null
  status: OutreachStatus
  contact_attempts: number
  assigned_at?: string | null
  last_attempted_at?: string | null
  completed_at?: string | null
  /** Plain string on the wire, not enum-validated in the response. */
  triage_instrument_code?: string | null
  triage_risk_level?: TriageRiskLevel | null
  crisis_flag: boolean
  notes?: string | null
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
