/**
 * In-memory store for consultancy engagements (Phase 4 #1).
 *
 * Records carry the API's `EngagementResponse` shape, deliverables and hours
 * included, because that is where the API keeps them: the child routes are
 * mutations only. Listing goes through the shared fixture pager so fixture mode
 * answers the same envelope and filters as the API
 * (MODULES_REPAIR_PLAN API-01, ENG-01).
 */

import type { DeliverableCreate, EngagementCreate, HoursLogCreate } from "@/api/generated"
import type {
  Engagement,
  EngagementDeliverable,
  EngagementSummary,
  EngagementTimeEntry,
} from "@/types/entities"
import type { DeliverableStatusValue, EngagementStatusValue } from "@/types/entities"
import { DeliverableStatus, EngagementStatus } from "@/types/enums"

import type { EngagementListParams } from "./engagements"
import { fixturePage, type FixturePageEnvelope } from "./fixture-page"

const TENANT = "tenant-fixture"
const CREATED_BY = "user-helen"

const ENGAGEMENT_SEED: Engagement[] = [
  {
    id: "eng-001",
    tenant_id: TENANT,
    client_id: "fixture-stanbic",
    name: "Mental health policy refresh",
    description:
      "2026 mental-health policy redraft incorporating WIBA/ARA changes and new EAP scope.",
    status: EngagementStatus.ACTIVE,
    period_start: "2026-04-01",
    period_end: "2026-06-15",
    deliverables: [
      {
        id: "dlv-001",
        title: "Stakeholder interview pack",
        description: "Summary of interviews with HR, ops, and legal.",
        due_date: "2026-04-15",
        status: DeliverableStatus.ACCEPTED,
        delivered_at: "2026-04-14T09:00:00Z",
      },
      {
        id: "dlv-002",
        title: "Policy draft v1",
        description: "Initial policy draft for legal review.",
        due_date: "2026-05-20",
        status: DeliverableStatus.IN_PROGRESS,
        delivered_at: null,
      },
    ],
    hours_log: [
      {
        id: "te-001",
        user_id: "user-helen",
        logged_on: "2026-04-02",
        hours: 4,
        note: "Stakeholder interviews: HR + ops.",
      },
      {
        id: "te-002",
        user_id: "user-helen",
        logged_on: "2026-04-08",
        hours: 6,
        note: "Interview synthesis + memo draft.",
      },
      {
        id: "te-003",
        user_id: "user-helen",
        logged_on: "2026-04-29",
        hours: 8,
        note: "Policy draft outline.",
      },
    ],
    created_by: CREATED_BY,
    activated_at: "2026-04-01T09:00:00Z",
    delivered_at: null,
    invoiced_at: null,
    closed_at: null,
    created_at: "2026-03-25T10:00:00Z",
    updated_at: "2026-05-06T16:00:00Z",
  },
  {
    id: "eng-002",
    tenant_id: TENANT,
    client_id: "fixture-absa",
    name: "Manager mental-health training: Q2",
    description: "Two cohorts × half-day workshop. Includes pre/post evaluation.",
    status: EngagementStatus.DRAFT,
    period_start: "2026-05-20",
    period_end: "2026-07-10",
    deliverables: [],
    hours_log: [],
    created_by: "user-mary",
    activated_at: null,
    delivered_at: null,
    invoiced_at: null,
    closed_at: null,
    created_at: "2026-05-04T09:30:00Z",
    updated_at: "2026-05-04T09:30:00Z",
  },
  {
    id: "eng-003",
    tenant_id: TENANT,
    client_id: "fixture-stanbic",
    name: "Wellness audit: branch network",
    description: "On-site assessment + report covering 12 priority branches.",
    status: EngagementStatus.DELIVERED,
    period_start: "2026-01-15",
    period_end: "2026-03-31",
    deliverables: [
      {
        id: "dlv-003",
        title: "Branch audit report",
        description: "Findings + recommendations for the 12 priority branches.",
        due_date: "2026-03-31",
        status: DeliverableStatus.DELIVERED,
        delivered_at: "2026-04-01T16:00:00Z",
      },
    ],
    hours_log: [
      {
        id: "te-004",
        user_id: "user-helen",
        logged_on: "2026-03-10",
        hours: 24,
        note: "On-site visits: 8 branches.",
      },
      {
        id: "te-005",
        user_id: "user-mary",
        logged_on: "2026-03-25",
        hours: 14,
        note: "Findings synthesis + report draft.",
      },
    ],
    created_by: CREATED_BY,
    activated_at: "2026-01-15T09:00:00Z",
    delivered_at: "2026-04-02T15:00:00Z",
    invoiced_at: null,
    closed_at: null,
    created_at: "2026-01-10T11:00:00Z",
    updated_at: "2026-04-02T15:00:00Z",
  },
]

const engagementStore: Engagement[] = [...ENGAGEMENT_SEED]

function find(engagementId: string): Engagement {
  const target = engagementStore.find((e) => e.id === engagementId)
  if (!target) throw new Error(`Engagement ${engagementId} not found`)
  return target
}

export function fixtureListEngagements(
  params?: EngagementListParams,
): FixturePageEnvelope<Engagement> {
  return fixturePage(engagementStore, params, {
    search: ["name", "description", "client_id"],
    equals: ["status", "client_id"],
    defaultSort: "created_at",
  })
}

export function fixtureGetEngagement(id: string): Engagement | undefined {
  return engagementStore.find((e) => e.id === id)
}

export function fixtureCreateEngagement(input: EngagementCreate): Engagement {
  const now = new Date().toISOString()
  const engagement: Engagement = {
    id: `eng-${Math.random().toString(36).slice(2, 8)}`,
    tenant_id: TENANT,
    client_id: input.client_id,
    name: input.name,
    description: input.description ?? null,
    status: EngagementStatus.DRAFT,
    period_start: input.period_start ?? null,
    period_end: input.period_end ?? null,
    deliverables: [],
    hours_log: [],
    created_by: CREATED_BY,
    activated_at: null,
    delivered_at: null,
    invoiced_at: null,
    closed_at: null,
    created_at: now,
    updated_at: now,
  }
  engagementStore.unshift(engagement)
  return engagement
}

/**
 * Mirrors the domain FSM in app/domain/entities/engagement.py, which is a strict
 * chain.
 */
const ALLOWED_TRANSITIONS: Record<EngagementStatusValue, EngagementStatusValue[]> = {
  [EngagementStatus.DRAFT]: [EngagementStatus.ACTIVE],
  [EngagementStatus.ACTIVE]: [EngagementStatus.DELIVERED],
  [EngagementStatus.DELIVERED]: [EngagementStatus.INVOICED],
  [EngagementStatus.INVOICED]: [EngagementStatus.CLOSED],
  [EngagementStatus.CLOSED]: [],
}

const TRANSITION_TIMESTAMP: Partial<Record<EngagementStatusValue, keyof Engagement>> = {
  [EngagementStatus.ACTIVE]: "activated_at",
  [EngagementStatus.DELIVERED]: "delivered_at",
  [EngagementStatus.INVOICED]: "invoiced_at",
  [EngagementStatus.CLOSED]: "closed_at",
}

export function fixtureAllowedTransitions(from: EngagementStatusValue): EngagementStatusValue[] {
  return ALLOWED_TRANSITIONS[from] ?? []
}

export function fixtureTransitionEngagement(id: string, to: EngagementStatusValue): Engagement {
  const target = find(id)
  const allowed = ALLOWED_TRANSITIONS[target.status] ?? []
  if (!allowed.includes(to)) {
    throw new Error(`Cannot transition ${target.status} → ${to}`)
  }
  const now = new Date().toISOString()
  target.status = to
  target.updated_at = now
  const stamp = TRANSITION_TIMESTAMP[to]
  if (stamp) Object.assign(target, { [stamp]: now })
  return target
}

export function fixtureCreateDeliverable(
  engagementId: string,
  input: DeliverableCreate,
): EngagementDeliverable {
  const target = find(engagementId)
  const deliverable: EngagementDeliverable = {
    id: `dlv-${Math.random().toString(36).slice(2, 8)}`,
    title: input.title,
    description: input.description ?? null,
    due_date: input.due_date ?? null,
    status: DeliverableStatus.PENDING,
    delivered_at: null,
  }
  target.deliverables.push(deliverable)
  target.updated_at = new Date().toISOString()
  return deliverable
}

export function fixtureUpdateDeliverableStatus(
  engagementId: string,
  deliverableId: string,
  status: DeliverableStatusValue,
): EngagementDeliverable {
  const target = find(engagementId)
  const deliverable = target.deliverables.find((d) => d.id === deliverableId)
  if (!deliverable) throw new Error(`Deliverable ${deliverableId} not found`)
  const now = new Date().toISOString()
  deliverable.status = status
  if (status === DeliverableStatus.DELIVERED && !deliverable.delivered_at) {
    deliverable.delivered_at = now
  }
  target.updated_at = now
  return deliverable
}

export function fixtureCreateTimeEntry(
  engagementId: string,
  input: HoursLogCreate,
): EngagementTimeEntry {
  const target = find(engagementId)
  const entry: EngagementTimeEntry = {
    id: `te-${Math.random().toString(36).slice(2, 8)}`,
    user_id: input.user_id,
    logged_on: input.logged_on,
    hours: input.hours,
    note: input.note ?? null,
  }
  target.hours_log.push(entry)
  target.updated_at = new Date().toISOString()
  return entry
}

export function fixtureGetSummary(engagementId: string): EngagementSummary {
  const target = find(engagementId)
  const deliverable_mix: Record<string, number> = {}
  for (const d of target.deliverables) {
    deliverable_mix[d.status] = (deliverable_mix[d.status] ?? 0) + 1
  }
  const hours_by_user: Record<string, number> = {}
  for (const entry of target.hours_log) {
    hours_by_user[entry.user_id] = (hours_by_user[entry.user_id] ?? 0) + entry.hours
  }
  return {
    engagement_id: target.id,
    client_id: target.client_id,
    name: target.name,
    status: target.status,
    deliverable_count: target.deliverables.length,
    deliverable_mix,
    total_hours: target.hours_log.reduce((total, entry) => total + entry.hours, 0),
    hours_by_user,
    period_start: target.period_start,
    period_end: target.period_end,
    generated_at: new Date().toISOString(),
  }
}
