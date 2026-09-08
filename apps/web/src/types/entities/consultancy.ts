/**
 * Consultancy engagement (Phase 4 #1).
 *
 * These are the API's own response shapes, generated from the OpenAPI contract.
 * They were hand-written before, and had drifted into a different entity: the
 * old shape carried `engagement_type`, `start_date`, `hourly_rate`,
 * `budget_hours` and `lead_user_id`, none of which the API has, and lacked the
 * embedded `deliverables` and `hours_log` the API returns on every engagement
 * (MODULES_REPAIR_PLAN API-01, ENG-01).
 */

import type { Schemas } from "@/api/generated"

export type Engagement = Schemas["EngagementResponse"]

/**
 * The status values as the API spells them. The `EngagementStatus` enum stays
 * the vocabulary for building option lists; this is the type on the wire, and a
 * value read back from the API is one of these, not an enum member.
 */
export type EngagementStatusValue = Schemas["EngagementStatus"]
export type DeliverableStatusValue = Schemas["DeliverableStatus"]
export type EngagementList = Schemas["EngagementListResponse"]
export type EngagementDeliverable = Schemas["DeliverableResponse"]
export type EngagementTimeEntry = Schemas["HoursLogResponse"]
export type EngagementSummary = Schemas["EngagementSummaryResponse"]

/** Sum of the engagement's embedded hours-log entries. */
export function engagementHours(engagement: Engagement): number {
  return engagement.hours_log.reduce((total, entry) => total + entry.hours, 0)
}
