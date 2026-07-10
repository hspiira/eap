import { useState } from "react"

import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate, useSearch } from "@tanstack/react-router"
import {
  AlertTriangle,
  ChevronRight,
  ExternalLink,
  Headphones,
  Phone,
} from "lucide-react"

import { careCallbacksApi } from "@/api/endpoints/care-callbacks"
import { EmptyState } from "@/components/common/EmptyState"
import {
  FilterBar,
  FilterButton,
  FilterChip,
  FilterSearch,
  FilterTrigger,
} from "@/components/common/FilterBar"
import { PageShell } from "@/components/common/PageShell"
import { TableSkeleton } from "@/components/common/PageSkeletons"
import { nextSort, SortHeader, type SortState } from "@/components/common/SortHeader"
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { cn } from "@/lib/utils"
import { useAuthStore } from "@/store/slices/authSlice"
import type { CallbackCase } from "@/types/entities"
import { CallbackCaseStatus } from "@/types/enums"

function isStatus(v: unknown): v is CallbackCaseStatus {
  return (
    v === CallbackCaseStatus.QUEUED ||
    v === CallbackCaseStatus.IN_PROGRESS ||
    v === CallbackCaseStatus.COMPLETED ||
    v === CallbackCaseStatus.NO_ANSWER ||
    v === CallbackCaseStatus.DECLINED ||
    v === CallbackCaseStatus.CRISIS_ESCALATED
  )
}

export const Route = createFileRoute("/care-callbacks/worklist/")({
  component: WorklistPage,
  validateSearch: (search: Record<string, unknown>) => {
    const out: { search?: string; status?: CallbackCaseStatus; crisis?: boolean } = {}
    if (typeof search.search === "string" && search.search.trim()) out.search = search.search
    if (isStatus(search.status)) out.status = search.status
    if (search.crisis === "1" || search.crisis === true) out.crisis = true
    return out
  },
})

const STATUS_OPTIONS = [
  { value: "all", label: "All statuses" },
  { value: CallbackCaseStatus.QUEUED, label: "Queued" },
  { value: CallbackCaseStatus.IN_PROGRESS, label: "In progress" },
  { value: CallbackCaseStatus.COMPLETED, label: "Completed" },
  { value: CallbackCaseStatus.NO_ANSWER, label: "No answer" },
  { value: CallbackCaseStatus.DECLINED, label: "Declined" },
  { value: CallbackCaseStatus.CRISIS_ESCALATED, label: "Crisis escalated" },
] as const

type StatusFilter = (typeof STATUS_OPTIONS)[number]["value"]

const ROW_BORDER = "border-fg/8"

function WorklistPage() {
  const searchParams = useSearch({ from: "/care-callbacks/worklist/" })
  const navigate = useNavigate({ from: "/care-callbacks/worklist/" })
  const userId = useAuthStore((s) => s.user_id) ?? "user-helen"
  const [searchInput, setSearchInput] = useState(searchParams.search ?? "")
  const [sort, setSort] = useState<SortState>({ field: "next_attempt_at", desc: false })

  const query = useQuery({
    queryKey: [
      "care-callback-cases",
      "list",
      { assigned_user_id: userId, status: searchParams.status },
    ],
    queryFn: () =>
      careCallbacksApi.listCases({
        assigned_user_id: userId,
        status: searchParams.status,
      }),
  })
  const allItems = query.data?.items ?? []
  const items = filterAndSort(allItems, {
    search: searchInput.trim(),
    crisis: searchParams.crisis,
    sort,
  })
  const loading = query.isPending
  const handleStatusChange = (next: StatusFilter) => {
    const status = next === "all" ? undefined : (next as CallbackCaseStatus)
    navigate({ search: (prev) => ({ ...prev, status }), replace: true })
  }
  const toggleSort = (field: string) => setSort((prev) => nextSort(prev, field))
  const hasFilters =
    Boolean(searchInput) || Boolean(searchParams.status) || Boolean(searchParams.crisis)

  const queuedCount = allItems.filter((c) => c.status === CallbackCaseStatus.QUEUED).length
  const crisisCount = allItems.filter((c) => c.crisis_flagged).length

  return (
    <PageShell
      icon={Headphones}
      breadcrumb="Care · My worklist"
      actions={
        <>
          <span className="mx-1 h-4 w-px bg-fg/15" aria-hidden />
          <Button
            size="sm"
            variant="outline"
            className="h-7 gap-1.5 px-2.5"
            onClick={() => navigate({ to: "/care-callbacks" })}
          >
            <Phone className="size-3.5" />
            Campaigns
          </Button>
        </>
      }
    >
      <FilterBar>
        <FilterButton
          options={[
            { id: "status", label: "Status" },
            { id: "crisis", label: "Crisis only" },
          ]}
        />
        {searchParams.status ? (
          <FilterChip
            label={`Status is ${searchParams.status}`}
            onRemove={() => handleStatusChange("all")}
          />
        ) : null}
        {searchParams.crisis ? (
          <FilterChip
            label="Crisis only"
            onRemove={() =>
              navigate({ search: (prev) => ({ ...prev, crisis: undefined }), replace: true })
            }
          />
        ) : null}
        <FilterTrigger
          label="All statuses"
          value={(searchParams.status ?? "all") as StatusFilter}
          options={STATUS_OPTIONS}
          onChange={handleStatusChange}
        />
        <Button
          type="button"
          variant="outline"
          size="sm"
          onClick={() =>
            navigate({
              search: (prev) => ({
                ...prev,
                crisis: searchParams.crisis ? undefined : true,
              }),
              replace: true,
            })
          }
          className={cn(
            "h-8 shrink-0 gap-1.5 rounded-sm px-2 text-sm",
            searchParams.crisis
              ? "border-danger/40 bg-danger-soft text-danger-fg hover:bg-danger-soft"
              : "border-fg/25 text-fg/80",
          )}
        >
          <AlertTriangle className="size-3.5" />
          Crisis only
        </Button>
        <div className="ml-auto" />
        <FilterSearch
          value={searchInput}
          onChange={setSearchInput}
          placeholder="Search by name…"
        />
      </FilterBar>

      <div className="flex shrink-0 items-center gap-3 border-b border-fg/10 bg-surface px-5 py-2.5">
        <Pip label="Queued" value={queuedCount} />
        <Pip label="Total" value={allItems.length} />
        {crisisCount > 0 ? (
          <span className="inline-flex items-center gap-1 rounded-sm border border-danger/30 bg-danger-soft px-2 py-0.5 text-[11px] font-medium text-danger-fg">
            <AlertTriangle className="size-3" />
            {crisisCount} crisis
          </span>
        ) : null}
      </div>

      <div className="flex min-h-0 flex-1 flex-col bg-bg">
        {loading ? (
          <div className="flex-1 overflow-auto p-5">
            <TableSkeleton cols={4} rows={6} />
          </div>
        ) : items.length === 0 ? (
          <EmptyState
            icon={Headphones}
            title={hasFilters ? "No cases match your filters" : "Your worklist is clear"}
            description={
              hasFilters
                ? "Try a different filter or clear the search."
                : "New cases assigned to you will show up here."
            }
          />
        ) : (
          <div className="relative min-h-0 flex-1 overflow-auto">
            <Table className="w-full caption-bottom text-sm">
              <TableHeader className="sticky top-0 z-10 border-b-0 bg-surface shadow-[inset_0_-1px_0_rgb(0_0_0/0.08)]">
                <TableRow className={`hover:bg-transparent ${ROW_BORDER}`}>
                  <TableHead>
                    <SortHeader field="person_display_name" sort={sort} onToggle={toggleSort}>
                      Person
                    </SortHeader>
                  </TableHead>
                  <TableHead>
                    <SortHeader field="campaign_id" sort={sort} onToggle={toggleSort}>
                      Campaign
                    </SortHeader>
                  </TableHead>
                  <TableHead>
                    <SortHeader field="status" sort={sort} onToggle={toggleSort}>
                      Status
                    </SortHeader>
                  </TableHead>
                  <TableHead>
                    <SortHeader field="next_attempt_at" sort={sort} onToggle={toggleSort}>
                      Next attempt
                    </SortHeader>
                  </TableHead>
                  <TableHead className="text-fg/65">Attempts</TableHead>
                  <TableHead className="w-16 text-right text-fg/65">
                    <span className="sr-only">Actions</span>
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((c) => (
                  <CaseRow key={c.id} row={c} />
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </div>
    </PageShell>
  )
}

function CaseRow({ row }: { row: CallbackCase }) {
  return (
    <TableRow className={`group cursor-default ${ROW_BORDER}`}>
      <TableCell>
        <Link
          to="/care-callbacks/worklist/$caseId"
          params={{ caseId: row.id }}
          className="flex items-center gap-2.5"
        >
          <span
            aria-hidden
            className="grid size-6 shrink-0 place-items-center bg-primary/10 font-mono text-[10px] font-semibold text-primary"
          >
            {personInitial(row.person_display_name)}
          </span>
          <span className="text-sm font-medium text-fg group-hover:text-primary">
            {row.person_display_name}
          </span>
        </Link>
      </TableCell>
      <TableCell>
        <Link
          to="/care-callbacks/$campaignId"
          params={{ campaignId: row.campaign_id }}
          className="font-mono text-xs text-fg/75 hover:text-primary"
        >
          {row.campaign_id}
        </Link>
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-1.5">
          <CaseStatusPill status={row.status} />
          {row.crisis_flagged ? (
            <span
              className="inline-flex items-center gap-1 rounded-sm border border-danger/30 bg-danger-soft px-1.5 py-0.5 text-[10px] font-medium tracking-wide text-danger-fg"
              title="Crisis protocol invoked"
            >
              <AlertTriangle className="size-3" />
              Crisis
            </span>
          ) : null}
        </div>
      </TableCell>
      <TableCell className="text-sm text-fg/75">
        {row.next_attempt_at ? new Date(row.next_attempt_at).toLocaleDateString() : "—"}
      </TableCell>
      <TableCell className="font-mono text-xs text-fg/75">{row.attempt_count}</TableCell>
      <TableCell className="text-right">
        <Link
          to="/care-callbacks/worklist/$caseId"
          params={{ caseId: row.id }}
          aria-label={`Open ${row.person_display_name}`}
          className="inline-grid size-7 place-items-center rounded-sm text-fg/65 hover:bg-surface-hover hover:text-fg group-hover:opacity-100"
        >
          <ChevronRight className="size-3.5" />
          <span className="sr-only">Open</span>
          <ExternalLink className="hidden" />
        </Link>
      </TableCell>
    </TableRow>
  )
}

function CaseStatusPill({ status }: { status: CallbackCaseStatus }) {
  const tone =
    status === CallbackCaseStatus.CRISIS_ESCALATED
      ? "border-danger/30 bg-danger-soft text-danger-fg"
      : status === CallbackCaseStatus.COMPLETED
        ? "border-primary/30 bg-primary/10 text-primary"
        : status === CallbackCaseStatus.IN_PROGRESS
          ? "border-fg/25 bg-bg text-fg"
          : "border-fg/15 bg-bg text-fg/75"
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-sm border px-1.5 py-0.5 text-[11px] font-medium",
        tone,
      )}
    >
      {status}
    </span>
  )
}

function Pip({ label, value }: { label: string; value: number }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-xs">
      <span className="text-fg/55">{label}</span>
      <span className="font-mono text-sm font-semibold text-fg">{value}</span>
    </span>
  )
}

function personInitial(name: string): string {
  const trimmed = name.trim()
  if (!trimmed) return "·"
  const parts = trimmed.split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return trimmed.slice(0, 2).toUpperCase()
}

function filterAndSort(
  items: CallbackCase[],
  opts: { search: string; crisis?: boolean; sort: SortState },
): CallbackCase[] {
  let out = items
  if (opts.crisis) out = out.filter((c) => c.crisis_flagged)
  if (opts.search) {
    const q = opts.search.toLowerCase()
    out = out.filter(
      (c) =>
        c.person_display_name.toLowerCase().includes(q) ||
        c.campaign_id.toLowerCase().includes(q),
    )
  }
  if (opts.sort.field) {
    const dir = opts.sort.desc ? -1 : 1
    out = [...out].sort((a, b) => {
      const av = (a as unknown as Record<string, unknown>)[opts.sort.field as string]
      const bv = (b as unknown as Record<string, unknown>)[opts.sort.field as string]
      if (av == null && bv == null) return 0
      if (av == null) return 1
      if (bv == null) return -1
      if (typeof av === "number" && typeof bv === "number") return (av - bv) * dir
      return String(av).localeCompare(String(bv)) * dir
    })
  }
  return out
}
