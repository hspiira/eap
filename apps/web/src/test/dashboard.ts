/**
 * Test-only builder for a dashboard aggregate response.
 *
 * The dashboard has no fixture path: every figure it shows is a count the API
 * computed, so sample data lives here rather than shipping in the bundle.
 */

import type { DashboardResponse } from "@/api/generated"

export function makeDashboard(overrides: Partial<DashboardResponse> = {}): DashboardResponse {
  return {
    range: {
      preset: "last_90d",
      start: "2026-06-09T00:00:00Z",
      end: "2026-09-07T00:00:00Z",
      prior_start: "2026-03-11T00:00:00Z",
      prior_end: "2026-06-09T00:00:00Z",
      granularity: "week",
    },
    session_years: [2026, 2025, 2024],
    kpis: {
      sessions: 41,
      sessions_prior: 43,
      clients_served: 13,
      covered_members: 3303,
      clients_with_roster: 5,
      clients_total: 43,
      import_backlog: 7103,
    },
    sessions_series: [
      { bucket: "2026-06-08", label: "8 Jun", physical: 1, online: 0, unknown: 0, total: 1 },
      { bucket: "2026-06-15", label: "15 Jun", physical: 3, online: 2, unknown: 0, total: 5 },
      { bucket: "2026-06-22", label: "22 Jun", physical: 3, online: 4, unknown: 0, total: 7 },
    ],
    sessions_by_category: [
      { category: "Group", total: 32 },
      { category: "Individual", total: 7 },
      { category: "Family", total: 1 },
      { category: "Couples", total: 1 },
    ],
    top_clients: [
      { client_id: "cl-1", client_name: "Stanbic Bank", total: 10 },
      { client_id: "cl-2", client_name: "Vivo Energy", total: 8 },
      { client_id: "cl-3", client_name: "KCB Bank", total: 7 },
    ],
    trending_services: [
      {
        service_id: "sv-1",
        service_name: "Group Counselling",
        total: 13,
        prior_total: 6,
        change_pct: 116.7,
      },
      {
        service_id: "sv-2",
        service_name: "Health Talk",
        total: 10,
        prior_total: 15,
        change_pct: -33.3,
      },
      {
        service_id: "sv-3",
        service_name: "Mental Health Talk",
        total: 5,
        prior_total: 0,
        change_pct: null,
      },
    ],
    data_quality: {
      sessions_missing_outcome: 186,
      sessions_missing_rate: 161,
      clients_without_roster: 38,
      providers_pending: 112,
      sessions_awaiting_confirmation: 24,
    },
    ...overrides,
  }
}
