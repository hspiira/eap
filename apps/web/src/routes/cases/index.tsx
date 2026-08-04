import { useEffect, useState } from "react"

import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate, useSearch } from "@tanstack/react-router"
import { HeartPulse, Plus } from "lucide-react"

import { casesApi } from "@/api/endpoints/cases"
import { CaseFormSheet } from "@/components/CaseFormSheet"
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
import { RequireClinicalScope } from "@/components/common/RequireClinicalScope"
import { compareSort, nextSort, SortHeader, type SortState } from "@/components/common/SortHeader"
import { StatusBadge } from "@/components/common/StatusBadge"
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import type { Case } from "@/types/entities"
import { CaseStatus, PresentingProblem } from "@/types/enums"
import { CasePresentingProblemLabel, CaseReferralSourceLabel } from "@/utils/caseLabels"

function isStatus(v: unknown): v is CaseStatus {
  return Object.values(CaseStatus).includes(v as CaseStatus)
}
function isPresentingProblem(v: unknown): v is PresentingProblem {
  return Object.values(PresentingProblem).includes(v as PresentingProblem)
}

export const Route = createFileRoute("/cases/")({
  component: () => (
    <RequireClinicalScope>
      <CasesListPage />
    </RequireClinicalScope>
  ),
  validateSearch: (search: Record<string, unknown>) => {
    const out: {
      new?: boolean
      search?: string
      status?: CaseStatus
      presenting_problem?: PresentingProblem
    } = {}
    if (search.new === "1" || search.new === true) out.new = true
    if (typeof search.search === "string" && search.search.trim()) out.search = search.search
    if (isStatus(search.status)) out.status = search.status
    if (isPresentingProblem(search.presenting_problem))
      out.presenting_problem = search.presenting_problem
    return out
  },
})

const STATUS_OPTIONS = [
  { value: "all", label: "All statuses" },
  { value: CaseStatus.INTAKE, label: "Intake" },
  { value: CaseStatus.ASSESSMENT, label: "Assessment" },
  { value: CaseStatus.ACTIVE, label: "Active" },
  { value: CaseStatus.CLOSED, label: "Closed" },
  { value: CaseStatus.REFERRED_OUT, label: "Referred out" },
  { value: CaseStatus.NO_SHOW_CLOSED, label: "No-show closed" },
] as const

type StatusFilter = (typeof STATUS_OPTIONS)[number]["value"]

const ROW_BORDER = "border-fg/8"

function CasesListPage() {
  const searchParams = useSearch({ from: "/cases/" })
  const navigate = useNavigate({ from: "/cases/" })
  const [searchInput, setSearchInput] = useState(searchParams.search ?? "")
  const [addOpen, setAddOpen] = useState(false)
  const [sort, setSort] = useState<SortState>({ field: "opened_at", desc: true })

  useEffect(() => {
    if (searchParams.new) {
      setAddOpen(true)
      navigate({ search: (prev) => ({ ...prev, new: undefined }), replace: true })
    }
  }, [searchParams.new, navigate])

  // BE GET /cases takes no query params — filtered client-side, same as
  // care-callbacks/engagements/surveys. There is no person/name filter: a
  // Case only carries a pseudonymous clinical_subject_id by design (the
  // privacy wall), so "search" matches the pseudonym and referral notes.
  const query = useQuery({
    queryKey: ["cases", "list"],
    queryFn: () => casesApi.list(),
    staleTime: 30_000,
  })
  const allItems = query.data ?? []
  const items = filterAndSort(allItems, {
    search: searchInput.trim(),
    status: searchParams.status,
    presentingProblem: searchParams.presenting_problem,
    sort,
  })
  const loading = query.isPending
  const handleStatusChange = (next: StatusFilter) => {
    const status = next === "all" ? undefined : (next as CaseStatus)
    navigate({ search: (prev) => ({ ...prev, status }), replace: true })
  }
  const toggleSort = (field: string) => setSort((prev) => nextSort(prev, field))
  const hasFilters = Boolean(searchInput) || Boolean(searchParams.status) || Boolean(searchParams.presenting_problem)

  return (
    <PageShell
      icon={HeartPulse}
      breadcrumb="Clinical · Cases"
      actions={
        <Button size="sm" className="h-7 gap-1.5 px-2.5" onClick={() => setAddOpen(true)}>
          <Plus className="size-3.5" />
          Open case
        </Button>
      }
    >
      <FilterBar>
        <FilterButton options={[{ id: "status", label: "Status" }]} />
        {searchParams.status ? (
          <FilterChip
            label={`Status is ${searchParams.status}`}
            onRemove={() => handleStatusChange("all")}
          />
        ) : null}
        <FilterTrigger
          label="All statuses"
          value={(searchParams.status ?? "all") as StatusFilter}
          options={STATUS_OPTIONS}
          onChange={handleStatusChange}
        />
        <div className="ml-auto" />
        <FilterSearch
          value={searchInput}
          onChange={setSearchInput}
          placeholder="Search by subject reference or referral notes…"
        />
      </FilterBar>

      <CaseFormSheet open={addOpen} onOpenChange={setAddOpen} />

      <div className="flex min-h-0 flex-1 flex-col bg-bg">
        {loading ? (
          <div className="flex-1 overflow-auto p-5">
            <TableSkeleton cols={5} />
          </div>
        ) : items.length === 0 ? (
          <EmptyState
            icon={HeartPulse}
            title={hasFilters ? "No cases match your filters" : "No cases yet"}
            description={
              hasFilters
                ? "Try a different search or clear filters."
                : "Open a case to start intake for an eligible member."
            }
            action={
              hasFilters ? null : (
                <Button size="sm" className="gap-1.5" onClick={() => setAddOpen(true)}>
                  <Plus className="size-4" />
                  Open case
                </Button>
              )
            }
          />
        ) : (
          <div className="flex-1 overflow-auto">
            <Table>
              <TableHeader>
                <TableRow className={ROW_BORDER}>
                  <TableHead>Subject</TableHead>
                  <TableHead>Presenting problem</TableHead>
                  <TableHead>Referral source</TableHead>
                  <TableHead>
                    <SortHeader field="opened_at" sort={sort} onToggle={toggleSort}>
                      Opened
                    </SortHeader>
                  </TableHead>
                  <TableHead>Status</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((c) => (
                  <TableRow key={c.id} className={ROW_BORDER}>
                    <TableCell>
                      <Link
                        to="/cases/$caseId"
                        params={{ caseId: c.id }}
                        className="font-mono text-xs text-fg hover:text-primary"
                      >
                        {c.clinical_subject_id}
                      </Link>
                    </TableCell>
                    <TableCell className="text-sm text-fg/85">
                      {CasePresentingProblemLabel[c.presenting_problem]}
                    </TableCell>
                    <TableCell className="text-sm text-fg/75">
                      {CaseReferralSourceLabel[c.referral_source]}
                    </TableCell>
                    <TableCell className="text-sm text-fg/75">
                      {new Date(c.opened_at).toLocaleDateString()}
                    </TableCell>
                    <TableCell>
                      <StatusBadge status={c.status} />
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </div>
        )}
      </div>
    </PageShell>
  )
}

function filterAndSort(
  items: Case[],
  opts: {
    search: string
    status?: CaseStatus
    presentingProblem?: PresentingProblem
    sort: SortState
  },
): Case[] {
  let out = items
  if (opts.status) out = out.filter((c) => c.status === opts.status)
  if (opts.presentingProblem) out = out.filter((c) => c.presenting_problem === opts.presentingProblem)
  if (opts.search) {
    const q = opts.search.toLowerCase()
    out = out.filter(
      (c) =>
        c.clinical_subject_id.toLowerCase().includes(q) ||
        c.referral_notes?.toLowerCase().includes(q),
    )
  }
  return compareSort(out, opts.sort)
}
