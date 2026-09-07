import { useMemo } from "react"

import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate, useSearch } from "@tanstack/react-router"
import { CalendarClock, Download, ExternalLink, MoreHorizontal, Plus } from "lucide-react"

import { membersApi } from "@/api/endpoints/members"
import { providersApi } from "@/api/endpoints/providers"
import { type ServiceSessionListParams, serviceSessionsApi } from "@/api/endpoints/service-sessions"
import { servicesApi } from "@/api/endpoints/services"
import { BulkAction } from "@/components/common/BulkAction"
import { EmptyState } from "@/components/common/EmptyState"
import { ErrorState } from "@/components/common/ErrorState"
import { FilterBar, FilterChip, FilterSearch, FilterTrigger } from "@/components/common/FilterBar"
import { IconButton } from "@/components/common/IconButton"
import { PageShell } from "@/components/common/PageShell"
import { TableSkeleton } from "@/components/common/PageSkeletons"
import { SelectionBar } from "@/components/common/SelectionBar"
import { SortHeader } from "@/components/common/SortHeader"
import { StatusBadge } from "@/components/common/StatusBadge"
import { STICKY_TABLE_HEAD } from "@/components/common/tableStyles"
import { ServiceSessionFormSheet } from "@/components/ServiceSessionFormSheet"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuSeparator,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { Pagination } from "@/components/ui/pagination"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { useCanWrite } from "@/hooks/useCanWrite"
import { useListPage } from "@/hooks/useListPage"
import { useTableSelection } from "@/hooks/useTableSelection"
import { memberLabel } from "@/lib/display"
import { normalizeErrorMessage } from "@/lib/errors"
import { formatDate } from "@/lib/format"
import { useEntityList } from "@/lib/queries"
import { queryKeys } from "@/lib/query-keys"
import { enumParam, listSearchSchema } from "@/lib/search-params"
import { cn } from "@/lib/utils"
import type { Provider, Service, ServiceSession } from "@/types/entities"
import { SessionStatus } from "@/types/enums"
import { getStatusLabel } from "@/utils/statusColors"

export const Route = createFileRoute("/service-sessions/")({
  component: ServiceSessionsListPage,
  validateSearch: listSearchSchema({
    status: enumParam(SessionStatus),
    service_id: (v) => (typeof v === "string" && v.trim() ? v : undefined),
    member_id: (v) => (typeof v === "string" && v.trim() ? v : undefined),
    range: (v): Exclude<RangeFilter, "all"> | undefined =>
      v === "today" || v === "7d" || v === "30d" || v === "past" ? v : undefined,
  }),
})

const STATUS_OPTIONS = [
  { value: "all", label: "All statuses" },
  { value: SessionStatus.SCHEDULED, label: "Scheduled" },
  { value: SessionStatus.RESCHEDULED, label: "Rescheduled" },
  { value: SessionStatus.COMPLETED, label: "Completed" },
  { value: SessionStatus.CANCELLED, label: "Cancelled" },
  { value: SessionStatus.NO_SHOW, label: "No show" },
] as const

const RANGE_OPTIONS = [
  { value: "all", label: "All time" },
  { value: "today", label: "Today" },
  { value: "7d", label: "Next 7 days" },
  { value: "30d", label: "Next 30 days" },
  { value: "past", label: "Past sessions" },
] as const

type StatusFilter = (typeof STATUS_OPTIONS)[number]["value"]
type RangeFilter = (typeof RANGE_OPTIONS)[number]["value"]

const ROW_BORDER = "border-fg/8"

function ServiceSessionsListPage() {
  const searchParams = useSearch({ from: "/service-sessions/" })
  const navigate = useNavigate({ from: "/service-sessions/" })
  const {
    searchInput,
    setSearchInput,
    activeSearch,
    addOpen,
    setAddOpen,
    page,
    setPage,
    limit,
    sort,
    toggleSort,
    setFilter,
    sortParams,
  } = useListPage({
    searchParams,
    navigate,
    initialSort: { field: "scheduled_at", desc: true },
  })
  const canWrite = useCanWrite()
  const activeStatus = searchParams.status
  const activeServiceId = searchParams.service_id
  const activeMemberId = searchParams.member_id
  const activeRange: RangeFilter = searchParams.range ?? "all"

  // Anchored to the selected range, not to render: `new Date()` inline would mint
  // a new query key on every render and refetch forever.
  const rangeParams = useMemo(() => rangeBounds(activeRange, new Date()), [activeRange])

  const handleStatusChange = (next: StatusFilter) =>
    setFilter("status", next === "all" ? undefined : next)

  const clearService = () => setFilter("service_id", undefined)
  const clearMember = () => setFilter("member_id", undefined)

  const handleRangeChange = (next: RangeFilter) =>
    setFilter("range", next === "all" ? undefined : next)

  const { data: servicesData } = useQuery({
    queryKey: ["services", "lookup"],
    queryFn: () => servicesApi.list({ limit: 100 }),
    staleTime: 5 * 60_000,
  })
  const servicesById = useMemo(() => {
    const m = new Map<string, Service>()
    for (const s of servicesData?.items ?? []) m.set(s.id, s)
    return m
  }, [servicesData])

  // Counsellors are looked up in one call, as services are. Per-row fetches
  // would add a second request per row on top of the member one.
  const { data: providersData } = useQuery({
    queryKey: ["providers", "lookup"],
    queryFn: () => providersApi.list({ limit: 200 }),
    staleTime: 5 * 60_000,
  })
  const providersById = useMemo(() => {
    const m = new Map<string, Provider>()
    for (const p of providersData?.items ?? []) m.set(p.id, p)
    return m
  }, [providersData])

  const { data: activeMemberForChip = null } = useQuery({
    queryKey: queryKeys.members.detail(activeMemberId ?? ""),
    queryFn: () => membersApi.getById(activeMemberId!),
    enabled: !!activeMemberId,
    staleTime: 10 * 60_000,
  })

  const query = useEntityList<ServiceSession, ServiceSessionListParams>({
    resource: "service-sessions",
    params: {
      page,
      limit,
      search: activeSearch,
      status: activeStatus,
      service_id: activeServiceId,
      member_id: activeMemberId,
      ...rangeParams,
      ...sortParams,
    },
    listFn: serviceSessionsApi.list,
  })
  const items = query.data?.items ?? []
  const total = query.data?.total ?? 0
  const selection = useTableSelection(items)
  const loading = query.isPending
  const error = query.isError ? normalizeErrorMessage(query.error, "Failed to load data") : null
  const hasFilters =
    Boolean(activeSearch) ||
    Boolean(activeStatus) ||
    Boolean(activeServiceId) ||
    Boolean(activeMemberId) ||
    activeRange !== "all"

  const activeServiceLabel = activeServiceId
    ? (servicesById.get(activeServiceId)?.name ?? activeServiceId.slice(0, 8))
    : null
  const activeMemberLabel = activeMemberId
    ? activeMemberForChip
      ? memberLabel(activeMemberForChip)
      : "Selected member"
    : null

  return (
    <PageShell
      icon={CalendarClock}
      breadcrumb="Delivery · Sessions"
      actions={
        <>
          <IconButton label="Export" icon={Download} />
          <span className="mx-1 h-4 w-px bg-fg/15" aria-hidden />
          {canWrite && (
            <Button size="sm" className="h-7 gap-1.5 px-2.5" onClick={() => setAddOpen(true)}>
              <Plus className="size-3.5" />
              Schedule session
            </Button>
          )}
        </>
      }
    >
      <FilterBar>
        {activeStatus ? (
          <FilterChip
            label={`Status is ${activeStatus}`}
            onRemove={() => handleStatusChange("all")}
          />
        ) : null}
        {activeServiceLabel ? (
          <FilterChip label={`Service: ${activeServiceLabel}`} onRemove={clearService} />
        ) : null}
        {activeMemberLabel ? (
          <FilterChip label={`Member: ${activeMemberLabel}`} onRemove={clearMember} />
        ) : null}
        <FilterTrigger
          label="All statuses"
          value={(activeStatus ?? "all") as StatusFilter}
          options={STATUS_OPTIONS}
          onChange={handleStatusChange}
        />
        <FilterTrigger
          icon={CalendarClock}
          label="All time"
          value={activeRange}
          options={RANGE_OPTIONS}
          onChange={handleRangeChange}
        />
        <div className="ml-auto" />
        <FilterSearch
          value={searchInput}
          onChange={setSearchInput}
          placeholder="Search sessions…"
        />
      </FilterBar>

      <ServiceSessionFormSheet
        open={addOpen}
        onOpenChange={setAddOpen}
        serviceId={activeServiceId}
        memberId={activeMemberId}
      />

      <div className="flex min-h-0 flex-1 flex-col bg-bg">
        {loading ? (
          <div className="flex-1 overflow-auto p-5">
            <TableSkeleton cols={5} />
          </div>
        ) : error ? (
          <ErrorState message={error} onRetry={() => void query.refetch()} />
        ) : items.length === 0 ? (
          <EmptyState
            icon={CalendarClock}
            title={hasFilters ? "No sessions match your filters" : "No sessions yet"}
            description={
              hasFilters
                ? "Try a different search or clear filters."
                : "Schedule a session to start delivering care against a contract."
            }
            action={
              hasFilters || !canWrite ? null : (
                <Button size="sm" className="gap-1.5" onClick={() => setAddOpen(true)}>
                  <Plus className="size-4" />
                  Schedule session
                </Button>
              )
            }
          />
        ) : (
          <>
            <SelectionBar count={selection.selectedIds.size} onClear={selection.clearSelection}>
              <BulkAction
                ids={selection.selectedIds}
                label="Archive"
                confirmTitle="Archive sessions"
                confirmDescription={(n) =>
                  `${n} ${n === 1 ? "session" : "sessions"} will be archived. You can restore them later.`
                }
                destructive
                action={serviceSessionsApi.archive}
                invalidateKey={["service-sessions"]}
                verb="archived"
                noun="session"
                onDone={selection.clearSelection}
              />
            </SelectionBar>
            <div className="relative min-h-0 flex-1 overflow-auto">
              <Table className="w-full caption-bottom text-sm">
                <TableHeader className={STICKY_TABLE_HEAD}>
                  <TableRow className={`hover:bg-transparent ${ROW_BORDER}`}>
                    <TableHead className="w-10 px-3">
                      <Checkbox
                        aria-label="Select all"
                        checked={selection.selectAllState}
                        onCheckedChange={selection.toggleSelectAll}
                      />
                    </TableHead>
                    <TableHead>
                      <SortHeader field="scheduled_at" sort={sort} onToggle={toggleSort}>
                        Date
                      </SortHeader>
                    </TableHead>
                    <TableHead className="text-fg/65">Time</TableHead>
                    <TableHead>
                      <SortHeader field="member_id" sort={sort} onToggle={toggleSort}>
                        Member
                      </SortHeader>
                    </TableHead>
                    <TableHead className="text-fg/65">Client</TableHead>
                    <TableHead className="text-fg/65">Counsellor</TableHead>
                    <TableHead>
                      <SortHeader field="service_id" sort={sort} onToggle={toggleSort}>
                        Intervention
                      </SortHeader>
                    </TableHead>
                    <TableHead className="text-fg/65">Mode</TableHead>
                    <TableHead className="text-fg/65">Category</TableHead>
                    <TableHead className="text-right text-fg/65">Session #</TableHead>
                    <TableHead>
                      <SortHeader field="status" sort={sort} onToggle={toggleSort}>
                        Status
                      </SortHeader>
                    </TableHead>
                    <TableHead className="text-fg/65">Outcome</TableHead>
                    <TableHead className="w-16 text-right text-fg/65">
                      <span className="sr-only">Actions</span>
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {items.map((row) => (
                    <SessionRow
                      key={row.id}
                      row={row}
                      servicesById={servicesById}
                      providersById={providersById}
                      isSelected={selection.selectedIds.has(row.id)}
                      onToggle={() => selection.toggleSelect(row.id)}
                    />
                  ))}
                </TableBody>
              </Table>
            </div>
            {total > 0 && (
              <div className="shrink-0 border-t border-fg/10 bg-surface px-3 py-2">
                <Pagination page={page} total={total} limit={limit} onPageChange={setPage} />
              </div>
            )}
          </>
        )}
      </div>
    </PageShell>
  )
}

/** One dash, one meaning: this session did not record that value. */
function Blank() {
  return <span className="text-fg-subtle">-</span>
}

function SessionRow({
  row,
  servicesById,
  providersById,
  isSelected,
  onToggle,
}: {
  row: ServiceSession
  servicesById: Map<string, Service>
  providersById: Map<string, Provider>
  isSelected: boolean
  onToggle: () => void
}) {
  const linkedService = servicesById.get(row.service_id) ?? null
  const counsellor = row.provider_id ? (providersById.get(row.provider_id) ?? null) : null
  // A company-wide session has no member to fetch, and asking for one would
  // report it as unavailable rather than as deliberately absent.
  const { data: linkedMember = null } = useQuery({
    queryKey: queryKeys.members.detail(row.member_id ?? ""),
    queryFn: () => membersApi.getById(row.member_id!),
    enabled: Boolean(row.member_id),
    staleTime: 10 * 60_000,
  })
  const personLabel = linkedMember ? memberLabel(linkedMember) : "Member unavailable"
  const scheduled = new Date(row.scheduled_at)
  const dateLabel = formatDate(scheduled)
  const timeLabel = scheduled.toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" })
  return (
    <TableRow className={`group cursor-default ${ROW_BORDER}`}>
      <TableCell className="px-3">
        <Checkbox
          aria-label={`Select session ${row.id}`}
          checked={isSelected}
          onCheckedChange={onToggle}
        />
      </TableCell>
      <TableCell>
        <Link
          to="/service-sessions/$sessionId"
          params={{ sessionId: row.id }}
          className="flex items-center gap-2.5"
        >
          <span
            aria-hidden
            className="grid size-6 shrink-0 place-items-center bg-primary/10 text-primary"
          >
            <CalendarClock className="size-3" />
          </span>
          <span className="truncate text-sm font-medium text-fg group-hover:text-primary">
            {dateLabel}
          </span>
        </Link>
      </TableCell>
      <TableCell className="whitespace-nowrap tabular-nums text-xs text-fg/75">
        {timeLabel}
      </TableCell>
      <TableCell className="max-w-44 truncate">
        {row.member_id ? (
          <Link
            to="/members/$memberId"
            params={{ memberId: row.member_id }}
            className="text-xs text-fg/75 hover:text-primary"
          >
            {personLabel}
          </Link>
        ) : (
          <span className="text-xs text-fg-muted">Company-wide</span>
        )}
      </TableCell>
      <TableCell className="max-w-36 truncate text-xs text-fg/75">
        {linkedMember?.client_name ?? <Blank />}
      </TableCell>
      <TableCell className="max-w-36 truncate text-xs text-fg/75">
        {counsellor && row.provider_id ? (
          <Link
            to="/providers/$providerId"
            params={{ providerId: row.provider_id }}
            className="hover:text-primary"
          >
            {counsellor.display_name}
          </Link>
        ) : (
          <Blank />
        )}
      </TableCell>
      <TableCell className="max-w-40 truncate">
        <Link
          to="/services/$serviceId"
          params={{ serviceId: row.service_id }}
          className={cn(
            "text-xs text-fg/75 hover:text-primary",
            !linkedService?.name && "font-mono",
          )}
        >
          {linkedService?.name ?? row.service_id.slice(0, 8)}
        </Link>
      </TableCell>
      <TableCell className="text-xs text-fg/75">{row.session_type ?? <Blank />}</TableCell>
      <TableCell className="text-xs text-fg/75">{row.category ?? <Blank />}</TableCell>
      <TableCell className="text-right tabular-nums text-xs text-fg/75">
        {row.session_number ?? <Blank />}
      </TableCell>
      <TableCell>
        <StatusBadge status={row.status} />
      </TableCell>
      <TableCell className="text-xs text-fg/75">
        {row.clinical_outcome ? getStatusLabel(row.clinical_outcome) : <Blank />}
      </TableCell>
      <TableCell className="text-right">
        <div className="flex items-center justify-end gap-0.5 opacity-0 transition-opacity group-hover:opacity-100 focus-within:opacity-100">
          <Link
            to="/service-sessions/$sessionId"
            params={{ sessionId: row.id }}
            aria-label="Open session"
            className="grid size-7 place-items-center rounded-sm text-fg/65 hover:bg-surface-hover hover:text-fg"
          >
            <ExternalLink className="size-3.5" />
          </Link>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button
                type="button"
                variant="ghost"
                size="sm"
                aria-label="More actions"
                className="size-7 p-0 text-fg/65"
              >
                <MoreHorizontal className="size-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem asChild>
                <Link to="/service-sessions/$sessionId" params={{ sessionId: row.id }}>
                  View details
                </Link>
              </DropdownMenuItem>
              {row.member_id ? (
                <DropdownMenuItem asChild>
                  <Link to="/members/$memberId" params={{ memberId: row.member_id }}>
                    View member
                  </Link>
                </DropdownMenuItem>
              ) : null}
              <DropdownMenuItem asChild>
                <Link to="/services/$serviceId" params={{ serviceId: row.service_id }}>
                  View service
                </Link>
              </DropdownMenuItem>
              <DropdownMenuSeparator />
              <DropdownMenuItem className="text-destructive focus:text-destructive">
                Cancel
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </TableCell>
    </TableRow>
  )
}

/**
 * Turns the range dropdown into absolute instants for the server to filter on.
 * This used to filter the fetched page in memory, which contradicted the total
 * returned alongside it.
 *
 * The bounds are computed here rather than named to the server ("today") on
 * purpose: "today" means the viewer's calendar day, so the browser is the only
 * thing that knows where it starts and ends. `now` is passed in so the mapping
 * stays a pure function.
 */
function rangeBounds(
  range: RangeFilter,
  now: Date,
): Pick<ServiceSessionListParams, "scheduled_from" | "scheduled_to"> {
  if (range === "all") return {}
  if (range === "past") return { scheduled_to: now.toISOString() }
  if (range === "today") {
    const start = new Date(now)
    start.setHours(0, 0, 0, 0)
    const end = new Date(now)
    end.setHours(23, 59, 59, 999)
    return { scheduled_from: start.toISOString(), scheduled_to: end.toISOString() }
  }
  const days = range === "7d" ? 7 : 30
  return {
    scheduled_from: now.toISOString(),
    scheduled_to: new Date(now.getTime() + days * 86_400_000).toISOString(),
  }
}
