/**
 * The decision panel: what to do next, ranked by what it unblocks.
 *
 * Every row states an action rather than a measurement, and is derived from
 * figures already on the page, so the panel never disagrees with the charts
 * below it. Severity is carried by an icon and the wording as well as colour.
 */

import { Link } from "@tanstack/react-router"
import {
  AlertTriangle,
  ArrowRight,
  CheckCircle2,
  CircleAlert,
  Info,
  type LucideIcon,
  Sparkles,
} from "lucide-react"

import type { DashboardResponse } from "@/api/generated"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"

import { CardBar, CardStat } from "./CardBar"

type Severity = "high" | "medium" | "low" | "signal"

/** Below this a percentage swing is noise, so no signal is raised from it. */
const MIN_PRIOR_FOR_TREND = 3
const MIN_SESSIONS_FOR_SIGNAL = 10
const CONCENTRATION_THRESHOLD = 25
const MOVE_THRESHOLD = 20

export interface AttentionItem {
  key: string
  severity: Severity
  headline: string
  consequence: string
  action: string
  to: string
}

const SEVERITY_ICON: Record<Severity, LucideIcon> = {
  high: CircleAlert,
  medium: AlertTriangle,
  low: Info,
  signal: Sparkles,
}

const SEVERITY_STYLE: Record<Severity, string> = {
  high: "bg-danger-soft text-danger-fg ring-danger/20",
  medium: "bg-warning-soft text-warning-fg ring-warning/20",
  low: "bg-info-soft text-info-fg ring-info/20",
  signal: "bg-muted text-fg-muted ring-border-strong/40",
}

const SEVERITY_RANK: Record<Severity, number> = { high: 0, medium: 1, low: 2, signal: 3 }

/**
 * Turn the aggregate into a ranked action list. Order is by severity first
 * and size second, so the largest queue does not outrank a smaller one that
 * is blocking new bookings outright.
 */
export function buildAttentionItems(data: DashboardResponse): AttentionItem[] {
  const quality = data.data_quality
  const backlog = data.kpis.import_backlog
  const items: (AttentionItem & { size: number })[] = []

  if (quality.clients_without_roster > 0) {
    items.push({
      key: "rosters",
      severity: "high",
      size: quality.clients_without_roster,
      headline: `Import member rosters for ${quality.clients_without_roster} clients`,
      consequence: backlog > 0 ? `unblocks ${backlog.toLocaleString()} import rows` : "",
      action: "Members",
      to: "/members",
    })
  }
  if (quality.sessions_awaiting_confirmation > 0) {
    items.push({
      key: "unconfirmed",
      severity: "high",
      size: quality.sessions_awaiting_confirmation,
      headline: `Confirm ${quality.sessions_awaiting_confirmation.toLocaleString()} past bookings`,
      consequence: "their date has passed and no outcome is recorded",
      action: "Sessions",
      to: "/service-sessions",
    })
  }
  if (quality.providers_pending > 0) {
    items.push({
      key: "practitioners",
      severity: "high",
      size: quality.providers_pending,
      headline: `Activate ${quality.providers_pending} pending practitioners`,
      consequence: "they cannot take new bookings",
      action: "Practitioners",
      to: "/providers",
    })
  }
  if (quality.sessions_missing_rate > 0) {
    items.push({
      key: "rates",
      severity: "medium",
      size: quality.sessions_missing_rate,
      headline: `Add rates to ${quality.sessions_missing_rate} sessions`,
      consequence: "not billable as recorded",
      action: "Sessions",
      to: "/service-sessions",
    })
  }
  if (quality.sessions_missing_outcome > 0) {
    items.push({
      key: "outcomes",
      severity: "low",
      size: quality.sessions_missing_outcome,
      headline: `Record outcomes for ${quality.sessions_missing_outcome} sessions`,
      consequence: "missing from clinical reporting",
      action: "Sessions",
      to: "/service-sessions",
    })
  }

  const signals = buildSignals(data).map((item) => ({ ...item, size: 0 }))
  items.push(...signals)
  items.sort((a, b) => SEVERITY_RANK[a.severity] - SEVERITY_RANK[b.severity] || b.size - a.size)
  return items.map(({ size: _size, ...item }) => item)
}

/**
 * Read the window's analytics for things worth acting on: a client the tenant
 * depends on, and services whose demand has moved. Each rule is guarded on
 * sample size, so a swing between two and six sessions never becomes advice.
 */
function buildSignals(data: DashboardResponse): AttentionItem[] {
  const sessions = data.kpis.sessions
  if (sessions < MIN_SESSIONS_FOR_SIGNAL) return []

  const signals: AttentionItem[] = []
  const leader = data.top_clients[0]
  if (leader) {
    const share = Math.round((leader.total / sessions) * 100)
    if (share >= CONCENTRATION_THRESHOLD) {
      signals.push({
        key: "concentration",
        severity: "signal",
        headline: `${leader.client_name} is ${share}% of delivery`,
        consequence: "revenue concentrated in one client",
        action: "Clients",
        to: "/clients",
      })
    }
  }

  const moved = data.trending_services.filter(
    (service) => service.prior_total >= MIN_PRIOR_FOR_TREND && service.change_pct !== null,
  )
  const riser = maxBy(moved, (service) => service.change_pct ?? 0)
  if (riser && (riser.change_pct ?? 0) >= MOVE_THRESHOLD) {
    signals.push({
      key: "riser",
      severity: "signal",
      headline: `${riser.service_name} demand up ${Math.round(riser.change_pct ?? 0)}%`,
      consequence: "check practitioner capacity",
      action: "Services",
      to: "/services",
    })
  }
  const faller = maxBy(moved, (service) => -(service.change_pct ?? 0))
  if (faller && (faller.change_pct ?? 0) <= -MOVE_THRESHOLD) {
    signals.push({
      key: "faller",
      severity: "signal",
      headline: `${faller.service_name} demand down ${Math.abs(Math.round(faller.change_pct ?? 0))}%`,
      consequence: "demand shifting to other services",
      action: "Services",
      to: "/services",
    })
  }
  return signals
}

function maxBy<T>(items: ReadonlyArray<T>, score: (item: T) => number): T | undefined {
  return items.reduce<T | undefined>(
    (best, item) => (best === undefined || score(item) > score(best) ? item : best),
    undefined,
  )
}

export function AttentionCard({
  items,
  loading,
}: {
  items: ReadonlyArray<AttentionItem>
  loading?: boolean
}) {
  const high = items.filter((item) => item.severity === "high").length
  return (
    <Card className="flex h-full flex-col rounded-md">
      <CardBar title="Needs attention">
        {!loading && high > 0 ? <CardStat value={`${high}`} label="blocking" /> : null}
      </CardBar>
      <CardContent className="max-h-[220px] flex-1 overflow-y-auto p-0">
        {loading ? (
          <div className="grid gap-2 p-3">
            <Skeleton className="h-9 w-full" />
            <Skeleton className="h-9 w-full" />
          </div>
        ) : items.length === 0 ? (
          <div className="flex items-center gap-2 p-4">
            <CheckCircle2 className="size-4 shrink-0 text-success-fg" aria-hidden />
            <p className="text-sm text-fg-muted">Nothing is blocked.</p>
          </div>
        ) : (
          <ul>
            {items.map((item, i) => (
              <li key={item.key} className={i > 0 ? "border-t border-border-subtle" : undefined}>
                <AttentionRow item={item} />
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}

function AttentionRow({ item }: { item: AttentionItem }) {
  const Icon = SEVERITY_ICON[item.severity]
  return (
    <Link
      to={item.to}
      className="group flex items-center gap-3 p-3 transition-colors hover:bg-surface-hover focus-visible:bg-surface-hover focus-visible:outline-none"
    >
      <span
        className={cn(
          "flex size-7 shrink-0 items-center justify-center rounded-md ring-1",
          SEVERITY_STYLE[item.severity],
        )}
        aria-hidden
      >
        <Icon className="size-3.5" />
      </span>
      <span className="flex min-w-0 flex-1 flex-wrap items-baseline gap-x-2">
        <span className="text-sm font-medium text-fg">{item.headline}</span>
        {item.consequence ? (
          <span className="text-xs text-fg-muted">{item.consequence}</span>
        ) : null}
      </span>
      <span className="flex shrink-0 items-center gap-1 text-xs font-medium text-fg-muted group-hover:underline">
        {item.action}
        <ArrowRight className="size-3.5" />
      </span>
    </Link>
  )
}
