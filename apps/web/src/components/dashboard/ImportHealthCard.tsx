/**
 * What became of the current import batch, and what is holding the rest back.
 *
 * The batch is a whole, so the headline is one part-to-whole bar: accepted,
 * already held, and blocked. The blocked reasons below carry a share of the
 * blocked total rather than a length bar. Their counts span three orders of
 * magnitude in real data, and on a shared length scale everything but the
 * largest reason collapses to an invisible sliver.
 */

import { Link } from "@tanstack/react-router"
import { ArrowUpRight } from "lucide-react"

import type { ImportBatchSummary, ImportQueueEntry } from "@/api/generated"
import { Badge } from "@/components/ui/badge"
import { Card, CardContent } from "@/components/ui/card"
import { Skeleton } from "@/components/ui/skeleton"

import { CardBar, CardStat } from "./CardBar"

interface ImportHealthCardProps {
  batch: ImportBatchSummary | null | undefined
  queues: ReadonlyArray<ImportQueueEntry>
  loading?: boolean
}

const QUEUE_PRESENTATION: Record<string, { label: string; action: string; to: string }> = {
  UnresolvedMember: {
    label: "Member not on a roster",
    action: "Import rosters",
    to: "/members",
  },
  MissingPractitioner: {
    label: "No practitioner named",
    action: "Review rows",
    to: "/service-sessions",
  },
  UnmappedPractitioner: {
    label: "Practitioner name unmapped",
    action: "Map aliases",
    to: "/providers",
  },
  AmbiguousPractitioner: {
    label: "Name matches several practitioners",
    action: "Disambiguate",
    to: "/providers",
  },
  UnresolvedClient: { label: "Client unknown", action: "Add client", to: "/clients" },
  UnresolvedService: { label: "Service unknown", action: "Add service", to: "/services" },
}

const SEGMENTS = [
  { key: "accepted", label: "Accepted", color: "var(--color-chart-good)" },
  { key: "duplicate", label: "Already held", color: "var(--color-chart-muted)" },
  { key: "blocked", label: "Blocked", color: "var(--color-chart-serious)" },
] as const

export function ImportHealthCard({ batch, queues, loading }: ImportHealthCardProps) {
  return (
    <Card className="flex h-full flex-col rounded-md">
      <CardBar
        title="Import health"
        control={
          batch ? (
            <Badge variant="outline" size="sm">
              {batch.status}
            </Badge>
          ) : undefined
        }
      >
        {batch ? (
          <>
            <CardStat value={batch.row_count.toLocaleString()} label="rows" />
            <span className="truncate text-xs text-fg-subtle">{batch.file_name}</span>
          </>
        ) : null}
      </CardBar>
      <CardContent className="grid flex-1 content-start gap-3 p-3">
        <ImportBody batch={batch} queues={queues} loading={loading} />
      </CardContent>
    </Card>
  )
}

function ImportBody({ batch, queues, loading }: ImportHealthCardProps) {
  if (loading) return <Skeleton className="h-28 w-full" />
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
  return (
    <>
      <CompositionBar batch={batch} />
      {queues.length > 0 ? <BlockedReasons queues={queues} /> : null}
    </>
  )
}

function CompositionBar({ batch }: { batch: ImportBatchSummary }) {
  const total = Math.max(batch.row_count, 1)
  const values: Record<string, number> = {
    accepted: batch.accepted,
    duplicate: batch.duplicate,
    blocked: batch.blocked,
  }
  const present = SEGMENTS.filter((segment) => values[segment.key] > 0)

  return (
    <div className="grid gap-2">
      <div className="flex h-2.5 gap-0.5 overflow-hidden rounded-full">
        {present.map((segment) => (
          <span
            key={segment.key}
            className="h-full first:rounded-l-full last:rounded-r-full"
            style={{
              width: `${(values[segment.key] / total) * 100}%`,
              background: segment.color,
            }}
          />
        ))}
      </div>
      <ul className="flex flex-wrap gap-x-4 gap-y-1">
        {present.map((segment) => (
          <li key={segment.key} className="flex items-center gap-1.5">
            <span
              className="size-2 rounded-[2px]"
              style={{ background: segment.color }}
              aria-hidden
            />
            <span className="text-xs text-fg-muted">{segment.label}</span>
            <span className="text-xs font-medium tabular-nums text-fg">
              {values[segment.key].toLocaleString()}
            </span>
            <span className="text-xs tabular-nums text-fg-subtle">
              {Math.round((values[segment.key] / total) * 100)}%
            </span>
          </li>
        ))}
      </ul>
    </div>
  )
}

function BlockedReasons({ queues }: { queues: ReadonlyArray<ImportQueueEntry> }) {
  const blocked = queues.reduce((sum, q) => sum + q.total, 0)
  return (
    <ul className="border-t border-border-subtle">
      {queues.map((queue) => {
        const presentation = QUEUE_PRESENTATION[queue.outcome]
        return (
          <li key={queue.outcome} className="border-b border-border-subtle last:border-b-0">
            <Link
              to={presentation?.to ?? "/service-sessions"}
              className="group grid grid-cols-[1fr_auto_2.5rem] items-center gap-3 py-2 focus-visible:outline-none focus-visible:ring-1 focus-visible:ring-ring"
            >
              <span className="min-w-0 truncate text-sm text-fg">
                {presentation?.label ?? queue.outcome}
              </span>
              <span className="text-sm font-medium tabular-nums text-fg">
                {queue.total.toLocaleString()}
              </span>
              <span className="text-right text-xs tabular-nums text-fg-subtle">
                {Math.round((queue.total / Math.max(blocked, 1)) * 100)}%
              </span>
            </Link>
          </li>
        )
      })}
    </ul>
  )
}
