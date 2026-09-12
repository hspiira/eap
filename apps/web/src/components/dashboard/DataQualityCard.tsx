/**
 * Derived data-quality queues: gaps that block reporting, each linking to
 * the module where the gap is closed. State is carried by icon and label
 * together, never by colour alone.
 */

import { Link } from "@tanstack/react-router"
import { AlertTriangle, ArrowUpRight, CheckCircle2, UserCog, Users } from "lucide-react"

import type { DataQuality } from "@/api/generated"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"

interface DataQualityCardProps {
  quality: DataQuality | undefined
  loading?: boolean
}

interface QualityRow {
  key: string
  label: string
  count: number
  to: string
  icon: React.ElementType
}

function rows(quality: DataQuality): QualityRow[] {
  return [
    {
      key: "providers-pending",
      label: "Practitioners pending activation",
      count: quality.providers_pending,
      to: "/providers",
      icon: UserCog,
    },
    {
      key: "clients-without-roster",
      label: "Clients without a member roster",
      count: quality.clients_without_roster,
      to: "/members",
      icon: Users,
    },
    {
      key: "sessions-missing-outcome",
      label: "Sessions missing a clinical outcome",
      count: quality.sessions_missing_outcome,
      to: "/service-sessions",
      icon: AlertTriangle,
    },
    {
      key: "sessions-missing-rate",
      label: "Sessions missing a rate",
      count: quality.sessions_missing_rate,
      to: "/service-sessions",
      icon: AlertTriangle,
    },
  ].filter((row) => row.count > 0)
}

export function DataQualityCard({ quality, loading }: DataQualityCardProps) {
  return (
    <Card className="rounded-md">
      <CardHeader className="border-b border-border p-3">
        <CardTitle className="text-sm font-semibold text-fg">Data quality</CardTitle>
      </CardHeader>
      <CardContent className="p-0">
        <DataQualityBody quality={quality} loading={loading} />
      </CardContent>
    </Card>
  )
}

function DataQualityBody({ quality, loading }: DataQualityCardProps) {
  if (loading || !quality) {
    return (
      <div className="grid gap-2 p-3">
        <Skeleton className="h-8 w-full" />
        <Skeleton className="h-8 w-full" />
      </div>
    )
  }
  const open = rows(quality)
  if (open.length === 0) {
    return (
      <div className="flex items-center gap-2 p-4">
        <CheckCircle2 className="size-4 shrink-0 text-success-fg" aria-hidden />
        <p className="text-sm text-fg-muted">No data gaps detected.</p>
      </div>
    )
  }
  return (
    <ul>
      {open.map((row, i) => (
        <li key={row.key} className={i > 0 ? "border-t border-border-subtle" : undefined}>
          <QualityLink row={row} />
        </li>
      ))}
    </ul>
  )
}

function QualityLink({ row }: { row: QualityRow }) {
  return (
    <Link
      to={row.to}
      className="group flex items-center gap-3 p-3 transition-colors hover:bg-surface-hover focus-visible:bg-surface-hover focus-visible:outline-none"
    >
      <span
        className="flex size-7 shrink-0 items-center justify-center rounded-md bg-warning-soft text-warning-fg ring-1 ring-warning/20"
        aria-hidden
      >
        <row.icon className="size-3.5" />
      </span>
      <span className="min-w-0 flex-1 text-sm text-fg">{row.label}</span>
      <span className="text-sm font-medium tabular-nums text-fg">{row.count.toLocaleString()}</span>
      <ArrowUpRight
        className="size-3.5 shrink-0 text-fg-subtle transition-colors group-hover:underline"
        aria-hidden
      />
    </Link>
  )
}
