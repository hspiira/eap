import { useCallback, useState } from "react"

import { useQuery, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, Link, useNavigate, useSearch } from "@tanstack/react-router"
import { Download, ExternalLink, Plus, ScanSearch, Users } from "lucide-react"

import { type MemberDuplicateCandidate, membersApi } from "@/api/endpoints/members"
import { EmptyState } from "@/components/common/EmptyState"
import { EntityListView, type ListColumn } from "@/components/common/EntityListView"
import { FilterBar, FilterChip, FilterSearch, FilterTrigger } from "@/components/common/FilterBar"
import { IconButton } from "@/components/common/IconButton"
import { PageShell } from "@/components/common/PageShell"
import { SelectionBar } from "@/components/common/SelectionBar"
import { StatusBadge } from "@/components/common/StatusBadge"
import { MemberFormSheet } from "@/components/MemberFormSheet"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog"
import { TableCell, TableRow } from "@/components/ui/table"
import { useToast } from "@/contexts/ToastContext"
import { useCanWrite } from "@/hooks/useCanWrite"
import { useListPage } from "@/hooks/useListPage"
import { useTableSelection } from "@/hooks/useTableSelection"
import { nameInitials } from "@/lib/display"
import { normalizeErrorMessage } from "@/lib/errors"
import { useEntityList } from "@/lib/queries"
import { enumParam, listSearchSchema } from "@/lib/search-params"
import type { Member } from "@/types/entities"
import { EligibilityStatus, MemberRelation } from "@/types/enums"

export const Route = createFileRoute("/members/")({
  component: MembersListPage,
  validateSearch: listSearchSchema({
    relation: enumParam(MemberRelation),
    status: enumParam(EligibilityStatus),
    client_id: (value) => (typeof value === "string" && value.trim() ? value : undefined),
  }),
})

const COLUMNS: ListColumn[] = [
  { header: "Member", sortField: "display_label" },
  { header: "Relationship", sortField: "relation" },
  { header: "Client" },
  { header: "Eligibility", sortField: "status" },
  { header: "Contact" },
]

const RELATION_OPTIONS = [
  { value: "all", label: "All relationships" },
  { value: MemberRelation.EMPLOYEE, label: "Employees" },
  { value: MemberRelation.SPOUSE, label: "Spouses" },
  { value: MemberRelation.CHILD, label: "Children" },
  { value: MemberRelation.DOMESTIC_PARTNER, label: "Domestic partners" },
  { value: MemberRelation.DEPENDENT_OTHER, label: "Other beneficiaries" },
] as const

const STATUS_OPTIONS = [
  { value: "all", label: "All statuses" },
  { value: EligibilityStatus.ACTIVE, label: "Active" },
  { value: EligibilityStatus.SUSPENDED, label: "Suspended" },
  { value: EligibilityStatus.PENDING, label: "Pending" },
  { value: EligibilityStatus.TERMINATED, label: "Terminated" },
] as const

type RelationFilter = (typeof RELATION_OPTIONS)[number]["value"]
type StatusFilter = (typeof STATUS_OPTIONS)[number]["value"]

function MembersListPage() {
  const searchParams = useSearch({ from: "/members/" })
  const navigate = useNavigate({ from: "/members/" })
  const list = useListPage({ searchParams, navigate })
  const canWrite = useCanWrite()
  const queryClient = useQueryClient()
  const toast = useToast()
  const [editing, setEditing] = useState<Member | null>(null)
  const [duplicatesOpen, setDuplicatesOpen] = useState(false)
  const duplicatesQuery = useQuery({
    queryKey: ["members", "duplicates", searchParams.client_id],
    queryFn: () => membersApi.scanDuplicates(searchParams.client_id),
    enabled: false,
  })
  const query = useEntityList({
    resource: "members",
    params: {
      page: list.page,
      limit: list.limit,
      search: list.activeSearch,
      relation: searchParams.relation,
      status: searchParams.status,
      client_id: searchParams.client_id,
      ...list.sortParams,
    },
    listFn: membersApi.list,
  })
  const items = query.data?.items ?? []
  const selection = useTableSelection(items)

  const download = useCallback(
    async (promise: Promise<Blob>, filename: string) => {
      try {
        const blob = await promise
        const url = URL.createObjectURL(blob)
        const anchor = document.createElement("a")
        anchor.href = url
        anchor.download = filename
        anchor.click()
        URL.revokeObjectURL(url)
      } catch (error) {
        toast.showError(normalizeErrorMessage(error, "Could not download members"))
      }
    },
    [toast],
  )

  const setRelation = (value: RelationFilter) => {
    list.setFilter("relation", value === "all" ? undefined : value)
  }
  const setStatus = (value: StatusFilter) => {
    list.setFilter("status", value === "all" ? undefined : value)
  }
  const hasFilters = Boolean(
    list.activeSearch || searchParams.relation || searchParams.status || searchParams.client_id,
  )

  return (
    <PageShell
      icon={Users}
      breadcrumb="Members"
      actions={
        <>
          <IconButton
            label="Scan duplicates"
            icon={ScanSearch}
            onClick={() => {
              setDuplicatesOpen(true)
              void duplicatesQuery.refetch()
            }}
          />
          <IconButton
            label="Export members"
            icon={Download}
            onClick={() =>
              void download(
                membersApi.exportCsv({
                  search: list.activeSearch,
                  relation: searchParams.relation,
                  status: searchParams.status,
                  client_id: searchParams.client_id,
                }),
                "members.csv",
              )
            }
          />
          {canWrite ? (
            <Button
              size="sm"
              className="h-7 gap-1.5 rounded-none px-2.5"
              onClick={() => list.setAddOpen(true)}
            >
              <Plus className="size-3.5" />
              Add member
            </Button>
          ) : null}
        </>
      }
    >
      <FilterBar>
        {searchParams.relation ? (
          <FilterChip
            label={`Relationship: ${searchParams.relation}`}
            onRemove={() => setRelation("all")}
          />
        ) : null}
        {searchParams.status ? (
          <FilterChip label={`Status: ${searchParams.status}`} onRemove={() => setStatus("all")} />
        ) : null}
        <FilterTrigger
          label="All relationships"
          value={(searchParams.relation ?? "all") as RelationFilter}
          options={RELATION_OPTIONS}
          onChange={setRelation}
        />
        <FilterTrigger
          label="All statuses"
          value={(searchParams.status ?? "all") as StatusFilter}
          options={STATUS_OPTIONS}
          onChange={setStatus}
        />
        <div className="ml-auto" />
        <FilterSearch
          value={list.searchInput}
          onChange={list.setSearchInput}
          placeholder="Search members…"
        />
      </FilterBar>

      <MemberFormSheet
        open={list.addOpen || editing !== null}
        onOpenChange={(open) => {
          if (!open) {
            list.setAddOpen(false)
            setEditing(null)
          }
        }}
        member={editing}
        onSaved={() => {
          void queryClient.invalidateQueries({ queryKey: ["members"] })
          list.setAddOpen(false)
          setEditing(null)
        }}
      />

      <DuplicateDialog
        open={duplicatesOpen}
        onOpenChange={setDuplicatesOpen}
        loading={duplicatesQuery.isFetching}
        candidates={duplicatesQuery.data?.candidates ?? []}
      />

      <EntityListView
        columns={COLUMNS}
        items={items}
        rowKey={(row) => row.id}
        renderRow={(row) => (
          <MemberRow
            member={row}
            selected={selection.selectedIds.has(row.id)}
            onToggle={() => selection.toggleSelect(row.id)}
            onEdit={canWrite ? () => setEditing(row) : undefined}
          />
        )}
        loading={query.isPending}
        error={query.isError ? normalizeErrorMessage(query.error, "Failed to load members") : null}
        onRetry={() => void query.refetch()}
        empty={
          <EmptyState
            icon={Users}
            title={hasFilters ? "No members match your filters" : "No members yet"}
            description={
              hasFilters
                ? "Try a different search or clear a filter."
                : "Add or import the client-covered people who can use the wellness programme."
            }
            action={
              canWrite && !hasFilters ? (
                <Button size="sm" className="rounded-none" onClick={() => list.setAddOpen(true)}>
                  Add member
                </Button>
              ) : null
            }
          />
        }
        sort={list.sort}
        onToggleSort={list.toggleSort}
        page={list.page}
        total={query.data?.total ?? 0}
        limit={list.limit}
        onPageChange={list.setPage}
        selectAllState={selection.selectAllState}
        onToggleSelectAll={selection.toggleSelectAll}
        toolbar={
          <SelectionBar count={selection.selectedIds.size} onClear={selection.clearSelection}>
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="h-7 rounded-none px-2.5"
              onClick={() =>
                void download(
                  membersApi.exportCsv({ member_ids: [...selection.selectedIds] }),
                  "selected-members.csv",
                )
              }
            >
              <Download className="mr-1.5 size-3.5" />
              Export selected
            </Button>
          </SelectionBar>
        }
      />
    </PageShell>
  )
}

function MemberRow({
  member,
  selected,
  onToggle,
  onEdit,
}: {
  member: Member
  selected: boolean
  onToggle: () => void
  onEdit?: () => void
}) {
  const label = member.display_label ?? member.employer_member_id
  const contact = member.work_email ?? member.personal_email ?? "—"
  return (
    <TableRow className="group border-fg/8">
      <TableCell className="px-3">
        <Checkbox aria-label={`Select ${label}`} checked={selected} onCheckedChange={onToggle} />
      </TableCell>
      <TableCell>
        <Link
          to="/members/$memberId"
          params={{ memberId: member.id }}
          className="flex items-center gap-2.5"
        >
          <span
            aria-hidden
            className="grid size-6 shrink-0 place-items-center bg-primary/10 text-[10px] font-semibold text-primary"
          >
            {nameInitials(label)}
          </span>
          <span className="min-w-0">
            <span className="block truncate text-sm font-medium text-fg group-hover:text-primary">
              {label}
            </span>
            <span className="block truncate text-xs text-fg-muted">
              {member.employer_member_id}
            </span>
          </span>
        </Link>
      </TableCell>
      <TableCell className="text-xs text-fg/70">{member.relation}</TableCell>
      <TableCell>
        <span className="font-mono text-xs text-fg/60">{member.client_id.slice(0, 10)}</span>
      </TableCell>
      <TableCell>
        <StatusBadge status={member.status} />
        {member.is_currently_eligible ? (
          <span className="ml-2 text-xs text-primary">Eligible</span>
        ) : null}
      </TableCell>
      <TableCell className="text-xs text-fg/70">{contact}</TableCell>
      <TableCell className="text-right">
        {onEdit ? (
          <Button
            type="button"
            variant="ghost"
            size="sm"
            className="rounded-none px-2 text-xs"
            onClick={onEdit}
          >
            Edit
          </Button>
        ) : null}
        <Link
          to="/members/$memberId"
          params={{ memberId: member.id }}
          aria-label={`Open ${label}`}
          className="inline-grid size-7 place-items-center text-fg/65 hover:text-fg"
        >
          <ExternalLink className="size-3.5" />
        </Link>
      </TableCell>
    </TableRow>
  )
}

function DuplicateDialog({
  open,
  onOpenChange,
  loading,
  candidates,
}: {
  open: boolean
  onOpenChange: (open: boolean) => void
  loading: boolean
  candidates: MemberDuplicateCandidate[]
}) {
  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[80vh] overflow-y-auto rounded-none sm:max-w-2xl">
        <DialogHeader>
          <DialogTitle>Possible duplicate members</DialogTitle>
          <DialogDescription>
            {loading
              ? "Scanning the member roster…"
              : `${candidates.length} possible duplicate records found.`}
          </DialogDescription>
        </DialogHeader>
        {!loading && candidates.length === 0 ? (
          <p className="text-sm text-fg-muted">No likely duplicates found.</p>
        ) : null}
        <div className="space-y-2">
          {candidates.map((candidate) => (
            <div key={candidate.member.id} className="border border-fg/15 bg-surface p-3">
              <p className="text-sm font-medium text-fg">
                {candidate.member.display_label ?? candidate.member.employer_member_id}
              </p>
              <p className="text-xs text-fg-muted">Matched on {candidate.matched_on.join(", ")}</p>
            </div>
          ))}
        </div>
      </DialogContent>
    </Dialog>
  )
}
