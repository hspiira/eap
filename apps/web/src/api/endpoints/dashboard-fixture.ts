/**
 * DEV fixture for the dashboard aggregate. Shaped like the staging tenant:
 * a historical session import with a large unresolved-member queue, most
 * practitioners still pending, and rosters loaded for only a few clients.
 *
 * The fixture honours the requested range so the window control can be
 * exercised without a backend: it re-buckets and scales with the window the
 * same way the API does.
 */

import type { DashboardResponse, SeriesPoint } from "@/api/generated"
import type { DashboardRange } from "@/lib/dashboard"

const MONTH_NAMES = [
  "Jan",
  "Feb",
  "Mar",
  "Apr",
  "May",
  "Jun",
  "Jul",
  "Aug",
  "Sep",
  "Oct",
  "Nov",
  "Dec",
]

const RANGE_DAYS: Record<string, number> = {
  this_week: 7,
  this_month: 30,
  last_30d: 30,
  last_90d: 90,
  last_180d: 180,
  custom: 60,
}

/** Deterministic pseudo-random so a re-render does not reshuffle the chart. */
function noise(seed: number): number {
  return (Math.sin(seed * 12.9898) * 43758.5453) % 1
}

function granularityFor(days: number): "day" | "week" | "month" {
  if (days <= 31) return "day"
  if (days <= 120) return "week"
  return "month"
}

function bucketCount(days: number, granularity: string): number {
  if (granularity === "day") return days
  if (granularity === "week") return Math.ceil(days / 7)
  return Math.ceil(days / 30)
}

function bucketAt(offsetFromEnd: number, granularity: string): { key: string; label: string } {
  const d = new Date()
  if (granularity === "month") {
    d.setDate(1)
    d.setMonth(d.getMonth() - offsetFromEnd)
    const key = `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`
    return { key, label: `${MONTH_NAMES[d.getMonth()]} ${d.getFullYear()}` }
  }
  d.setDate(d.getDate() - offsetFromEnd * (granularity === "week" ? 7 : 1))
  const key = d.toISOString().slice(0, 10)
  return { key, label: `${d.getDate()} ${MONTH_NAMES[d.getMonth()]}` }
}

function fixtureSeries(days: number): SeriesPoint[] {
  const granularity = granularityFor(days)
  const count = bucketCount(days, granularity)
  const scale = granularity === "day" ? 1 : granularity === "week" ? 4 : 18
  const points: SeriesPoint[] = []
  for (let i = count - 1; i >= 0; i--) {
    const { key, label } = bucketAt(i, granularity)
    const wobble = Math.abs(noise(i + count))
    const physical = Math.round(scale * (0.5 + wobble))
    const online = Math.round(scale * 0.4 * (0.4 + Math.abs(noise(i * 3))))
    const unknown = i % 5 === 0 ? Math.round(scale * 0.15) : 0
    points.push({
      bucket: key,
      label,
      physical,
      online,
      unknown,
      total: physical + online + unknown,
    })
  }
  return points
}

/**
 * Split a total across weights so the parts sum to exactly the total. The
 * groupings on the page are subsets of the same sessions, so a fixture whose
 * parts outran the whole would teach an invariant the API never produces.
 */
function apportion(total: number, weights: number[]): number[] {
  const sum = weights.reduce((a, b) => a + b, 0)
  const exact = weights.map((w) => (w / sum) * total)
  const parts = exact.map((v) => Math.floor(v))
  let remainder = total - parts.reduce((a, b) => a + b, 0)
  const order = exact
    .map((v, i) => ({ i, frac: v - Math.floor(v) }))
    .sort((a, b) => b.frac - a.frac)
  for (const { i } of order) {
    if (remainder <= 0) break
    parts[i] += 1
    remainder -= 1
  }
  return parts
}

const CATEGORY_NAMES = ["Group", "Family", "Individual", "Couples"]
const CLIENT_NAMES = ["Vivo Energy", "Stanbic Bank", "KCB Bank", "Absa", "I&M Bank"]
const SERVICE_NAMES = [
  "Group Counselling",
  "Health Talk",
  "Physical Wellness",
  "Mental Health Talk",
  "Individual Counselling",
  "Family Therapy",
]
const SERVICE_CHANGE = [116.7, -33.3, -40, 150, 200, -75]

export function fixtureDashboard(range: DashboardRange): DashboardResponse {
  const days = RANGE_DAYS[range.preset] ?? 90
  const series = fixtureSeries(days)
  const sessions = series.reduce((sum, p) => sum + p.total, 0)
  const now = new Date()
  const start = new Date(now.getTime() - days * 86_400_000)

  // Every grouping is a view of the same sessions, so all three are shares of
  // the window total rather than independently scaled figures.
  const categoryTotals = apportion(sessions, [127, 20, 9, 3])
  // The top five never account for the whole tenant; the tail is other clients.
  const clientTotals = apportion(Math.round(sessions * 0.72), [40, 20, 16, 13, 10])
  const serviceTotals = apportion(sessions, [13, 10, 9, 5, 3, 1])

  return {
    range: {
      preset: range.preset,
      start: start.toISOString(),
      end: now.toISOString(),
      prior_start: new Date(start.getTime() - days * 86_400_000).toISOString(),
      granularity: granularityFor(days),
    },
    kpis: {
      sessions,
      sessions_prior: Math.round(sessions * 1.08),
      clients_served: Math.min(13, Math.max(1, Math.round((13 * days) / 90))),
      covered_members: 3303,
      clients_with_roster: 5,
      clients_total: 43,
      import_backlog: 7103,
    },
    sessions_series: series,
    sessions_by_category: CATEGORY_NAMES.map((category, i) => ({
      category,
      total: categoryTotals[i],
    })),
    top_clients: CLIENT_NAMES.map((client_name, i) => ({
      client_id: `fx-cl-${i + 1}`,
      client_name,
      total: clientTotals[i],
    })),
    trending_services: SERVICE_NAMES.map((service_name, i) => ({
      service_id: `fx-sv-${i + 1}`,
      service_name,
      total: serviceTotals[i],
      prior_total: Math.round(serviceTotals[i] / (1 + SERVICE_CHANGE[i] / 100)),
      change_pct: SERVICE_CHANGE[i],
    })),
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
      duplicate: 85,
      blocked: 7103,
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
