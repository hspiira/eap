import { useMemo, useState } from "react"

import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate, useSearch } from "@tanstack/react-router"
import {
  Archive,
  ArchiveRestore,
  CalendarClock,
  CalendarX,
  Download,
  ExternalLink,
  FileUp,
  MoreHorizontal,
  Plus,
  User,
  Users,
} from "lucide-react"

import { membersApi } from "@/api/endpoints/members"
import { type ServiceSessionListParams, serviceSessionsApi } from "@/api/endpoints/service-sessions"
import { servicesApi } from "@/api/endpoints/services"
import { BulkAction } from "@/components/common/BulkAction"
import { EmptyState } from "@/components/common/EmptyState"
import { ErrorState } from "@/components/common/ErrorState"
import { FilterBar, FilterChip, FilterSearch, FilterTrigger } from "@/components/common/FilterBar"
import { IconButton } from "@/components/common/IconButton"
import { InfiniteScrollSentinel } from "@/components/common/InfiniteScrollSentinel"
import { PagedTableBody } from "@/components/common/PagedTableBody"
import { PageShell } from "@/components/common/PageShell"
import { TableSkeleton } from "@/components/common/PageSkeletons"
import { SelectionBar } from "@/components/common/SelectionBar"
import { SortHeader } from "@/components/common/SortHeader"
import { StatusBadge } from "@/components/common/StatusBadge"
import { STICKY_TABLE_HEAD } from "@/components/common/tableStyles"
import { ServiceSessionFormSheet } from "@/components/ServiceSessionFormSheet"
import { SessionImportDialog } from "@/components/sessions/SessionImportDialog"
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
import { Table, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table"
import { useCanWrite, useHasClinicalScope } from "@/hooks/useCanWrite"
import { useListPage } from "@/hooks/useListPage"
import { useTableSelection } from "@/hooks/useTableSelection"
import { useVisiblePage } from "@/hooks/useVisiblePage"
import { memberLabel } from "@/lib/display"
import { normalizeErrorMessage } from "@/lib/errors"
import { formatDate } from "@/lib/format"
import { useEntityListPages } from "@/lib/queries"
import { queryKeys } from "@/lib/query-keys"
import { enumOptions, enumParam, listSearchSchema } from "@/lib/search-params"
import { cn } from "@/lib/utils"
import type { ServiceSession } from "@/types/entities"
import { SessionCategory, SessionClinicalStatus, SessionStatus, SessionType } from "@/types/enums"
import { getStatusLabel } from "@/utils/statusColors"

export const Route = createFileRoute("/service-sessions/")({
  component: ServiceSessionsListPage,
  validateSearch: listSearchSchema({
    status: enumParam(SessionStatus),
    session_type: enumParam(SessionType),
    category: enumParam(SessionCategory),
    clinical_outcome: enumParam(SessionClinicalStatus),
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

const MODE_OPTIONS = enumOptions(SessionType, "All modes")
const CATEGORY_OPTIONS = enumOptions(SessionCategory, "All categories")
const OUTCOME_OPTIONS = enumOptions(SessionClinicalStatus, "All outcomes")

const RANGE_OPTIONS = [
  { value: "all", label: "All time" },
  { value: "today", label: "Today" },
  { value: "this_week", label: "This week" },
  { value: "this_month", label: "This month" },
  { value: "7d", label: "Next 7 days" },
  { value: "30d", label: "Next 30 days" },
  { value: "past", label: "Past sessions" },
] as const

/**
 * Ranges that look ahead. They sort soonest first, because a list of what is
 * coming is read from the near end: furthest-away-first answers no question
 * anyone asks of it.
 *
 * "This week" and "This month" are here even though they open in the past.
 * They are calendar periods, and a period you are inside is mostly ahead of
 * you; the ones already behind are what the confirmation queue is for.
 */
const FORWARD_RANGES = new Set<RangeFilter>(["today", "this_week", "this_month", "7d", "30d"])

type StatusFilter = (typeof STATUS_OPTIONS)[number]["value"]
type ModeFilter = (typeof MODE_OPTIONS)[number]["value"]
type CategoryFilter = (typeof CATEGORY_OPTIONS)[number]["value"]
type OutcomeFilter = (typeof OUTCOME_OPTIONS)[number]["value"]
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
    // Only the default moves: a column the user clicked is held in the URL and
    // still wins over this.
    initialSort: {
      field: "scheduled_at",
      desc: !FORWARD_RANGES.has(searchParams.range ?? "all"),
    },
  })
  const [importOpen, setImportOpen] = useState(false)
  const canWrite = useCanWrite()
  const { hasScope: hasClinicalScope } = useHasClinicalScope()
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

  /** Booked and still to come, which otherwise takes two dropdowns to ask for. */
  const showUpcoming = () =>
    void navigate({
      search: (prev) => ({
        ...prev,
        status: SessionStatus.SCHEDULED,
        range: "7d" as const,
        page: undefined,
      }),
    })
  const upcomingActive = activeStatus === SessionStatus.SCHEDULED && FORWARD_RANGES.has(activeRange)

  const { data: activeServiceForChip = null } = useQuery({
    queryKey: ["services", "detail", activeServiceId ?? ""],
    queryFn: () => servicesApi.getById(activeServiceId!),
    enabled: !!activeServiceId,
    staleTime: 5 * 60_000,
  })

  const { data: activeMemberForChip = null } = useQuery({
    queryKey: queryKeys.members.detail(activeMemberId ?? ""),
    queryFn: () => membersApi.getById(activeMemberId!),
    enabled: !!activeMemberId,
    staleTime: 10 * 60_000,
  })

  const [visiblePage, setVisiblePage] = useVisiblePage(page)

  const query = useEntityListPages<ServiceSession, ServiceSessionListParams>({
    resource: "service-sessions",
    params: {
      page,
      limit,
      search: activeSearch,
      status: activeStatus,
      session_type: searchParams.session_type,
      category: searchParams.category,
      clinical_outcome: searchParams.clinical_outcome,
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
    Boolean(searchParams.session_type) ||
    Boolean(searchParams.category) ||
    Boolean(searchParams.clinical_outcome) ||
    activeRange !== "all"

  const activeServiceLabel = activeServiceId
    ? (activeServiceForChip?.name ?? activeServiceId.slice(0, 8))
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
            <IconButton
              label="Import"
              icon={FileUp}
              emphasis="raised"
              onClick={() => setImportOpen(true)}
            />
          )}
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
          label="All modes"
          value={(searchParams.session_type ?? "all") as ModeFilter}
          options={MODE_OPTIONS}
          onChange={(v) => setFilter("session_type", v === "all" ? undefined : v)}
        />
        <FilterTrigger
          label="All categories"
          value={(searchParams.category ?? "all") as CategoryFilter}
          options={CATEGORY_OPTIONS}
          onChange={(v) => setFilter("category", v === "all" ? undefined : v)}
        />
        {hasClinicalScope ? (
          <FilterTrigger
            label="All outcomes"
            value={(searchParams.clinical_outcome ?? "all") as OutcomeFilter}
            options={OUTCOME_OPTIONS}
            onChange={(v) => setFilter("clinical_outcome", v === "all" ? undefined : v)}
          />
        ) : null}
        <Button
          type="button"
          variant="ghost"
          size="sm"
          aria-pressed={upcomingActive}
          onClick={showUpcoming}
          className={cn(
            "h-7 px-2 text-xs font-medium",
            upcomingActive ? "bg-primary/10 text-primary hover:bg-primary/10" : "text-fg-muted",
          )}
        >
          Upcoming
        </Button>
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

      <SessionImportDialog
        open={importOpen}
        onOpenChange={setImportOpen}
        onImported={() => void query.refetch()}
      />
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
                label="No-show"
                icon={CalendarX}
                confirmTitle="Mark sessions as no-show"
                confirmDescription={(n) =>
                  `Mark ${n} selected ${n === 1 ? "session" : "sessions"} as no-show?`
                }
                action={serviceSessionsApi.noShow}
                invalidateKey={["service-sessions"]}
                verb="marked as no-show"
                noun="session"
                onDone={selection.clearSelection}
              />
              <BulkAction
                ids={selection.selectedIds}
                label="Restore"
                icon={ArchiveRestore}
                confirmTitle="Restore sessions"
                confirmDescription={(n) =>
                  `Restore ${n} selected ${n === 1 ? "session" : "sessions"}?`
                }
                action={serviceSessionsApi.restore}
                invalidateKey={["service-sessions"]}
                verb="restored"
                noun="session"
                onDone={selection.clearSelection}
              />
              <BulkAction
                ids={selection.selectedIds}
                label="Archive"
                icon={Archive}
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
            <div
              className="relative min-h-0 flex-1 overflow-auto"
              data-scroll-restoration-id="list"
            >
              <Table className="w-full caption-bottom text-sm" scrollable={false}>
                <TableHeader className={STICKY_TABLE_HEAD}>
                  <TableRow className={`hover:bg-transparent ${ROW_BORDER}`}>
                    <TableHead className="w-10 px-3">
                      <Checkbox
                        aria-label="Select all"
                        checked={selection.selectAllState}
                        onCheckedChange={selection.toggleSelectAll}
                      />
                    </TableHead>
                    <TableHead className="text-fg/65">Attendee</TableHead>
                    <TableHead className="text-center">
                      <SortHeader field="status" sort={sort} onToggle={toggleSort}>
                        <span className="sr-only">Status</span>
                      </SortHeader>
                    </TableHead>
                    <TableHead>
                      <SortHeader field="scheduled_at" sort={sort} onToggle={toggleSort}>
                        Date
                      </SortHeader>
                    </TableHead>
                    <TableHead className="text-fg/65">Time</TableHead>
                    <TableHead className="text-fg/65">Client</TableHead>
                    <TableHead className="text-fg/65">Practitioner</TableHead>
                    <TableHead className="text-fg/65">Service</TableHead>
                    <TableHead>
                      <SortHeader field="session_type" sort={sort} onToggle={toggleSort}>
                        Mode of delivery
                      </SortHeader>
                    </TableHead>
                    <TableHead>
                      <SortHeader field="category" sort={sort} onToggle={toggleSort}>
                        Category
                      </SortHeader>
                    </TableHead>
                    <TableHead className="text-right">
                      <SortHeader field="session_number" sort={sort} onToggle={toggleSort}>
                        Session #
                      </SortHeader>
                    </TableHead>
                    <TableHead>
                      {hasClinicalScope ? (
                        <SortHeader field="clinical_outcome" sort={sort} onToggle={toggleSort}>
                          Outcome
                        </SortHeader>
                      ) : (
                        "Outcome"
                      )}
                    </TableHead>
                    <TableHead className="w-16 text-right text-fg/65">
                      <span className="sr-only">Actions</span>
                    </TableHead>
                  </TableRow>
                </TableHeader>
                <PagedTableBody
                  items={items}
                  anchorPage={page}
                  limit={limit}
                  rowKey={(row) => row.id}
                  renderRow={(row) => (
                    <SessionRow
                      row={row}
                      isSelected={selection.selectedIds.has(row.id)}
                      onToggle={() => selection.toggleSelect(row.id)}
                    />
                  )}
                  onVisiblePageChange={setVisiblePage}
                />
              </Table>
              <InfiniteScrollSentinel
                onLoadMore={query.loadMore}
                hasMore={query.hasMore}
                loadingMore={query.loadingMore}
              />
            </div>
            {total > 0 && (
              <div className="shrink-0 border-t border-fg/10 bg-surface px-3 py-2">
                <Pagination
                  page={visiblePage}
                  total={total}
                  limit={limit}
                  shownCount={items.length}
                  onPageChange={setPage}
                />
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
  isSelected,
  onToggle,
}: {
  row: ServiceSession
  isSelected: boolean
  onToggle: () => void
}) {
  // A session's name-like value is who it was for. A company-wide session has
  // no member, and its client is the attendee.
  const attendeeLabel =
    row.member_display_label ??
    (row.member_id ? "Member unavailable" : (row.client_name ?? "Company-wide"))
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
      <TableCell className="max-w-52">
        <Link
          to="/service-sessions/$sessionId"
          params={{ sessionId: row.id }}
          className="flex items-center gap-2.5"
        >
          <span
            aria-hidden
            className="grid size-6 shrink-0 place-items-center bg-fg/6 text-fg-muted"
          >
            {row.member_id ? <User className="size-3" /> : <Users className="size-3" />}
          </span>
          <span className="truncate text-sm font-medium text-fg group-hover:text-primary">
            {attendeeLabel}
          </span>
        </Link>
      </TableCell>
      <TableCell className="text-center">
        <StatusBadge status={row.status} iconOnly />
      </TableCell>
      <TableCell className="whitespace-nowrap text-xs text-fg/75">{dateLabel}</TableCell>
      <TableCell className="whitespace-nowrap tabular-nums text-xs text-fg/75">
        {timeLabel}
      </TableCell>
      <TableCell className="max-w-36 truncate text-xs text-fg/75">
        {row.client_name ?? <Blank />}
      </TableCell>
      <TableCell className="max-w-36 truncate text-xs text-fg/75">
        {row.provider_display_name && row.provider_id ? (
          <Link
            to="/providers/$providerId"
            params={{ providerId: row.provider_id }}
            className="hover:text-primary"
          >
            {row.provider_display_name}
          </Link>
        ) : (
          <Blank />
        )}
      </TableCell>
      <TableCell className="max-w-40 truncate">
        <Link
          to="/services/$serviceId"
          params={{ serviceId: row.service_id }}
          className={cn("text-xs text-fg/75 hover:text-primary", !row.service_name && "font-mono")}
        >
          {row.service_name ?? row.service_id.slice(0, 8)}
        </Link>
      </TableCell>
      <TableCell className="text-xs text-fg/75">{row.session_type ?? <Blank />}</TableCell>
      <TableCell className="text-xs text-fg/75">{row.category ?? <Blank />}</TableCell>
      <TableCell className="text-right tabular-nums text-xs text-fg/75">
        {row.session_number ?? <Blank />}
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
 * Exported for its own tests: the calendar boundaries are the whole point and
 * are easier to pin directly than through a rendered page.
 * This used to filter the fetched page in memory, which contradicted the total
 * returned alongside it.
 *
 * The bounds are computed here rather than named to the server ("today") on
 * purpose: "today" means the viewer's calendar day, so the browser is the only
 * thing that knows where it starts and ends. `now` is passed in so the mapping
 * stays a pure function.
 */
/** Whole calendar days, from the first's midnight to the last's final instant. */
function dayBounds(
  from: Date,
  to: Date,
): Pick<ServiceSessionListParams, "scheduled_from" | "scheduled_to"> {
  const start = new Date(from)
  start.setHours(0, 0, 0, 0)
  const end = new Date(to)
  end.setHours(23, 59, 59, 999)
  return { scheduled_from: start.toISOString(), scheduled_to: end.toISOString() }
}

export function rangeBounds(
  range: RangeFilter,
  now: Date,
): Pick<ServiceSessionListParams, "scheduled_from" | "scheduled_to"> {
  if (range === "all") return {}
  if (range === "past") return { scheduled_to: now.toISOString() }
  if (range === "today") {
    return dayBounds(now, now)
  }
  if (range === "this_week") {
    // Monday-start, matching how the API buckets a week.
    const monday = new Date(now)
    monday.setDate(now.getDate() - ((now.getDay() + 6) % 7))
    const sunday = new Date(monday)
    sunday.setDate(monday.getDate() + 6)
    return dayBounds(monday, sunday)
  }
  if (range === "this_month") {
    const first = new Date(now.getFullYear(), now.getMonth(), 1)
    const last = new Date(now.getFullYear(), now.getMonth() + 1, 0)
    return dayBounds(first, last)
  }
  const days = range === "7d" ? 7 : 30
  return {
    scheduled_from: now.toISOString(),
    scheduled_to: new Date(now.getTime() + days * 86_400_000).toISOString(),
  }
}
