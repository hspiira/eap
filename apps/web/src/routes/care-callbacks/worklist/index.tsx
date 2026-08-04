import { useState } from "react"

import { useQueries, useQuery } from "@tanstack/react-query"
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
import { compareSort, nextSort, SortHeader, type SortState } from "@/components/common/SortHeader"
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { formatDate } from "@/lib/format"
import { enumParam, listSearchSchema } from "@/lib/search-params"
import { cn } from "@/lib/utils"
import { useAuthStore } from "@/store/slices/authSlice"
import type { OutreachRecord } from "@/types/entities"
import { CareCallbackCampaignStatus, OutreachStatus } from "@/types/enums"

export const Route = createFileRoute("/care-callbacks/worklist/")({
  component: WorklistPage,
  validateSearch: listSearchSchema({
    status: enumParam(OutreachStatus),
    crisis: (v) => (v === "1" || v === true ? true : undefined),
  }),
})

const STATUS_OPTIONS = [
  { value: "all", label: "All statuses" },
  { value: OutreachStatus.PENDING, label: "Pending" },
  { value: OutreachStatus.ASSIGNED, label: "Assigned" },
  { value: OutreachStatus.CONTACTED, label: "Contacted" },
  { value: OutreachStatus.COMPLETED, label: "Completed" },
  { value: OutreachStatus.UNREACHABLE, label: "Unreachable" },
  { value: OutreachStatus.DECLINED, label: "Declined" },
  { value: OutreachStatus.ESCALATED, label: "Escalated" },
] as const

type StatusFilter = (typeof STATUS_OPTIONS)[number]["value"]

const ROW_BORDER = "border-fg/8"

/**
 * There is no "my worklist" endpoint on the BE — outreach records are only
 * listable nested under one campaign at a time (GET .../{campaign}/outreach-records),
 * with no assigned/counsellor filter. This fetches every active campaign's
 * records and filters to the current user client-side. Fine at the campaign
 * counts this product runs; would need a real BE endpoint at real scale.
 */
function useMyOutreachAcrossCampaigns(counsellorId: string | null) {
  const campaignsQuery = useQuery({
    queryKey: ["care-callback-campaigns", "list"],
    queryFn: () => careCallbacksApi.listCampaigns(),
    staleTime: 30_000,
  })
  const activeCampaigns = (campaignsQuery.data ?? []).filter(
    (c) => c.status === CareCallbackCampaignStatus.ACTIVE,
  )

  const recordQueries = useQueries({
    queries: activeCampaigns.map((c) => ({
      queryKey: ["outreach-records", "for-campaign", c.id],
      queryFn: () => careCallbacksApi.listOutreachForCampaign(c.id, { limit: 200 }),
      enabled: !!counsellorId,
    })),
  })

  const isPending = campaignsQuery.isPending || (!!counsellorId && recordQueries.some((q) => q.isPending))
  const campaignNameById = new Map(activeCampaigns.map((c) => [c.id, c.name]))
  const records = recordQueries
    .flatMap((q) => q.data ?? [])
    .filter((r) => r.counsellor_id === counsellorId)

  return { records, campaignNameById, isPending }
}

function WorklistPage() {
  const searchParams = useSearch({ from: "/care-callbacks/worklist/" })
  const navigate = useNavigate({ from: "/care-callbacks/worklist/" })
  const userId = useAuthStore((s) => s.user_id)
  const [searchInput, setSearchInput] = useState(searchParams.search ?? "")
  const [sort, setSort] = useState<SortState>({ field: "last_attempted_at", desc: false })

  const { records, campaignNameById, isPending } = useMyOutreachAcrossCampaigns(userId)
  const items = filterAndSort(records, {
    search: searchInput.trim(),
    status: searchParams.status,
    crisis: searchParams.crisis,
    sort,
  })
  const handleStatusChange = (next: StatusFilter) => {
    const status = next === "all" ? undefined : (next as OutreachStatus)
    navigate({ search: (prev) => ({ ...prev, status }), replace: true })
  }
  const toggleSort = (field: string) => setSort((prev) => nextSort(prev, field))
  const hasFilters =
    Boolean(searchInput) || Boolean(searchParams.status) || Boolean(searchParams.crisis)

  const pendingCount = records.filter((c) => c.status === OutreachStatus.ASSIGNED).length
  const crisisCount = records.filter((c) => c.crisis_flag).length

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
          placeholder="Search by person or campaign…"
        />
      </FilterBar>

      <div className="flex shrink-0 items-center gap-3 border-b border-fg/10 bg-surface px-5 py-2.5">
        <Pip label="Assigned" value={pendingCount} />
        <Pip label="Total" value={records.length} />
        {crisisCount > 0 ? (
          <span className="inline-flex items-center gap-1 rounded-sm border border-danger/30 bg-danger-soft px-2 py-0.5 text-[11px] font-medium text-danger-fg">
            <AlertTriangle className="size-3" />
            {crisisCount} crisis
          </span>
        ) : null}
      </div>

      <div className="flex min-h-0 flex-1 flex-col bg-bg">
        {isPending ? (
          <div className="flex-1 overflow-auto p-5">
            <TableSkeleton cols={4} rows={6} />
          </div>
        ) : items.length === 0 ? (
          <EmptyState
            icon={Headphones}
            title={hasFilters ? "No records match your filters" : "Your worklist is clear"}
            description={
              hasFilters
                ? "Try a different filter or clear the search."
                : "Records you've claimed (assigned to you) across active campaigns show up here."
            }
          />
        ) : (
          <div className="relative min-h-0 flex-1 overflow-auto">
            <Table className="w-full caption-bottom text-sm">
              <TableHeader className="sticky top-0 z-10 border-b-0 bg-surface shadow-[inset_0_-1px_0_rgb(0_0_0/0.08)]">
                <TableRow className={`hover:bg-transparent ${ROW_BORDER}`}>
                  <TableHead>
                    <SortHeader field="person_id" sort={sort} onToggle={toggleSort}>
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
                    <SortHeader field="last_attempted_at" sort={sort} onToggle={toggleSort}>
                      Last attempt
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
                  <CaseRow key={c.id} row={c} campaignName={campaignNameById.get(c.campaign_id) ?? null} />
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </div>
    </PageShell>
  )
}

function CaseRow({ row, campaignName }: { row: OutreachRecord; campaignName: string | null }) {
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
            <Headphones className="size-3" />
          </span>
          <span className="font-mono text-sm font-medium text-fg group-hover:text-primary">
            {row.person_id}
          </span>
        </Link>
      </TableCell>
      <TableCell>
        <Link
          to="/care-callbacks/$campaignId"
          params={{ campaignId: row.campaign_id }}
          className="text-xs text-fg/75 hover:text-primary"
        >
          {campaignName ?? row.campaign_id}
        </Link>
      </TableCell>
      <TableCell>
        <div className="flex items-center gap-1.5">
          <CaseStatusPill status={row.status} />
          {row.crisis_flag ? (
            <span
              className="inline-flex items-center gap-1 rounded-sm border border-danger/30 bg-danger-soft px-1.5 py-0.5 text-[10px] font-medium tracking-wide text-danger-fg"
              title="Crisis flag raised"
            >
              <AlertTriangle className="size-3" />
              Crisis
            </span>
          ) : null}
        </div>
      </TableCell>
      <TableCell className="text-sm text-fg/75">
        {formatDate(row.last_attempted_at)}
      </TableCell>
      <TableCell className="font-mono text-xs text-fg/75">{row.contact_attempts}</TableCell>
      <TableCell className="text-right">
        <Link
          to="/care-callbacks/worklist/$caseId"
          params={{ caseId: row.id }}
          aria-label={`Open ${row.person_id}`}
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

function CaseStatusPill({ status }: { status: OutreachStatus }) {
  const tone =
    status === OutreachStatus.ESCALATED
      ? "border-danger/30 bg-danger-soft text-danger-fg"
      : status === OutreachStatus.COMPLETED
        ? "border-primary/30 bg-primary/10 text-primary"
        : status === OutreachStatus.CONTACTED
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

function filterAndSort(
  items: OutreachRecord[],
  opts: { search: string; status?: OutreachStatus; crisis?: boolean; sort: SortState },
): OutreachRecord[] {
  let out = items
  if (opts.status) out = out.filter((c) => c.status === opts.status)
  if (opts.crisis) out = out.filter((c) => c.crisis_flag)
  if (opts.search) {
    const q = opts.search.toLowerCase()
    out = out.filter(
      (c) =>
        c.person_id.toLowerCase().includes(q) || c.campaign_id.toLowerCase().includes(q),
    )
  }
  return compareSort(out, opts.sort)
}
