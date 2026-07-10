/**
 * In-memory store for consultancy engagements (Phase 4 #1).
 *
 * Tracks engagement, deliverables, time entries, and a derived timeline. Hours roll
 * up from time entries on every mutation; deliverable status transitions emit
 * timeline events. Replaced by BE Phase 4 #1 endpoints.
 */

import type {
  Engagement,
  EngagementDeliverable,
  EngagementTimeEntry,
  EngagementTimelineEvent,
} from '@/types/entities'
import {
  DeliverableStatus,
  EngagementStatus,
  EngagementTimelineEventKind,
  EngagementType,
} from '@/types/enums'

const TENANT = 'tenant-fixture'

const ENGAGEMENT_SEED: Engagement[] = [
  {
    id: 'eng-001',
    tenant_id: TENANT,
    client_id: 'fixture-stanbic',
    name: 'Mental health policy refresh',
    description:
      '2026 mental-health policy redraft incorporating WIBA/ARA changes and new EAP scope.',
    status: EngagementStatus.ACTIVE,
    engagement_type: EngagementType.POLICY_DRAFT,
    start_date: '2026-04-01',
    due_date: '2026-06-15',
    closed_at: null,
    hourly_rate: 180,
    currency: 'USD',
    budget_hours: 60,
    hours_logged: 18,
    lead_user_id: 'user-helen',
    created_at: '2026-03-25T10:00:00Z',
    updated_at: '2026-05-06T16:00:00Z',
  },
  {
    id: 'eng-002',
    tenant_id: TENANT,
    client_id: 'fixture-absa',
    name: 'Manager mental-health training — Q2',
    description: 'Two cohorts × half-day workshop. Includes pre/post evaluation.',
    status: EngagementStatus.SCOPING,
    engagement_type: EngagementType.TRAINING,
    start_date: '2026-05-20',
    due_date: '2026-07-10',
    closed_at: null,
    hourly_rate: 150,
    currency: 'USD',
    budget_hours: 24,
    hours_logged: 0,
    lead_user_id: 'user-mary',
    created_at: '2026-05-04T09:30:00Z',
    updated_at: '2026-05-04T09:30:00Z',
  },
  {
    id: 'eng-003',
    tenant_id: TENANT,
    client_id: 'fixture-stanbic',
    name: 'Wellness audit — branch network',
    description: 'On-site assessment + report covering 12 priority branches.',
    status: EngagementStatus.DELIVERED,
    engagement_type: EngagementType.AUDIT,
    start_date: '2026-01-15',
    due_date: '2026-03-31',
    closed_at: null,
    hourly_rate: 200,
    currency: 'USD',
    budget_hours: 40,
    hours_logged: 38,
    lead_user_id: 'user-helen',
    created_at: '2026-01-10T11:00:00Z',
    updated_at: '2026-04-02T15:00:00Z',
  },
]

const DELIVERABLE_SEED: EngagementDeliverable[] = [
  {
    id: 'dlv-001',
    engagement_id: 'eng-001',
    title: 'Stakeholder interview pack',
    description: 'Summary of interviews with HR, ops, and legal.',
    status: DeliverableStatus.ACCEPTED,
    due_date: '2026-04-15',
    submitted_at: '2026-04-14T09:00:00Z',
    accepted_at: '2026-04-16T11:00:00Z',
    artefact_url: null,
    created_at: '2026-04-01T10:00:00Z',
    updated_at: '2026-04-16T11:00:00Z',
  },
  {
    id: 'dlv-002',
    engagement_id: 'eng-001',
    title: 'Policy draft v1',
    description: 'Initial policy draft for legal review.',
    status: DeliverableStatus.IN_PROGRESS,
    due_date: '2026-05-20',
    submitted_at: null,
    accepted_at: null,
    artefact_url: null,
    created_at: '2026-04-16T11:00:00Z',
    updated_at: '2026-05-06T16:00:00Z',
  },
  {
    id: 'dlv-003',
    engagement_id: 'eng-003',
    title: 'Branch audit report',
    description: 'Findings + recommendations for the 12 priority branches.',
    status: DeliverableStatus.SUBMITTED,
    due_date: '2026-03-31',
    submitted_at: '2026-04-01T16:00:00Z',
    accepted_at: null,
    artefact_url: null,
    created_at: '2026-01-15T10:00:00Z',
    updated_at: '2026-04-01T16:00:00Z',
  },
]

const TIME_ENTRY_SEED: EngagementTimeEntry[] = [
  {
    id: 'te-001',
    engagement_id: 'eng-001',
    user_id: 'user-helen',
    occurred_on: '2026-04-02',
    hours: 4,
    description: 'Stakeholder interviews — HR + ops.',
    deliverable_id: 'dlv-001',
    created_at: '2026-04-02T18:00:00Z',
  },
  {
    id: 'te-002',
    engagement_id: 'eng-001',
    user_id: 'user-helen',
    occurred_on: '2026-04-08',
    hours: 6,
    description: 'Interview synthesis + memo draft.',
    deliverable_id: 'dlv-001',
    created_at: '2026-04-08T18:00:00Z',
  },
  {
    id: 'te-003',
    engagement_id: 'eng-001',
    user_id: 'user-helen',
    occurred_on: '2026-04-29',
    hours: 8,
    description: 'Policy draft outline.',
    deliverable_id: 'dlv-002',
    created_at: '2026-04-29T18:00:00Z',
  },
  {
    id: 'te-004',
    engagement_id: 'eng-003',
    user_id: 'user-helen',
    occurred_on: '2026-03-10',
    hours: 24,
    description: 'On-site visits — 8 branches.',
    deliverable_id: 'dlv-003',
    created_at: '2026-03-10T18:00:00Z',
  },
  {
    id: 'te-005',
    engagement_id: 'eng-003',
    user_id: 'user-mary',
    occurred_on: '2026-03-25',
    hours: 14,
    description: 'Findings synthesis + report draft.',
    deliverable_id: 'dlv-003',
    created_at: '2026-03-25T18:00:00Z',
  },
]

const TIMELINE_SEED: EngagementTimelineEvent[] = [
  {
    id: 'tl-eng-001-1',
    engagement_id: 'eng-001',
    kind: EngagementTimelineEventKind.CREATED,
    at: '2026-03-25T10:00:00Z',
    actor: 'Helen Mwangi',
    message: 'Engagement created from policy refresh request.',
  },
  {
    id: 'tl-eng-001-2',
    engagement_id: 'eng-001',
    kind: EngagementTimelineEventKind.STATUS_CHANGED,
    at: '2026-04-01T09:00:00Z',
    actor: 'Helen Mwangi',
    message: 'Status: Scoping → Active.',
  },
  {
    id: 'tl-eng-001-3',
    engagement_id: 'eng-001',
    kind: EngagementTimelineEventKind.DELIVERABLE_ADDED,
    at: '2026-04-01T10:00:00Z',
    actor: 'Helen Mwangi',
    message: 'Deliverable added: Stakeholder interview pack.',
    deliverable_id: 'dlv-001',
  },
  {
    id: 'tl-eng-001-4',
    engagement_id: 'eng-001',
    kind: EngagementTimelineEventKind.DELIVERABLE_UPDATED,
    at: '2026-04-16T11:00:00Z',
    actor: 'Helen Mwangi',
    message: 'Deliverable accepted: Stakeholder interview pack.',
    deliverable_id: 'dlv-001',
  },
]

const engagementStore: Engagement[] = [...ENGAGEMENT_SEED]
const deliverableStore: EngagementDeliverable[] = [...DELIVERABLE_SEED]
const timeStore: EngagementTimeEntry[] = [...TIME_ENTRY_SEED]
const timelineStore: EngagementTimelineEvent[] = [...TIMELINE_SEED]

export interface EngagementCreateInput {
  client_id: string
  name: string
  description?: string | null
  engagement_type: EngagementType
  start_date: string
  due_date?: string | null
  hourly_rate?: number | null
  currency?: string | null
  budget_hours?: number | null
  lead_user_id?: string | null
}

export interface DeliverableCreateInput {
  engagement_id: string
  title: string
  description?: string | null
  due_date?: string | null
}

export interface TimeEntryCreateInput {
  engagement_id: string
  user_id: string
  occurred_on: string
  hours: number
  description?: string | null
  deliverable_id?: string | null
}

export function fixtureListEngagements(): Engagement[] {
  return [...engagementStore].sort((a, b) =>
    a.created_at < b.created_at ? 1 : a.created_at > b.created_at ? -1 : 0,
  )
}

export function fixtureGetEngagement(id: string): Engagement | undefined {
  return engagementStore.find((e) => e.id === id)
}

export function fixtureCreateEngagement(input: EngagementCreateInput): Engagement {
  const now = new Date().toISOString()
  const engagement: Engagement = {
    id: `eng-${Math.random().toString(36).slice(2, 8)}`,
    tenant_id: TENANT,
    status: EngagementStatus.SCOPING,
    closed_at: null,
    hours_logged: 0,
    description: input.description ?? null,
    due_date: input.due_date ?? null,
    hourly_rate: input.hourly_rate ?? null,
    currency: input.currency ?? null,
    budget_hours: input.budget_hours ?? null,
    lead_user_id: input.lead_user_id ?? null,
    created_at: now,
    updated_at: now,
    ...input,
  }
  engagementStore.unshift(engagement)
  timelineStore.push({
    id: `tl-${engagement.id}-1`,
    engagement_id: engagement.id,
    kind: EngagementTimelineEventKind.CREATED,
    at: now,
    actor: 'Current user',
    message: 'Engagement created.',
  })
  return engagement
}

const ALLOWED_TRANSITIONS: Record<EngagementStatus, EngagementStatus[]> = {
  [EngagementStatus.SCOPING]: [EngagementStatus.ACTIVE, EngagementStatus.CANCELLED],
  [EngagementStatus.ACTIVE]: [EngagementStatus.DELIVERED, EngagementStatus.CANCELLED],
  [EngagementStatus.DELIVERED]: [EngagementStatus.CLOSED, EngagementStatus.ACTIVE],
  [EngagementStatus.CLOSED]: [],
  [EngagementStatus.CANCELLED]: [],
}

export function fixtureAllowedTransitions(from: EngagementStatus): EngagementStatus[] {
  return ALLOWED_TRANSITIONS[from] ?? []
}

export function fixtureTransitionEngagement(
  id: string,
  to: EngagementStatus,
  actor = 'Current user',
): Engagement {
  const target = engagementStore.find((e) => e.id === id)
  if (!target) throw new Error(`Engagement ${id} not found`)
  const allowed = ALLOWED_TRANSITIONS[target.status] ?? []
  if (!allowed.includes(to)) {
    throw new Error(`Cannot transition ${target.status} → ${to}`)
  }
  const from = target.status
  const now = new Date().toISOString()
  target.status = to
  target.updated_at = now
  if (to === EngagementStatus.CLOSED) target.closed_at = now
  timelineStore.push({
    id: `tl-${id}-${timelineStore.length + 1}`,
    engagement_id: id,
    kind: EngagementTimelineEventKind.STATUS_CHANGED,
    at: now,
    actor,
    message: `Status: ${from} → ${to}.`,
  })
  return target
}

export function fixtureListDeliverables(engagementId: string): EngagementDeliverable[] {
  return deliverableStore
    .filter((d) => d.engagement_id === engagementId)
    .sort((a, b) => (a.created_at < b.created_at ? -1 : 1))
}

export function fixtureCreateDeliverable(input: DeliverableCreateInput): EngagementDeliverable {
  const now = new Date().toISOString()
  const deliverable: EngagementDeliverable = {
    id: `dlv-${Math.random().toString(36).slice(2, 8)}`,
    engagement_id: input.engagement_id,
    title: input.title,
    description: input.description ?? null,
    status: DeliverableStatus.PENDING,
    due_date: input.due_date ?? null,
    submitted_at: null,
    accepted_at: null,
    artefact_url: null,
    created_at: now,
    updated_at: now,
  }
  deliverableStore.push(deliverable)
  timelineStore.push({
    id: `tl-${input.engagement_id}-${timelineStore.length + 1}`,
    engagement_id: input.engagement_id,
    kind: EngagementTimelineEventKind.DELIVERABLE_ADDED,
    at: now,
    actor: 'Current user',
    message: `Deliverable added: ${input.title}.`,
    deliverable_id: deliverable.id,
  })
  return deliverable
}

export function fixtureUpdateDeliverableStatus(
  id: string,
  status: DeliverableStatus,
  actor = 'Current user',
): EngagementDeliverable {
  const target = deliverableStore.find((d) => d.id === id)
  if (!target) throw new Error(`Deliverable ${id} not found`)
  const now = new Date().toISOString()
  target.status = status
  target.updated_at = now
  if (status === DeliverableStatus.SUBMITTED && !target.submitted_at) target.submitted_at = now
  if (status === DeliverableStatus.ACCEPTED && !target.accepted_at) target.accepted_at = now
  timelineStore.push({
    id: `tl-${target.engagement_id}-${timelineStore.length + 1}`,
    engagement_id: target.engagement_id,
    kind: EngagementTimelineEventKind.DELIVERABLE_UPDATED,
    at: now,
    actor,
    message: `Deliverable status: ${target.title} → ${status}.`,
    deliverable_id: target.id,
  })
  return target
}

export function fixtureListTimeEntries(engagementId: string): EngagementTimeEntry[] {
  return timeStore
    .filter((t) => t.engagement_id === engagementId)
    .sort((a, b) => (a.occurred_on < b.occurred_on ? 1 : -1))
}

export function fixtureCreateTimeEntry(input: TimeEntryCreateInput): EngagementTimeEntry {
  const now = new Date().toISOString()
  const entry: EngagementTimeEntry = {
    id: `te-${Math.random().toString(36).slice(2, 8)}`,
    engagement_id: input.engagement_id,
    user_id: input.user_id,
    occurred_on: input.occurred_on,
    hours: input.hours,
    description: input.description ?? null,
    deliverable_id: input.deliverable_id ?? null,
    created_at: now,
  }
  timeStore.push(entry)
  rollupHours(input.engagement_id)
  timelineStore.push({
    id: `tl-${input.engagement_id}-${timelineStore.length + 1}`,
    engagement_id: input.engagement_id,
    kind: EngagementTimelineEventKind.HOURS_LOGGED,
    at: now,
    actor: input.user_id,
    message: `Logged ${input.hours}h on ${input.occurred_on}.`,
  })
  return entry
}

export function fixtureGetTimeline(engagementId: string): EngagementTimelineEvent[] {
  return timelineStore
    .filter((e) => e.engagement_id === engagementId)
    .sort((a, b) => (a.at < b.at ? -1 : 1))
}

function rollupHours(engagementId: string) {
  const target = engagementStore.find((e) => e.id === engagementId)
  if (!target) return
  const total = timeStore
    .filter((t) => t.engagement_id === engagementId)
    .reduce((acc, t) => acc + t.hours, 0)
  target.hours_logged = total
  target.updated_at = new Date().toISOString()
}
