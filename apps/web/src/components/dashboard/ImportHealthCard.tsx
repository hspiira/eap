/**
 * The session-import backlog: how much of the current batch landed, and the
 * unresolved queues that better reference data would unlock. Each queue row
 * links to the module where that identity gets resolved.
 */

import { Link } from "@tanstack/react-router"
import { ArrowUpRight } from "lucide-react"

import type { ImportBatchSummary, ImportQueueEntry } from "@/api/generated"
import { BarList, type BarListItem } from "@/components/dashboard/BarList"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"

interface ImportHealthCardProps {
  batch: ImportBatchSummary | null | undefined
  queues: ReadonlyArray<ImportQueueEntry>
  loading?: boolean
}

const QUEUE_PRESENTATION: Record<string, { label: string; hint: string; to: string }> = {
  UnresolvedMember: {
    label: "Members not on a roster",
    hint: "Import client rosters, then re-stage the file",
    to: "/members",
  },
  MissingPractitioner: {
    label: "Rows naming no practitioner",
    hint: "The source rows carry no name to resolve",
    to: "/service-sessions",
  },
  UnmappedPractitioner: {
    label: "Practitioner names not yet mapped",
    hint: "Map aliases to practitioners",
    to: "/providers",
  },
  AmbiguousPractitioner: {
    label: "Names matching several practitioners",
    hint: "Disambiguate the alias mapping",
    to: "/providers",
  },
  UnresolvedClient: {
    label: "Unknown client names",
    hint: "Add the client or an alias",
    to: "/clients",
  },
  UnresolvedService: {
    label: "Unknown service names",
    hint: "Add the service to the catalogue",
    to: "/services",
  },
}

export function ImportHealthCard({ batch, queues, loading }: ImportHealthCardProps) {
  return (
    <Card className="rounded-md">
      <CardHeader className="flex-row items-center justify-between gap-2 space-y-0 border-b border-border p-3">
        <div className="min-w-0">
          <CardTitle className="text-sm font-semibold text-fg">Import health</CardTitle>
          {batch ? (
            <p className="truncate text-xs text-fg-muted">{batch.file_name}</p>
          ) : null}
        </div>
        {batch ? (
          <Badge variant="outline" size="sm">
            {batch.status}
          </Badge>
        ) : null}
      </CardHeader>
      <CardContent className="grid gap-3 p-3">
        <ImportHealthBody batch={batch} queues={queues} loading={loading} />
      </CardContent>
    </Card>
  )
}

function ImportHealthBody({ batch, queues, loading }: ImportHealthCardProps) {
  if (loading) return <Skeleton className="h-32 w-full" />
  if (!batch) {
    return (
      <div className="grid gap-1 py-4 text-center">
        <p className="text-sm text-fg-muted">No session imports staged yet.</p>
        <Link
          to="/service-sessions"
          className="inline-flex items-center justify-center gap-1 text-sm font-medium text-primary hover:underline"
        >
          Import sessions
          <ArrowUpRight className="size-3.5" />
        </Link>
      </div>
    )
  }

  const items: BarListItem[] = queues.map((queue) => {
    const presentation = QUEUE_PRESENTATION[queue.outcome]
    return {
      key: queue.outcome,
      label: presentation?.label ?? queue.outcome,
      value: queue.total,
      hint: presentation?.hint,
      to: presentation?.to,
    }
  })

  return (
    <>
      <AcceptedMeter accepted={batch.accepted} total={batch.row_count} />
      {items.length === 0 ? (
        <p className="py-2 text-sm text-fg-muted">
          No rows are blocked. Re-stage the file after reference data improves to pull in more.
        </p>
      ) : (
        <BarList items={items} tone="warning" />
      )}
    </>
  )
}

function AcceptedMeter({ accepted, total }: { accepted: number; total: number }) {
  const pct = total > 0 ? (accepted / total) * 100 : 0
  return (
    <div className="grid gap-1">
      <div className="flex items-baseline justify-between gap-2">
        <span className="text-xs text-fg-muted">Rows accepted</span>
        <span className="text-xs font-medium tabular-nums text-fg">
          {accepted.toLocaleString()} of {total.toLocaleString()}
        </span>
      </div>
      <div className="h-1.5 overflow-hidden rounded-full bg-primary/10">
        <div className="h-full rounded-full bg-primary" style={{ width: `${pct}%` }} />
      </div>
    </div>
  )
}
