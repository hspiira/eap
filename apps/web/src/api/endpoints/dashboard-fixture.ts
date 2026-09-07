/**
 * DEV fixture for the dashboard aggregate. Shaped like the staging tenant:
 * a historical session import with a large unresolved-member queue, most
 * practitioners still pending, and rosters loaded for only a few clients.
 */

import type { DashboardResponse, MonthlySessions } from "@/api/generated"

const MONTHLY_TOTALS = [20, 12, 11, 5, 18, 16, 13, 17, 20, 15, 12, 9]

function monthKey(offset: number): string {
  const d = new Date()
  d.setDate(1)
  d.setMonth(d.getMonth() - offset)
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`
}

function fixtureMonthly(): MonthlySessions[] {
  return MONTHLY_TOTALS.map((total, i) => ({
    month: monthKey(MONTHLY_TOTALS.length - 1 - i),
    total,
  }))
}

export function fixtureDashboard(): DashboardResponse {
  return {
    kpis: {
      sessions_90d: 41,
      sessions_prior_90d: 43,
      clients_served_90d: 13,
      covered_members: 3303,
      clients_with_roster: 5,
      clients_total: 43,
      import_backlog: 7103,
    },
    sessions_monthly: fixtureMonthly(),
    sessions_by_category: [
      { category: "Group", total: 127 },
      { category: "Family", total: 20 },
      { category: "Individual", total: 9 },
      { category: "Couples", total: 3 },
    ],
    top_clients: [
      { client_id: "fx-cl-1", client_name: "Vivo Energy", total: 40 },
      { client_id: "fx-cl-2", client_name: "Stanbic Bank", total: 20 },
      { client_id: "fx-cl-3", client_name: "KCB Bank", total: 16 },
      { client_id: "fx-cl-4", client_name: "Absa", total: 13 },
      { client_id: "fx-cl-5", client_name: "I&M Bank", total: 10 },
      { client_id: "fx-cl-6", client_name: "Epicenter", total: 9 },
      { client_id: "fx-cl-7", client_name: "Diamond Trust Bank", total: 8 },
      { client_id: "fx-cl-8", client_name: "NCBA Bank Uganda", total: 7 },
    ],
    import_queues: [
      { outcome: "UnresolvedMember", total: 6444 },
      { outcome: "MissingPractitioner", total: 637 },
      { outcome: "UnresolvedService", total: 14 },
      { outcome: "UnresolvedClient", total: 6 },
      { outcome: "UnmappedPractitioner", total: 2 },
    ],
    import_batch: {
      file_name: "sessions.csv",
      status: "Applied",
      row_count: 7471,
      accepted: 283,
      applied_at: new Date().toISOString(),
    },
    data_quality: {
      sessions_missing_outcome: 186,
      sessions_missing_rate: 161,
      clients_without_roster: 38,
      providers_pending: 112,
    },
  }
}
