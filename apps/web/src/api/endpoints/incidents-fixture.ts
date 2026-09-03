/**
 * In-memory store for incidents (CISM v1). Replaced by a real BE endpoint when
 * BE Phase 2 #5 ships.
 *
 * Mutating helpers below patch the store in place so the FE can exercise create/list/get
 * + timeline append flows end-to-end during dev.
 */

import type { Incident, IncidentTimelineEvent } from '@/types/entities'
import { IncidentSeverity, IncidentStatus, IncidentTimelineEventKind } from '@/types/enums'

const SEED: Incident[] = [
  {
    id: 'inc-001',
    tenant_id: 'tenant-fixture',
    client_id: 'fixture-stanbic',
    title: 'Workplace fatality — Branch 14',
    description:
      'Long-tenured employee passed away suddenly on-site. Counsellor support requested for the immediate team and adjacent branches.',
    severity: IncidentSeverity.CRITICAL,
    status: IncidentStatus.IN_PROGRESS,
    occurred_at: '2026-04-22T08:30:00Z',
    affected_population: 38,
    linked_session_ids: ['sess-pl-1', 'sess-pl-2'],
    resolution_notes: null,
    created_at: '2026-04-22T09:00:00Z',
    updated_at: '2026-04-25T10:00:00Z',
  },
  {
    id: 'inc-002',
    tenant_id: 'tenant-fixture',
    client_id: 'fixture-absa',
    title: 'Robbery — main branch lobby',
    description: 'Armed robbery during business hours; no injuries. Tellers and security visibly affected.',
    severity: IncidentSeverity.HIGH,
    status: IncidentStatus.RESOLVED,
    occurred_at: '2026-03-12T14:05:00Z',
    affected_population: 14,
    linked_session_ids: ['sess-rb-1'],
    resolution_notes: 'After-action distributed; HR follow-up scheduled at 30 days.',
    created_at: '2026-03-12T15:00:00Z',
    updated_at: '2026-03-22T12:00:00Z',
  },
]

const TIMELINE_SEED: IncidentTimelineEvent[] = [
  {
    id: 'tl-001-1',
    incident_id: 'inc-001',
    kind: IncidentTimelineEventKind.CREATED,
    at: '2026-04-22T09:00:00Z',
    actor: 'Helen Mwangi',
    message: 'Incident logged from BCM hotline call.',
  },
  {
    id: 'tl-001-2',
    incident_id: 'inc-001',
    kind: IncidentTimelineEventKind.TRIAGE,
    at: '2026-04-22T09:35:00Z',
    actor: 'Helen Mwangi',
    message: 'Severity set to CRITICAL. Three counsellors mobilised; first session same day.',
  },
  {
    id: 'tl-001-3',
    incident_id: 'inc-001',
    kind: IncidentTimelineEventKind.SESSION_LINKED,
    at: '2026-04-22T15:00:00Z',
    actor: 'System',
    message: 'Group debrief session scheduled.',
    session_id: 'sess-pl-1',
  },
  {
    id: 'tl-001-4',
    incident_id: 'inc-001',
    kind: IncidentTimelineEventKind.SESSION_LINKED,
    at: '2026-04-24T11:00:00Z',
    actor: 'System',
    message: 'Follow-up 1:1 sessions booked for high-impact attendees.',
    session_id: 'sess-pl-2',
  },
  {
    id: 'tl-002-1',
    incident_id: 'inc-002',
    kind: IncidentTimelineEventKind.CREATED,
    at: '2026-03-12T15:00:00Z',
    actor: 'Helen Mwangi',
    message: 'Incident logged after security ops call.',
  },
  {
    id: 'tl-002-2',
    incident_id: 'inc-002',
    kind: IncidentTimelineEventKind.SESSION_LINKED,
    at: '2026-03-13T10:30:00Z',
    actor: 'System',
    message: 'On-site debrief scheduled with branch staff.',
    session_id: 'sess-rb-1',
  },
  {
    id: 'tl-002-3',
    incident_id: 'inc-002',
    kind: IncidentTimelineEventKind.AFTER_ACTION,
    at: '2026-03-22T11:30:00Z',
    actor: 'Helen Mwangi',
    message: 'After-action report shared with HR + facilities.',
  },
  {
    id: 'tl-002-4',
    incident_id: 'inc-002',
    kind: IncidentTimelineEventKind.RESOLVED,
    at: '2026-03-22T12:00:00Z',
    actor: 'Helen Mwangi',
    message: 'Incident closed; 30-day HR follow-up booked.',
  },
]

const incidentStore: Incident[] = [...SEED]
const timelineStore: IncidentTimelineEvent[] = [...TIMELINE_SEED]

export function fixtureGetAll(): Incident[] {
  return [...incidentStore].sort((a, b) =>
    a.occurred_at < b.occurred_at ? 1 : a.occurred_at > b.occurred_at ? -1 : 0,
  )
}

export function fixtureGetById(id: string): Incident | undefined {
  return incidentStore.find((i) => i.id === id)
}

export function fixtureGetTimeline(incidentId: string): IncidentTimelineEvent[] {
  return timelineStore
    .filter((e) => e.incident_id === incidentId)
    .sort((a, b) => (a.at < b.at ? -1 : a.at > b.at ? 1 : 0))
}

export function fixtureCreate(
  data: Omit<Incident, 'id' | 'created_at' | 'updated_at' | 'tenant_id' | 'status' | 'linked_session_ids'>,
): Incident {
  const now = new Date().toISOString()
  const incident: Incident = {
    ...data,
    id: `inc-${Math.random().toString(36).slice(2, 8)}`,
    tenant_id: 'tenant-fixture',
    status: IncidentStatus.OPEN,
    linked_session_ids: [],
    created_at: now,
    updated_at: now,
  }
  incidentStore.unshift(incident)
  timelineStore.push({
    id: `tl-${incident.id}-1`,
    incident_id: incident.id,
    kind: IncidentTimelineEventKind.CREATED,
    at: now,
    actor: 'Current user',
    message: 'Incident logged.',
  })
  return incident
}

export function fixtureAppendNote(
  incidentId: string,
  message: string,
  actor = 'Current user',
): IncidentTimelineEvent {
  const event: IncidentTimelineEvent = {
    id: `tl-${incidentId}-${timelineStore.length + 1}`,
    incident_id: incidentId,
    kind: IncidentTimelineEventKind.NOTE,
    at: new Date().toISOString(),
    actor,
    message,
  }
  timelineStore.push(event)
  const incident = incidentStore.find((i) => i.id === incidentId)
  if (incident) incident.updated_at = event.at
  return event
}
