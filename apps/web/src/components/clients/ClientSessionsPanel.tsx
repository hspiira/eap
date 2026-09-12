import { useState } from "react"

import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { CalendarClock, ExternalLink, RotateCw, X } from "lucide-react"

import { serviceSessionsApi } from "@/api/endpoints/service-sessions"
import { DetailGrid, DetailRow, RailSection } from "@/components/common/DetailPrimitives"
import { EmptyState } from "@/components/common/EmptyState"
import { FilterBar, FilterTrigger } from "@/components/common/FilterBar"
import { TableSkeleton } from "@/components/common/PageSkeletons"
import { StatusBadge } from "@/components/common/StatusBadge"
import { ROW_BORDER, STICKY_TABLE_HEAD } from "@/components/common/tableStyles"
import { Button } from "@/components/ui/button"
import { Pagination } from "@/components/ui/pagination"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { normalizeErrorMessage } from "@/lib/errors"
import { formatDay } from "@/lib/format"
import { entityListKey } from "@/lib/queries"
import { cn } from "@/lib/utils"
import type { ServiceSession } from "@/types/entities"
import { SessionStatus } from "@/types/enums"
import { getStatusLabel } from "@/utils/statusColors"

const PAGE = 20

const STATUS_FILTER_OPTIONS = [
  { value: "all", label: "All statuses" },
  ...Object.values(SessionStatus).map((value) => ({ value, label: getStatusLabel(value) })),
] as const

/** A company-wide session names no member: it is the client that attended. */
function attendeeLabel(session: ServiceSession): string {
  return session.member_display_label ?? "Company-wide"
}

function rateLabel(session: ServiceSession): string | null {
  return session.rate_ugx == null ? null : `UGX ${session.rate_ugx.toLocaleString()}`
}

export function ClientSessionsPanel({ clientId }: { clientId: string }) {
  const [page, setPage] = useState(1)
  const [status, setStatus] = useState<SessionStatus | "all">("all")
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const params = {
    client_id: clientId,
    page,
    limit: PAGE,
    status: status === "all" ? undefined : status,
  }
  const query = useQuery({
    queryKey: entityListKey("service-sessions", params),
    queryFn: () => serviceSessionsApi.list(params),
  })
  const items = query.data?.items ?? []
  const selected = items.find((session) => session.id === selectedId) ?? items[0] ?? null

  return (
    <div className="grid grid-cols-12 gap-3 lg:h-[70vh]">
      <div className="col-span-12 flex min-h-0 min-w-0 flex-col border border-fg/10 bg-surface lg:col-span-8 lg:h-full">
        <FilterBar>
          <FilterTrigger
            label="All statuses"
            value={status}
            options={STATUS_FILTER_OPTIONS}
            onChange={(value) => {
              setStatus(value)
              setPage(1)
            }}
          />
          <div className="ml-auto" />
          <p className="shrink-0 text-xs text-fg-muted">
            {query.data ? `${query.data.total} sessions` : "Sessions"}
          </p>
        </FilterBar>
        <div className="min-h-0 flex-1 overflow-y-auto">
          <SessionsTable
            query={query}
            filtered={status !== "all"}
            selectedId={selected?.id ?? null}
            onSelect={setSelectedId}
          />
        </div>
        {query.data && query.data.total > PAGE && (
          <div className="shrink-0 border-t border-fg/10 px-3 py-2">
            <Pagination page={page} total={query.data.total} limit={PAGE} onPageChange={setPage} />
          </div>
        )}
      </div>

      <div className="col-span-12 flex min-h-0 min-w-0 flex-col lg:col-span-4 lg:h-full">
        {selected ? (
          <SessionSummaryCard session={selected} onClose={() => setSelectedId(null)} />
        ) : (
          <SessionsPlaceholder />
        )}
      </div>
    </div>
  )
}

function SessionsTable({
  query,
  filtered,
  selectedId,
  onSelect,
}: {
  query: ReturnType<typeof useQuery<{ items: ServiceSession[]; total: number }>>
  filtered: boolean
  selectedId: string | null
  onSelect: (id: string) => void
}) {
  if (query.isPending) return <TableSkeleton cols={6} rows={6} />
  if (query.isError)
    return (
      <div role="alert" className="flex flex-col items-center gap-2 p-8 text-center text-sm">
        <p className="text-danger-fg">
          {normalizeErrorMessage(query.error, "Could not load sessions")}
        </p>
        <Button
          type="button"
          size="sm"
          variant="outline"
          className="gap-1.5"
          onClick={() => void query.refetch()}
        >
          <RotateCw className="size-3.5" />
          Try again
        </Button>
      </div>
    )
  if (query.data.total === 0)
    return (
      <EmptyState
        icon={CalendarClock}
        title={filtered ? "No sessions match this filter" : "No sessions yet"}
        description={
          filtered
            ? "Try a different status or clear the filter."
            : "Sessions delivered to this client's people will appear here."
        }
      />
    )
  return (
    <Table className="w-full text-sm" scrollable={false}>
      <TableHeader className={STICKY_TABLE_HEAD}>
        <TableRow className={`hover:bg-transparent ${ROW_BORDER}`}>
          <TableHead>Service</TableHead>
          <TableHead className="text-center">
            <span className="sr-only">Status</span>
          </TableHead>
          <TableHead className="text-fg/65">Date</TableHead>
          <TableHead className="text-fg/65">Attendee</TableHead>
          <TableHead className="text-fg/65">Practitioner</TableHead>
          <TableHead className="text-right text-fg/65">Rate</TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        {query.data.items.map((session) => (
          <SessionRow
            key={session.id}
            session={session}
            selected={selectedId === session.id}
            onSelect={() => onSelect(session.id)}
          />
        ))}
      </TableBody>
    </Table>
  )
}

function SessionRow({
  session,
  selected,
  onSelect,
}: {
  session: ServiceSession
  selected: boolean
  onSelect: () => void
}) {
  return (
    <TableRow
      onClick={onSelect}
      className={cn(
        "group h-9 cursor-pointer",
        ROW_BORDER,
        selected && "bg-primary/5 hover:bg-primary/5",
      )}
    >
      <TableCell>
        <span className="flex items-center gap-2.5">
          <span
            aria-hidden
            className="grid size-6 shrink-0 place-items-center bg-fg/6 text-fg-muted"
          >
            <CalendarClock className="size-3.5" />
          </span>
          <span className={cn("truncate font-medium", selected ? "text-primary" : "text-fg")}>
            {session.service_name ?? "Session"}
          </span>
        </span>
      </TableCell>
      <TableCell className="text-center">
        <StatusBadge status={session.status} iconOnly />
      </TableCell>
      <TableCell className="whitespace-nowrap text-xs text-fg/70">
        {formatDay(session.scheduled_at)}
      </TableCell>
      <TableCell className="max-w-[12rem] truncate text-xs text-fg/70">
        {attendeeLabel(session)}
      </TableCell>
      <TableCell className="max-w-[12rem] truncate text-xs text-fg/70">
        {session.provider_display_name ?? <span className="text-fg-subtle">-</span>}
      </TableCell>
      <TableCell className="whitespace-nowrap text-right tabular-nums text-xs text-fg/70">
        {rateLabel(session) ?? <span className="text-fg-subtle">-</span>}
      </TableCell>
    </TableRow>
  )
}

/**
 * What one session was, read top to bottom.
 *
 * No cards inside the rail: the rail is already a panel, and boxing each group
 * again draws three frames around four lines of text. Sections are a muted
 * heading and a hairline, which is enough to separate them.
 */
function SessionSummaryCard({
  session,
  onClose,
}: {
  session: ServiceSession
  onClose: () => void
}) {
  const record = session.issue_topic || session.notes || session.cancellation_reason
  return (
    <div className="flex min-h-0 flex-col overflow-hidden border border-fg/10 bg-surface">
      <header className="flex items-start gap-2.5 border-b border-fg/10 px-3 py-2.5">
        <span aria-hidden className="grid size-7 shrink-0 place-items-center bg-fg/6 text-fg-muted">
          <CalendarClock className="size-3.5" />
        </span>
        <div className="min-w-0 flex-1">
          <h3 className="truncate text-sm font-semibold leading-tight text-fg">
            {session.service_name ?? "Session"}
          </h3>
          <p className="mt-0.5 text-[11px] text-fg-muted">{sessionSubtitle(session)}</p>
        </div>
        <StatusBadge status={session.status} size="sm" />
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={onClose}
          aria-label="Close session"
          className="size-7 shrink-0 p-0 text-fg-muted"
        >
          <X className="size-4" />
        </Button>
      </header>

      <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto overscroll-contain p-3">
        <RailSection title="Delivery">
          <DetailGrid>
            <DetailRow label="Attendee" value={attendeeLabel(session)} />
            <DetailRow label="Practitioner" value={session.provider_display_name} />
            <DetailRow
              label="Format"
              value={session.session_type ? getStatusLabel(session.session_type) : null}
            />
            <DetailRow
              label="Category"
              value={session.category ? getStatusLabel(session.category) : null}
            />
            <DetailRow label="Rate" value={rateLabel(session)} />
            <DetailRow
              label="Headcount"
              value={session.headcount ? String(session.headcount) : null}
            />
          </DetailGrid>
        </RailSection>
        {record ? (
          <RailSection title="Record" className="border-t border-fg/10 pt-3">
            <DetailGrid>
              <DetailRow label="Presenting issue" value={session.issue_topic} fullWidth />
              <DetailRow label="Notes" value={session.notes} fullWidth />
              <DetailRow label="Cancelled because" value={session.cancellation_reason} fullWidth />
            </DetailGrid>
          </RailSection>
        ) : null}
        <Link
          to="/service-sessions/$sessionId"
          params={{ sessionId: session.id }}
          className="mt-auto inline-flex items-center gap-1.5 border-t border-fg/10 pt-2.5 text-xs font-medium text-primary hover:underline"
        >
          Open full session
          <ExternalLink className="size-3" />
        </Link>
      </div>
    </div>
  )
}

/** The line under the heading: when it ran, and for how long if that is known. */
function sessionSubtitle(session: ServiceSession): string {
  const day = formatDay(session.scheduled_at)
  return session.duration ? `${day} · ${session.duration} minutes` : day
}

function SessionsPlaceholder() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-1 border border-dashed border-fg/15 p-8 text-center">
      <div className="mb-2 grid size-9 place-items-center bg-fg/6">
        <CalendarClock className="size-4 text-primary" />
      </div>
      <h3 className="text-sm font-semibold text-fg">No session selected</h3>
      <p className="max-w-[24ch] text-xs text-fg/60">Select a row to see how it was delivered.</p>
    </div>
  )
}
