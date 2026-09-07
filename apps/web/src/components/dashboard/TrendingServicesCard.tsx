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
    <Card className="rounded-md">
      <CardBar title="Services in demand">
        {services.length > 0 ? <CardStat value={`${rising}`} label="rising" /> : null}
      </CardBar>
      <CardContent className="p-0">
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
                <ServiceRow service={service} max={services[0].total} />
              </li>
            ))}
          </ul>
        )}
      </CardContent>
    </Card>
  )
}

function ServiceRow({ service, max }: { service: ServiceTrend; max: number }) {
  return (
    <div className="grid grid-cols-[1fr_2.5rem_4rem] items-center gap-3 px-3 py-2">
      <div className="grid min-w-0 gap-1">
        <span className="truncate text-sm text-fg">{service.service_name}</span>
        <span className="h-1 rounded-full bg-chart-3/10">
          <span
            className="block h-full rounded-full bg-chart-3"
            style={{ width: `${Math.max((service.total / Math.max(max, 1)) * 100, 2)}%` }}
          />
        </span>
      </div>
      <span className="text-right text-sm font-medium tabular-nums text-fg">
        {service.total.toLocaleString()}
      </span>
      <ChangeChip service={service} />
    </div>
  )
}

function ChangeChip({ service }: { service: ServiceTrend }) {
  if (service.change_pct === null || service.change_pct === undefined) {
    return (
      <span className="justify-self-end rounded-sm bg-muted px-1.5 text-xs font-medium text-fg-muted">
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
        "inline-flex items-center justify-self-end gap-0.5 rounded-sm px-1.5 text-xs font-medium tabular-nums",
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
