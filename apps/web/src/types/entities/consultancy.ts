import type {
  DeliverableStatus,
  EngagementStatus,
  EngagementTimelineEventKind,
  EngagementType,
} from '../enums'
import type { BaseEntity } from './base'

/**
 * Consultancy engagement (Phase 4 #1). Tracks scope, deliverables, hours-logged, and a
 * status FSM. Hours roll up from the time entries; deliverables have an independent
 * status so a single engagement can be partially delivered.
 */
export interface Engagement extends BaseEntity {
  client_id: string
  name: string
  description?: string | null
  status: EngagementStatus
  engagement_type: EngagementType
  /** ISO date — when scoping was signed off and work began. */
  start_date: string
  /** ISO date — agreed delivery date. Slips trigger a yellow indicator in the list. */
  due_date?: string | null
  /** Set when status transitions to CLOSED. */
  closed_at?: string | null
  /** Hourly rate snapshot at engagement-create time. BE owns canonical rate cards. */
  hourly_rate?: number | null
  currency?: string | null
  /** Hours budgeted; null = open-ended. */
  budget_hours?: number | null
  /** Sum of `EngagementTimeEntry.hours` for this engagement. Read-only. */
  hours_logged: number
  /** Lead consultant on the engagement (Person.id from PlatformStaff). */
  lead_user_id?: string | null
}

export interface EngagementDeliverable {
  id: string
  engagement_id: string
  title: string
  description?: string | null
  status: DeliverableStatus
  /** ISO date — agreed delivery date for *this* deliverable. */
  due_date?: string | null
  /** Set when status transitions to SUBMITTED / ACCEPTED. */
  submitted_at?: string | null
  accepted_at?: string | null
  /** Optional document URL or note. */
  artefact_url?: string | null
  created_at: string
  updated_at: string
}

export interface EngagementTimeEntry {
  id: string
  engagement_id: string
  user_id: string
  /** ISO date — the day the work happened. */
  occurred_on: string
  hours: number
  description?: string | null
  /** Optional reference to a deliverable. */
  deliverable_id?: string | null
  created_at: string
}

export interface EngagementTimelineEvent {
  id: string
  engagement_id: string
  kind: EngagementTimelineEventKind
  at: string
  actor: string
  message: string
  /** When kind === DELIVERABLE_*, references the deliverable. */
  deliverable_id?: string | null
}
