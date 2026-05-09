import { useEffect, useState } from "react"

import { useQuery } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate, useSearch } from "@tanstack/react-router"
import {
  ClipboardList,
  Download,
  ExternalLink,
  MoreHorizontal,
  Plus,
  RotateCw,
} from "lucide-react"

import { surveysApi } from "@/api/endpoints/surveys"
import { EmptyState } from "@/components/common/EmptyState"
import {
  FilterBar,
  FilterButton,
  FilterChip,
  FilterSearch,
  FilterTrigger,
} from "@/components/common/FilterBar"
import { PageShell } from "@/components/common/PageShell"
import { nextSort, SortHeader, type SortState } from "@/components/common/SortHeader"
import { SurveyFormSheet } from "@/components/SurveyFormSheet"
import { TableSkeleton } from "@/components/common/PageSkeletons"
import { Button } from "@/components/ui/button"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import {
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { cn } from "@/lib/utils"
import type { Survey } from "@/types/entities"
import { SurveyStatus } from "@/types/enums"

function isStatus(v: unknown): v is SurveyStatus {
  return (
    v === SurveyStatus.DRAFT ||
    v === SurveyStatus.COLLECTING ||
    v === SurveyStatus.CLOSED
  )
}

export const Route = createFileRoute("/surveys/")({
  component: SurveysListPage,
  validateSearch: (search: Record<string, unknown>) => {
    const out: { new?: boolean; search?: string; status?: SurveyStatus } = {}
    if (search.new === "1" || search.new === true) out.new = true
    if (typeof search.search === "string" && search.search.trim()) out.search = search.search
    if (isStatus(search.status)) out.status = search.status
    return out
  },
})

const STATUS_OPTIONS = [
  { value: "all", label: "All statuses" },
  { value: SurveyStatus.DRAFT, label: "Draft" },
  { value: SurveyStatus.COLLECTING, label: "Collecting" },
  { value: SurveyStatus.CLOSED, label: "Closed" },
] as const

type StatusFilter = (typeof STATUS_OPTIONS)[number]["value"]

const ROW_BORDER = "border-fg/8"

function SurveysListPage() {
  const searchParams = useSearch({ from: "/surveys/" })
  const navigate = useNavigate({ from: "/surveys/" })
  const [searchInput, setSearchInput] = useState(searchParams.search ?? "")
  const [addOpen, setAddOpen] = useState(false)
  const [sort, setSort] = useState<SortState>({ field: "period_start", desc: true })
  useEffect(() => {
    if (searchParams.new) {
      setAddOpen(true)
      navigate({ search: (prev) => ({ ...prev, new: undefined }), replace: true })
    }
  }, [searchParams.new, navigate])

  const query = useQuery({
    queryKey: ["surveys", "list"],
    queryFn: () => surveysApi.list(),
    staleTime: 30_000,
  })
  const allItems = query.data?.items ?? []
  const items = filterAndSort(allItems, {
    search: searchInput.trim(),
    status: searchParams.status,
    sort,
  })
  const loading = query.isPending
  const handleStatusChange = (next: StatusFilter) => {
    const status = next === "all" ? undefined : (next as SurveyStatus)
    navigate({ search: (prev) => ({ ...prev, status }), replace: true })
  }
  const toggleSort = (field: string) => setSort((prev) => nextSort(prev, field))
  const hasFilters = Boolean(searchInput) || Boolean(searchParams.status)

  return (
    <PageShell
      icon={ClipboardList}
      breadcrumb="Insights · Surveys"
      actions={
        <>
          <IconButton label="Refresh" onClick={() => void query.refetch()} icon={RotateCw} />
          <IconButton label="Export" icon={Download} />
          <span className="mx-1 h-4 w-px bg-fg/15" aria-hidden />
          <Button size="sm" className="h-7 gap-1.5 px-2.5" onClick={() => setAddOpen(true)}>
            <Plus className="size-3.5" />
            New survey
          </Button>
        </>
      }
    >
      <FilterBar>
        <FilterButton
          options={[
            { id: "status", label: "Status" },
            { id: "client", label: "Client" },
            { id: "source", label: "Source" },
          ]}
        />
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
          placeholder="Search surveys…"
        />
      </FilterBar>

      <SurveyFormSheet open={addOpen} onOpenChange={setAddOpen} />

      <div className="flex min-h-0 flex-1 flex-col bg-bg">
        {loading ? (
          <div className="flex-1 overflow-auto p-5">
            <TableSkeleton cols={5} />
          </div>
        ) : items.length === 0 ? (
          <EmptyState
            icon={ClipboardList}
            title={hasFilters ? "No surveys match your filters" : "No surveys yet"}
            description={
              hasFilters
                ? "Try a different search or clear filters."
                : "Create a survey and copy the webhook URL into your provider to start collecting responses."
            }
            action={
              hasFilters ? null : (
                <Button size="sm" className="gap-1.5" onClick={() => setAddOpen(true)}>
                  <Plus className="size-4" />
                  New survey
                </Button>
              )
            }
          />
        ) : (
          <div className="relative min-h-0 flex-1 overflow-auto">
            <table className="w-full caption-bottom text-sm">
              <TableHeader className="sticky top-0 z-10 border-b-0 bg-surface shadow-[inset_0_-1px_0_rgb(0_0_0/0.08)]">
                <TableRow className={`hover:bg-transparent ${ROW_BORDER}`}>
                  <TableHead className="w-10 px-3">
                    <input
                      type="checkbox"
                      aria-label="Select all"
                      className="size-3.5 cursor-pointer accent-primary"
                    />
                  </TableHead>
                  <TableHead>
                    <SortHeader field="name" sort={sort} onToggle={toggleSort}>
                      Survey
                    </SortHeader>
                  </TableHead>
                  <TableHead>
                    <SortHeader field="status" sort={sort} onToggle={toggleSort}>
                      Status
                    </SortHeader>
                  </TableHead>
                  <TableHead>
                    <SortHeader field="period_start" sort={sort} onToggle={toggleSort}>
                      Window
                    </SortHeader>
                  </TableHead>
                  <TableHead className="text-fg/65">Source</TableHead>
                  <TableHead className="text-fg/65">Responses</TableHead>
                  <TableHead className="w-16 text-right text-fg/65">
                    <span className="sr-only">Actions</span>
                  </TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {items.map((s) => (
                  <SurveyRow key={s.id} row={s} />
                ))}
              </TableBody>
            </table>
          </div>
        )}
      </div>
    </PageShell>
  )
}

function SurveyRow({ row }: { row: Survey }) {
  return (
    <TableRow className={`group cursor-default ${ROW_BORDER}`}>
      <TableCell className="px-3">
        <input
          type="checkbox"
          aria-label={`Select ${row.name}`}
          onClick={(e) => e.stopPropagation()}
          className="size-3.5 cursor-pointer accent-primary"
        />
      </TableCell>
      <TableCell>
        <Link
          to="/surveys/$surveyId"
          params={{ surveyId: row.id }}
          className="flex items-center gap-2.5"
        >
          <span
            aria-hidden
            className="grid size-6 shrink-0 place-items-center bg-primary/10 text-primary"
          >
            <ClipboardList className="size-3" />
          </span>
          <span className="min-w-0">
            <span className="block truncate text-sm font-medium text-fg group-hover:text-primary">
              {row.name}
            </span>
            {row.description ? (
              <span className="block truncate text-xs text-fg/55">{row.description}</span>
            ) : null}
          </span>
        </Link>
      </TableCell>
      <TableCell>
        <SurveyStatusPill status={row.status} />
      </TableCell>
      <TableCell className="text-sm text-fg/75">
        {new Date(row.period_start).toLocaleDateString()}
        <span className="text-fg/40"> – </span>
        {new Date(row.period_end).toLocaleDateString()}
      </TableCell>
      <TableCell className="text-xs text-fg/75">{row.source}</TableCell>
      <TableCell className="font-mono text-xs text-fg/75">{row.response_count}</TableCell>
      <TableCell className="text-right">
        <div className="flex items-center justify-end gap-0.5 opacity-0 transition-opacity group-hover:opacity-100 focus-within:opacity-100">
          <Link
            to="/surveys/$surveyId"
            params={{ surveyId: row.id }}
            aria-label={`Open ${row.name}`}
            className="grid size-7 place-items-center rounded-sm text-fg/65 hover:bg-surface-hover hover:text-fg"
          >
            <ExternalLink className="size-3.5" />
          </Link>
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <button
                type="button"
                aria-label={`More actions for ${row.name}`}
                className="grid size-7 place-items-center rounded-sm text-fg/65 hover:bg-surface-hover hover:text-fg"
              >
                <MoreHorizontal className="size-4" />
              </button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem asChild>
                <Link to="/surveys/$surveyId" params={{ surveyId: row.id }}>
                  View details
                </Link>
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </TableCell>
    </TableRow>
  )
}

export function SurveyStatusPill({ status }: { status: SurveyStatus }) {
  const tone = statusTone(status)
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

function statusTone(status: SurveyStatus): string {
  switch (status) {
    case SurveyStatus.COLLECTING:
      return "border-primary/30 bg-primary/10 text-primary"
    case SurveyStatus.DRAFT:
      return "border-fg/20 bg-bg text-fg"
    case SurveyStatus.CLOSED:
      return "border-fg/15 bg-bg text-fg/60"
    default:
      return "border-fg/15 bg-bg text-fg/65"
  }
}

function IconButton({
  label,
  icon: Icon,
  onClick,
}: {
  label: string
  icon: React.ElementType
  onClick?: () => void
}) {
  return (
    <button
      type="button"
      onClick={onClick}
      aria-label={label}
      title={label}
      className="grid size-7 place-items-center rounded-sm text-fg/70 transition-colors hover:bg-surface-hover hover:text-fg"
    >
      <Icon className="size-3.5" />
    </button>
  )
}

function filterAndSort(
  items: Survey[],
  opts: { search: string; status?: SurveyStatus; sort: SortState },
): Survey[] {
  let out = items
  if (opts.status) out = out.filter((s) => s.status === opts.status)
  if (opts.search) {
    const q = opts.search.toLowerCase()
    out = out.filter(
      (s) =>
        s.name.toLowerCase().includes(q) ||
        s.description?.toLowerCase().includes(q) ||
        s.client_id.toLowerCase().includes(q) ||
        s.source.toLowerCase().includes(q),
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
