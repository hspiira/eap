import { useState } from "react"

import { createFileRoute, Link, useNavigate, useSearch } from "@tanstack/react-router"
import {
  Building,
  CircleCheck,
  CirclePause,
  ExternalLink,
  MoreHorizontal,
  Plus,
  Power,
  PowerOff,
  ShieldOff,
} from "lucide-react"

import {
  type ProviderOrganisationListParams,
  providerOrganisationsApi,
} from "@/api/endpoints/provider-organisations"
import { BulkActionWithReason } from "@/components/common/BulkActionWithReason"
import { EmptyState } from "@/components/common/EmptyState"
import { EntityListView, type ListColumn } from "@/components/common/EntityListView"
import { EntityNameCell } from "@/components/common/EntityNameCell"
import { FilterBar, FilterChip, FilterSearch, FilterTrigger } from "@/components/common/FilterBar"
import { PageShell } from "@/components/common/PageShell"
import { SelectionBar } from "@/components/common/SelectionBar"
import { StatusBadge } from "@/components/common/StatusBadge"
import { ROW_BORDER } from "@/components/common/tableStyles"
import { ProviderOrganisationFormSheet } from "@/components/providers/ProviderOrganisationFormSheet"
import { ProviderSectionTabs } from "@/components/providers/ProviderSectionTabs"
import { Button } from "@/components/ui/button"
import { Checkbox } from "@/components/ui/checkbox"
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from "@/components/ui/dropdown-menu"
import { TableCell, TableRow } from "@/components/ui/table"
import { useCanWrite, useCurrentRole } from "@/hooks/useCanWrite"
import { useListPage } from "@/hooks/useListPage"
import { useTableSelection } from "@/hooks/useTableSelection"
import { nameInitials } from "@/lib/display"
import { normalizeErrorMessage } from "@/lib/errors"
import { useEntityList } from "@/lib/queries"
import { boolParam, enumOptions, enumParam, listSearchSchema } from "@/lib/search-params"
import type { ProviderOrganisation } from "@/types/entities"
import { OrganisationApprovalStatus, TenantRole } from "@/types/enums"

const APPROVAL_OPTIONS = enumOptions(OrganisationApprovalStatus, "All approval states")

export const Route = createFileRoute("/provider-organisations/")({
  component: ProviderOrganisationsListPage,
  validateSearch: listSearchSchema({
    approval_status: enumParam(OrganisationApprovalStatus),
    inactive: boolParam(),
  }),
})

const COLUMNS: ListColumn[] = [
  { header: "Organisation", sortField: "name" },
  { header: "Registration", className: "text-fg/65" },
  { header: "Supplier approval", className: "text-fg/65 text-center" },
  { header: "Active", className: "text-fg/65 text-center" },
  { header: "Contact", className: "text-fg/65" },
]

function ProviderOrganisationsListPage() {
  const searchParams = useSearch({ from: "/provider-organisations/" })
  const navigate = useNavigate({ from: "/provider-organisations/" })
  const list = useListPage({ searchParams, navigate, initialSort: { field: "name", desc: false } })
  const canWrite = useCanWrite()
  const isAdmin = useCurrentRole() === TenantRole.ADMIN
  const [editing, setEditing] = useState<ProviderOrganisation | null>(null)

  const query = useEntityList<ProviderOrganisation, ProviderOrganisationListParams>({
    resource: "provider-organisations",
    params: {
      page: list.page,
      limit: list.limit,
      search: list.activeSearch,
      approval_status: searchParams.approval_status,
      is_active: searchParams.inactive ? false : undefined,
      ...list.sortParams,
    },
    listFn: providerOrganisationsApi.list,
  })

  const items = query.data?.items ?? []
  const selection = useTableSelection(items)
  const hasFilters = Boolean(
    list.activeSearch || searchParams.approval_status || searchParams.inactive,
  )

  return (
    <PageShell
      icon={Building}
      trail={[{ label: "Providers" }]}
      title="Organisations"
      actions={
        canWrite ? (
          <Button size="sm" className="h-7 gap-1.5 px-2.5" onClick={() => list.setAddOpen(true)}>
            <Plus className="size-3.5" />
            Add organisation
          </Button>
        ) : null
      }
    >
      <ProviderSectionTabs />

      <FilterBar>
        {searchParams.approval_status ? (
          <FilterChip
            label={`Approval: ${searchParams.approval_status}`}
            onRemove={() => list.setFilter("approval_status", undefined)}
          />
        ) : null}
        {searchParams.inactive ? (
          <FilterChip
            label="Inactive only"
            onRemove={() => list.setFilter("inactive", undefined)}
          />
        ) : null}
        <FilterTrigger
          label="All approval states"
          value={searchParams.approval_status ?? "all"}
          options={APPROVAL_OPTIONS}
          onChange={(value) =>
            list.setFilter("approval_status", value === "all" ? undefined : value)
          }
        />
        <FilterTrigger
          label="Active and inactive"
          value={searchParams.inactive ? "inactive" : "all"}
          options={[
            { value: "all", label: "Active and inactive" },
            { value: "inactive", label: "Inactive only" },
          ]}
          onChange={(value) => list.setFilter("inactive", value === "inactive" ? "1" : undefined)}
        />
        <div className="ml-auto" />
        <FilterSearch
          value={list.searchInput}
          onChange={list.setSearchInput}
          placeholder="Search organisations…"
        />
      </FilterBar>

      <ProviderOrganisationFormSheet
        open={list.addOpen || editing !== null}
        organisation={editing}
        onOpenChange={(open) => {
          if (!open) {
            list.setAddOpen(false)
            setEditing(null)
          }
        }}
      />

      <EntityListView
        columns={COLUMNS}
        items={items}
        rowKey={(row) => row.id}
        renderRow={(row) => (
          <OrganisationRow
            organisation={row}
            isSelected={selection.selectedIds.has(row.id)}
            onToggle={() => selection.toggleSelect(row.id)}
            onEdit={canWrite ? () => setEditing(row) : undefined}
          />
        )}
        loading={query.isPending}
        error={
          query.isError ? normalizeErrorMessage(query.error, "Failed to load organisations") : null
        }
        onRetry={() => void query.refetch()}
        empty={
          <EmptyState
            icon={Building}
            title={hasFilters ? "No organisations match your filters" : "No organisations yet"}
            description={
              hasFilters
                ? "Try a different search or clear a filter."
                : "Add the supplier firms your practitioners deliver through. A firm is not a practitioner and not a login."
            }
            action={
              canWrite && !hasFilters ? (
                <Button size="sm" onClick={() => list.setAddOpen(true)}>
                  Add organisation
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
          isAdmin ? (
            <SelectionBar count={selection.selectedIds.size} onClear={selection.clearSelection}>
              <BulkActionWithReason
                ids={selection.selectedIds}
                label="Approve"
                icon={CircleCheck}
                confirmTitle="Approve organisations"
                confirmDescription={(n) =>
                  `Approve ${n} selected ${n === 1 ? "organisation" : "organisations"} as a supplier?`
                }
                labelFor={(id) => items.find((i) => i.id === id)?.name ?? id}
                action={(id, reason) => providerOrganisationsApi.runCommand(id, "approve", reason)}
                invalidateKey={["provider-organisations"]}
                verb="approved"
                noun="organisation"
                onDone={selection.clearSelection}
              />
              <BulkActionWithReason
                ids={selection.selectedIds}
                label="Suspend"
                icon={CirclePause}
                confirmTitle="Suspend organisations"
                confirmDescription={(n) =>
                  `Suspend ${n} selected ${n === 1 ? "organisation" : "organisations"} as a supplier?`
                }
                destructive
                labelFor={(id) => items.find((i) => i.id === id)?.name ?? id}
                action={(id, reason) => providerOrganisationsApi.runCommand(id, "suspend", reason)}
                invalidateKey={["provider-organisations"]}
                verb="suspended"
                noun="organisation"
                onDone={selection.clearSelection}
              />
              <BulkActionWithReason
                ids={selection.selectedIds}
                label="Revoke"
                icon={ShieldOff}
                confirmTitle="Revoke organisation approval"
                confirmDescription={(n) =>
                  `Revoke supplier approval for ${n} selected ${n === 1 ? "organisation" : "organisations"}?`
                }
                destructive
                labelFor={(id) => items.find((i) => i.id === id)?.name ?? id}
                action={(id, reason) => providerOrganisationsApi.runCommand(id, "revoke", reason)}
                invalidateKey={["provider-organisations"]}
                verb="revoked"
                noun="organisation"
                onDone={selection.clearSelection}
              />
              <BulkActionWithReason
                ids={selection.selectedIds}
                label="Deactivate"
                icon={PowerOff}
                confirmTitle="Deactivate organisations"
                confirmDescription={(n) =>
                  `Deactivate ${n} selected ${n === 1 ? "organisation" : "organisations"}?`
                }
                destructive
                labelFor={(id) => items.find((i) => i.id === id)?.name ?? id}
                action={(id, reason) =>
                  providerOrganisationsApi.runCommand(id, "deactivate", reason)
                }
                invalidateKey={["provider-organisations"]}
                verb="deactivated"
                noun="organisation"
                onDone={selection.clearSelection}
              />
              <BulkActionWithReason
                ids={selection.selectedIds}
                label="Reactivate"
                icon={Power}
                confirmTitle="Reactivate organisations"
                confirmDescription={(n) =>
                  `Reactivate ${n} selected ${n === 1 ? "organisation" : "organisations"}?`
                }
                labelFor={(id) => items.find((i) => i.id === id)?.name ?? id}
                action={(id, reason) =>
                  providerOrganisationsApi.runCommand(id, "reactivate", reason)
                }
                invalidateKey={["provider-organisations"]}
                verb="reactivated"
                noun="organisation"
                onDone={selection.clearSelection}
              />
            </SelectionBar>
          ) : undefined
        }
      />
    </PageShell>
  )
}

function OrganisationRow({
  organisation,
  isSelected,
  onToggle,
  onEdit,
}: {
  organisation: ProviderOrganisation
  isSelected: boolean
  onToggle: () => void
  onEdit?: () => void
}) {
  return (
    <TableRow className={`group h-9 ${ROW_BORDER}`}>
      <TableCell className="px-3">
        <Checkbox
          aria-label={`Select ${organisation.name}`}
          checked={isSelected}
          onCheckedChange={onToggle}
        />
      </TableCell>
      <TableCell className="max-w-[16rem] truncate">
        <Link
          to="/provider-organisations/$organisationId"
          params={{ organisationId: organisation.id }}
          className="flex items-center gap-2.5"
        >
          <EntityNameCell initials={nameInitials(organisation.name)} name={organisation.name} />
        </Link>
      </TableCell>
      <TableCell className="py-1.5 text-xs text-fg/70">
        {organisation.registration_number ?? "-"}
      </TableCell>
      <TableCell className="py-1.5 text-center">
        <StatusBadge status={organisation.approval_status} size="sm" iconOnly />
      </TableCell>
      <TableCell className="py-1.5 text-center">
        <StatusBadge status={organisation.is_active ? "active" : "inactive"} size="sm" iconOnly />
      </TableCell>
      <TableCell className="max-w-[14rem] truncate py-1.5 text-xs text-fg/70">
        {organisation.contact_email ?? organisation.contact_phone ?? "-"}
      </TableCell>
      <TableCell className="py-1.5 text-right">
        <div className="flex items-center justify-end gap-0.5 opacity-0 transition-opacity focus-within:opacity-100 group-hover:opacity-100">
          <Link
            to="/provider-organisations/$organisationId"
            params={{ organisationId: organisation.id }}
            aria-label={`Open ${organisation.name}`}
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
                aria-label={`More actions for ${organisation.name}`}
                className="size-7 p-0 text-fg/65"
              >
                <MoreHorizontal className="size-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem asChild>
                <Link
                  to="/provider-organisations/$organisationId"
                  params={{ organisationId: organisation.id }}
                >
                  View details
                </Link>
              </DropdownMenuItem>
              {onEdit ? <DropdownMenuItem onSelect={onEdit}>Edit</DropdownMenuItem> : null}
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </TableCell>
    </TableRow>
  )
}
