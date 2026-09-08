/**
 * Which services are in demand, and which way they are moving.
 *
 * Each row pairs the window's count with its change against the equal-length
 * window before it. A service with no prior sessions shows "new" rather than
 * a percentage, because a rise from zero has no percentage to state.
 */

import { Minus, TrendingDown, TrendingUp } from "lucide-react"

import type { ServiceTrend } from "@/api/generated"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"
import { cn } from "@/lib/utils"

import { CardBar, CardStat } from "./CardBar"

interface TrendingServicesCardProps {
  services: ReadonlyArray<ServiceTrend>
  loading?: boolean
}

export function TrendingServicesCard({ services, loading }: TrendingServicesCardProps) {
  const rising = services.filter((s) => (s.change_pct ?? 0) > 0).length
  return (
    <Card className="flex h-full flex-col rounded-md">
      <CardBar title="Services in demand">
        {services.length > 0 ? <CardStat value={`${rising}`} label="rising" /> : null}
      </CardBar>
      <CardContent className="flex-1 p-0">
        {loading ? (
          <div className="p-3">
            <Skeleton className="h-32 w-full" />
          </div>
        ) : services.length === 0 ? (
          <p className="p-6 text-center text-sm text-fg-muted">No services used in this window.</p>
        ) : (
          <ul>
            {services.map((service, i) => (
              <li
                key={service.service_id}
                className={i > 0 ? "border-t border-border-subtle" : undefined}
              >
                <ServiceRow service={service} />
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}

function ServiceRow({ service }: { service: ServiceTrend }) {
  return (
    <div className="flex items-center gap-2 px-3 py-2.5">
      <span className="min-w-0 flex-1 truncate text-sm text-fg" title={service.service_name}>
        {service.service_name}
      </span>
      <span className="text-sm font-medium tabular-nums text-fg">
        {service.total.toLocaleString()}
      </span>
      <ChangeChip service={service} />
    </div>
  )
}

function ChangeChip({ service }: { service: ServiceTrend }) {
  if (service.change_pct === null || service.change_pct === undefined) {
    return (
      <span className="w-14 shrink-0 rounded-sm bg-muted px-1.5 py-0.5 text-right text-xs font-medium text-fg-muted">
        new
      </span>
    )
  }
  const rising = service.change_pct > 0
  const flat = service.change_pct === 0
  const Icon = flat ? Minus : rising ? TrendingUp : TrendingDown
  return (
    <span
      className={cn(
        "inline-flex w-14 shrink-0 items-center justify-end gap-0.5 rounded-sm px-1.5 py-0.5 text-xs font-medium tabular-nums",
        flat
          ? "bg-muted text-fg-muted"
          : rising
            ? "bg-success-soft text-success-fg"
            : "bg-danger-soft text-danger-fg",
      )}
      title={`${service.prior_total} in the previous period`}
    >
      <Icon className="size-3" aria-hidden />
      {Math.abs(Math.round(service.change_pct))}%
    </span>
  )
}
