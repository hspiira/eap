import { createFileRoute, Link, useNavigate, useSearch } from "@tanstack/react-router"
import { ClipboardList, Download, ExternalLink, Lock, MoreHorizontal, Plus } from "lucide-react"

import { type SurveyListParams, surveysApi } from "@/api/endpoints/surveys"
import { BulkAction } from "@/components/common/BulkAction"
import { EmptyState } from "@/components/common/EmptyState"
import { EntityListView } from "@/components/common/EntityListView"
import { FilterBar, FilterChip, FilterSearch, FilterTrigger } from "@/components/common/FilterBar"
import { IconButton } from "@/components/common/IconButton"
import { PageShell } from "@/components/common/PageShell"
import { SelectionBar } from "@/components/common/SelectionBar"
import { ROW_BORDER } from "@/components/common/tableStyles"
import { SurveyFormSheet } from "@/components/SurveyFormSheet"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { TableCell, TableRow } from "@/components/ui/table"
import { useListPage } from "@/hooks/useListPage"
import { useTableSelection } from "@/hooks/useTableSelection"
import { normalizeErrorMessage } from "@/lib/errors"
import { formatDate } from "@/lib/format"
import { useEntityList } from "@/lib/queries"
import { enumOptions, enumParam, listSearchSchema } from "@/lib/search-params"
import { cn } from "@/lib/utils"
import type { Survey, SurveyStatusValue } from "@/types/entities"
import { SurveyCampaignStatus } from "@/types/enums"
import { getStatusLabel } from "@/utils/statusColors"

export const Route = createFileRoute("/surveys/")({
  component: SurveysListPage,
  validateSearch: listSearchSchema({ status: enumParam(SurveyCampaignStatus) }),
})

const STATUS_OPTIONS = enumOptions(SurveyCampaignStatus, "All statuses")

type StatusFilter = (typeof STATUS_OPTIONS)[number]["value"]

const COLUMNS = [
  { header: "Survey", sortField: "name" },
  { header: "Status", sortField: "status" },
  { header: "Window", sortField: "period_start" },
  { header: "Source", className: "text-fg/65" },
  { header: "Responses", sortField: "response_count" },
]

function SurveysListPage() {
  const searchParams = useSearch({ from: "/surveys/" })
  const navigate = useNavigate({ from: "/surveys/" })
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
  } = useListPage({ searchParams, navigate, initialSort: { field: "period_start", desc: true } })

  const activeStatus = searchParams.status
  const handleStatusChange = (next: StatusFilter) =>
    setFilter("status", next === "all" ? undefined : next)

  const query = useEntityList<Survey, SurveyListParams>({
    resource: "surveys",
    params: { page, limit, search: activeSearch, status: activeStatus, ...sortParams },
    listFn: surveysApi.list,
  })
  const items = query.data?.items ?? []
  const total = query.data?.total ?? 0
  const error = query.isError ? normalizeErrorMessage(query.error, "Failed to load data") : null
  const selection = useTableSelection(items)
  const hasFilters = Boolean(activeSearch) || Boolean(activeStatus)

  return (
    <PageShell
      icon={ClipboardList}
      breadcrumb="Insights · Surveys"
      actions={
        <>
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
        {activeStatus ? (
          <FilterChip
            label={`Status is ${activeStatus}`}
            onRemove={() => handleStatusChange("all")}
          />
        ) : null}
        <FilterTrigger
          label="All statuses"
          value={(activeStatus ?? "all") as StatusFilter}
          options={STATUS_OPTIONS}
          onChange={handleStatusChange}
        />
        <div className="ml-auto" />
        <FilterSearch value={searchInput} onChange={setSearchInput} placeholder="Search surveys…" />
      </FilterBar>

      <SurveyFormSheet open={addOpen} onOpenChange={setAddOpen} />

      <EntityListView
        columns={COLUMNS}
        items={items}
        rowKey={(row) => row.id}
        renderRow={(row) => (
          <SurveyRow
            row={row}
            isSelected={selection.selectedIds.has(row.id)}
            onToggle={() => selection.toggleSelect(row.id)}
          />
        )}
        loading={query.isPending}
        error={error}
        onRetry={() => void query.refetch()}
        selectAllState={selection.selectAllState}
        onToggleSelectAll={selection.toggleSelectAll}
        empty={
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
        }
        toolbar={
          <SelectionBar count={selection.selectedIds.size} onClear={selection.clearSelection}>
            <BulkAction
              ids={selection.selectedIds}
              label="Close"
              icon={Lock}
              confirmTitle="Close surveys"
              confirmDescription={(n) =>
                `${n} ${n === 1 ? "survey" : "surveys"} will stop accepting responses. You can reopen them later.`
              }
              labelFor={(id) => items.find((i) => i.id === id)?.name ?? id}
              action={surveysApi.close}
              invalidateKey={["surveys"]}
              verb="closed"
              noun="survey"
              onDone={selection.clearSelection}
            />
          </SelectionBar>
        }
        sort={sort}
        onToggleSort={toggleSort}
        page={page}
        total={total}
        limit={limit}
        onPageChange={setPage}
      />
    </PageShell>
  )
}

function SurveyRow({
  row,
  isSelected,
  onToggle,
}: {
  row: Survey
  isSelected: boolean
  onToggle: () => void
}) {
  return (
    <TableRow className={`group cursor-default ${ROW_BORDER}`}>
      <TableCell className="px-3">
        <Checkbox
          aria-label={`Select ${row.name}`}
          checked={isSelected}
          onCheckedChange={onToggle}
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
            <span className="block truncate text-xs text-fg-muted">{row.external_form_id}</span>
          </span>
        </Link>
      </TableCell>
      <TableCell>
        <SurveyStatusPill status={row.status} />
      </TableCell>
      <TableCell className="text-sm text-fg/75">
        {formatDate(row.period_start)}
        <span className="text-fg-subtle"> – </span>
        {formatDate(row.period_end)}
      </TableCell>
      <TableCell className="text-xs text-fg/75">{getStatusLabel(row.source)}</TableCell>
      <TableCell className="tabular-nums text-xs text-fg/75">{row.response_count}</TableCell>
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
              <Button
                type="button"
                variant="ghost"
                size="sm"
                aria-label={`More actions for ${row.name}`}
                className="size-7 p-0 text-fg/65"
              >
                <MoreHorizontal className="size-4" />
              </Button>
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

export function SurveyStatusPill({ status }: { status: SurveyStatusValue }) {
  return (
    <span
      className={cn(
        "inline-flex items-center rounded-sm border px-1.5 py-0.5 text-[11px] font-medium",
        statusTone(status),
      )}
    >
      {status}
    </span>
  )
}

function statusTone(status: SurveyStatusValue): string {
  switch (status) {
    case SurveyCampaignStatus.ACTIVE:
      return "border-primary/30 bg-primary/10 text-primary"
    case SurveyCampaignStatus.DRAFT:
      return "border-fg/20 bg-bg text-fg"
    case SurveyCampaignStatus.CLOSED:
      return "border-fg/15 bg-bg text-fg/60"
    default:
      return "border-fg/15 bg-bg text-fg/65"
  }
}
