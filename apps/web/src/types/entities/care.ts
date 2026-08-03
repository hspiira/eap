import type {
  CallbackCampaignStatus,
  CallbackCaseStatus,
  CallbackSamplingStrategy,
  IncidentSeverity,
  IncidentStatus,
  IncidentTimelineEventKind,
  QuestionnaireAdministration,
  QuestionnaireQuestionType,
  SurveySource,
  SurveyStatus,
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
 * Counsellor-Initiated Care Call campaign (Phase 3 flagship).
 *
 * One campaign defines audience + sampling + period + counsellor pool. The BE generates
 * `CallbackCase` rows — one per sampled person — into each counsellor's worklist.
 */
export interface CallbackCampaign extends BaseEntity {
  client_id: string
  name: string
  description?: string | null
  status: CallbackCampaignStatus
  /** ISO date — first day cases are opened for outreach. */
  period_start: string
  /** ISO date — outreach window closes; cases not yet completed roll into reporting as no-answer. */
  period_end: string
  sampling: CallbackSamplingStrategy
  /** Honoured when `sampling !== FULL`. */
  sample_size?: number | null
  /** User IDs of counsellors assigned to the pool. The pool drives case round-robin. */
  counsellor_user_ids: string[]
  /** Slug of the questionnaire used for triage (must match a `Questionnaire.code`). */
  questionnaire_code: string
  /** Optional WOS-5 follow-up administered after the call (`Questionnaire.code`). */
  followup_questionnaire_code?: string | null
  /** Set when the campaign was generated. Read-only for the FE. */
  case_count: number
  cases_completed: number
  cases_in_progress: number
}

/**
 * One person × campaign assignment. The counsellor works the queue, runs triage, and
 * records an outcome. Crisis flags raise `CRISIS_ESCALATED` and notify the supervisor.
 */
export interface CallbackCase extends BaseEntity {
  campaign_id: string
  person_id: string
  /** Denormalised for worklist rendering. The BE strips PII at the report layer. */
  person_display_name: string
  /** ID of the source service-session that made the person eligible for this campaign. */
  source_session_id?: string | null
  assigned_user_id: string
  status: CallbackCaseStatus
  /** Set when the counsellor opens the case. */
  started_at?: string | null
  /** Set on `COMPLETED` / `NO_ANSWER` / `DECLINED` / `CRISIS_ESCALATED`. */
  closed_at?: string | null
  /** ISO date — when the next attempt is allowed for `NO_ANSWER` cases. */
  next_attempt_at?: string | null
  attempt_count: number
  /** Set when an outcome has been recorded. */
  outcome_id?: string | null
  /** Latched when the questionnaire emits a crisis answer (e.g. PHQ-9 item-9 > 0). */
  crisis_flagged: boolean
}

/**
 * Triage outcome for a single case. Answers are `key → primitive` (numeric scale, choice id, free text).
 * BE stores the canonical aggregate; FE only ever submits a fresh outcome.
 */
export interface CallbackOutcome {
  id: string
  case_id: string
  questionnaire_code: string
  followup_questionnaire_code?: string | null
  /** Pre-call answers (Joseph 7-variable + PHQ-9 item-9). */
  pre_answers: Record<string, string | number | string[] | null>
  /** Optional post-call follow-up (WOS-5 post). May be empty if call did not complete. */
  post_answers?: Record<string, string | number | string[] | null> | null
  /** Free-text counsellor notes — must NEVER appear in aggregated reports. */
  counsellor_notes?: string | null
  /** True when at least one rule fired (e.g. PHQ-9 item-9 > 0). */
  crisis_flagged: boolean
  /** Human-readable list of triggered rules; rendered in the case timeline. */
  crisis_reasons: string[]
  recorded_at: string
  recorded_by_user_id: string
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
