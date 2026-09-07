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
} from "lucide-react"

import type { DashboardResponse } from "@/api/generated"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"

import { CardBar, CardStat } from "./CardBar"

type Severity = "high" | "medium" | "low"

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
}

const SEVERITY_STYLE: Record<Severity, string> = {
  high: "bg-danger-soft text-danger-fg ring-danger/20",
  medium: "bg-warning-soft text-warning-fg ring-warning/20",
  low: "bg-info-soft text-info-fg ring-info/20",
}

const SEVERITY_RANK: Record<Severity, number> = { high: 0, medium: 1, low: 2 }

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

  items.sort((a, b) => SEVERITY_RANK[a.severity] - SEVERITY_RANK[b.severity] || b.size - a.size)
  return items.map(({ size: _size, ...item }) => item)
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
    <Card className="rounded-md">
      <CardBar title="Needs attention">
        {!loading && items.length > 0 ? (
          <CardStat value={`${high}`} label="blocking" />
        ) : null}
      </CardBar>
      <CardContent className="p-0">
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
      <span className="flex shrink-0 items-center gap-1 text-xs font-medium text-fg-muted group-hover:text-primary">
        {item.action}
        <ArrowRight className="size-3.5" />
      </span>
    </Link>
  )
}
