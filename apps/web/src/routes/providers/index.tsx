import { useState } from "react"

import { createFileRoute, Link, useNavigate, useSearch } from "@tanstack/react-router"
import {
  ExternalLink,
  MoreHorizontal,
  Plus,
  Power,
  PowerOff,
  Stethoscope,
  UserMinus,
  UserPlus,
} from "lucide-react"

import { type ProviderListParams, providersApi } from "@/api/endpoints/providers"
import { BulkActionWithReason } from "@/components/common/BulkActionWithReason"
import { EmptyState } from "@/components/common/EmptyState"
import { EntityListView, type ListColumn } from "@/components/common/EntityListView"
import { EntityNameCell } from "@/components/common/EntityNameCell"
import { FilterBar, FilterChip, FilterSearch, FilterTrigger } from "@/components/common/FilterBar"
import { PageShell } from "@/components/common/PageShell"
import { ProviderTierBadge } from "@/components/common/ProviderTierBadge"
import { SelectionBar } from "@/components/common/SelectionBar"
import { StatusBadge } from "@/components/common/StatusBadge"
import { ROW_BORDER } from "@/components/common/tableStyles"
import { ProviderFormSheet } from "@/components/providers/ProviderFormSheet"
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
import { enumOptions, enumParam, listSearchSchema } from "@/lib/search-params"
import type { Provider } from "@/types/entities"
import {
  AccreditationStatus,
  BaseStatus,
  PanelStatus,
  ProviderTier,
  TenantRole,
  UgandaRegion,
} from "@/types/enums"

const TIER_OPTIONS = enumOptions(ProviderTier, "All tiers")
const REGION_OPTIONS = enumOptions(UgandaRegion, "All regions")
const PANEL_OPTIONS = enumOptions(PanelStatus, "All panel states")
const ACCREDITATION_OPTIONS = enumOptions(AccreditationStatus, "All accreditation")

export const Route = createFileRoute("/providers/")({
  component: ProvidersListPage,
  validateSearch: listSearchSchema({
    tier: enumParam(ProviderTier),
    region: enumParam(UgandaRegion),
    panel_status: enumParam(PanelStatus),
    accreditation_status: enumParam(AccreditationStatus),
  }),
})

const COLUMNS: ListColumn[] = [
  { header: "Practitioner", sortField: "display_name" },
  { header: "Tier", className: "text-fg/65" },
  { header: "Region", className: "text-fg/65" },
  { header: "Panel", className: "text-fg/65 text-center" },
  { header: "Accreditation", className: "text-fg/65 text-center" },
  { header: "Email", className: "text-fg/65" },
  { header: "Phone", className: "text-fg/65" },
  { header: "Account", className: "text-fg/65" },
]

/** The API filters are repeatable; the URL carries at most one value each. */
function one<T>(value: T | undefined): T[] | undefined {
  return value ? [value] : undefined
}

function ProvidersListPage() {
  const searchParams = useSearch({ from: "/providers/" })
  const navigate = useNavigate({ from: "/providers/" })
  const list = useListPage({
    searchParams,
    navigate,
    initialSort: { field: "display_name", desc: false },
  })
  const canWrite = useCanWrite()
  const isAdmin = useCurrentRole() === TenantRole.ADMIN
  const [editing, setEditing] = useState<Provider | null>(null)

  const query = useEntityList<Provider, ProviderListParams>({
    resource: "providers",
    params: {
      page: list.page,
      limit: list.limit,
      search: list.activeSearch,
      tier: one(searchParams.tier),
      region: one(searchParams.region),
      panel_status: one(searchParams.panel_status),
      accreditation_status: one(searchParams.accreditation_status),
      ...list.sortParams,
    },
    listFn: providersApi.list,
  })

  const items = query.data?.items ?? []
  const selection = useTableSelection(items)
  const hasFilters = Boolean(
    list.activeSearch ||
    searchParams.tier ||
    searchParams.region ||
    searchParams.panel_status ||
    searchParams.accreditation_status,
  )

  const clear = (key: string) => () => list.setFilter(key, undefined)
  const set = (key: string) => (value: string) =>
    list.setFilter(key, value === "all" ? undefined : value)

  return (
    <PageShell
      icon={Stethoscope}
      trail={[{ label: "Providers" }]}
      title="Practitioners"
      actions={
        canWrite ? (
          <Button size="sm" className="h-7 gap-1.5 px-2.5" onClick={() => list.setAddOpen(true)}>
            <Plus className="size-3.5" />
            Add practitioner
          </Button>
        ) : null
      }
    >
      <ProviderSectionTabs />

      <FilterBar>
        {searchParams.tier ? (
          <FilterChip label={`Tier: ${searchParams.tier}`} onRemove={clear("tier")} />
        ) : null}
        {searchParams.region ? (
          <FilterChip label={`Region: ${searchParams.region}`} onRemove={clear("region")} />
        ) : null}
        {searchParams.panel_status ? (
          <FilterChip
            label={`Panel: ${searchParams.panel_status}`}
            onRemove={clear("panel_status")}
          />
        ) : null}
        {searchParams.accreditation_status ? (
          <FilterChip
            label={`Accreditation: ${searchParams.accreditation_status}`}
            onRemove={clear("accreditation_status")}
          />
        ) : null}
        <FilterTrigger
          label="All tiers"
          value={searchParams.tier ?? "all"}
          options={TIER_OPTIONS}
          onChange={set("tier")}
        />
        <FilterTrigger
          label="All regions"
          value={searchParams.region ?? "all"}
          options={REGION_OPTIONS}
          onChange={set("region")}
        />
        <FilterTrigger
          label="All panel states"
          value={searchParams.panel_status ?? "all"}
          options={PANEL_OPTIONS}
          onChange={set("panel_status")}
        />
        <FilterTrigger
          label="All accreditation"
          value={searchParams.accreditation_status ?? "all"}
          options={ACCREDITATION_OPTIONS}
          onChange={set("accreditation_status")}
        />
        <div className="ml-auto" />
        <FilterSearch
          value={list.searchInput}
          onChange={list.setSearchInput}
          placeholder="Search practitioners…"
        />
      </FilterBar>

      <ProviderFormSheet
        open={list.addOpen || editing !== null}
        provider={editing}
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
          <ProviderRow
            provider={row}
            isSelected={selection.selectedIds.has(row.id)}
            onToggle={() => selection.toggleSelect(row.id)}
            onEdit={canWrite ? () => setEditing(row) : undefined}
          />
        )}
        loading={query.isPending}
        error={
          query.isError ? normalizeErrorMessage(query.error, "Failed to load practitioners") : null
        }
        onRetry={() => void query.refetch()}
        empty={
          <EmptyState
            icon={Stethoscope}
            title={hasFilters ? "No practitioners match your filters" : "No practitioners yet"}
            description={
              hasFilters
                ? "Try a different search or clear a filter."
                : "Add the counsellors who deliver sessions. A practitioner does not need a login."
            }
            action={
              canWrite && !hasFilters ? (
                <Button size="sm" onClick={() => list.setAddOpen(true)}>
                  Add practitioner
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
                label="Activate"
                icon={Power}
                confirmTitle="Activate practitioners"
                confirmDescription={(n) =>
                  `Activate ${n} selected ${n === 1 ? "practitioner" : "practitioners"}?`
                }
                labelFor={(id) => items.find((i) => i.id === id)?.display_name ?? id}
                action={(id, reason) =>
                  providersApi.changeStatus(id, { status: BaseStatus.ACTIVE, reason })
                }
                invalidateKey={["providers"]}
                verb="activated"
                noun="practitioner"
                onDone={selection.clearSelection}
              />
              <BulkActionWithReason
                ids={selection.selectedIds}
                label="Deactivate"
                icon={PowerOff}
                confirmTitle="Deactivate practitioners"
                confirmDescription={(n) =>
                  `Deactivate ${n} selected ${n === 1 ? "practitioner" : "practitioners"}?`
                }
                destructive
                labelFor={(id) => items.find((i) => i.id === id)?.display_name ?? id}
                action={(id, reason) =>
                  providersApi.changeStatus(id, { status: BaseStatus.INACTIVE, reason })
                }
                invalidateKey={["providers"]}
                verb="deactivated"
                noun="practitioner"
                onDone={selection.clearSelection}
              />
              <BulkActionWithReason
                ids={selection.selectedIds}
                label="Suspend from panel"
                icon={UserMinus}
                confirmTitle="Suspend practitioners from panel"
                confirmDescription={(n) =>
                  `Suspend ${n} selected ${n === 1 ? "practitioner" : "practitioners"} from the panel? They will not be bookable.`
                }
                destructive
                labelFor={(id) => items.find((i) => i.id === id)?.display_name ?? id}
                action={(id, reason) =>
                  providersApi.changePanelStatus(id, {
                    panel_status: PanelStatus.SUSPENDED,
                    reason,
                  })
                }
                invalidateKey={["providers"]}
                verb="suspended from panel"
                noun="practitioner"
                onDone={selection.clearSelection}
              />
              <BulkActionWithReason
                ids={selection.selectedIds}
                label="Reactivate panel"
                icon={UserPlus}
                confirmTitle="Reactivate practitioners on panel"
                confirmDescription={(n) =>
                  `Reactivate ${n} selected ${n === 1 ? "practitioner" : "practitioners"} on the panel?`
                }
                labelFor={(id) => items.find((i) => i.id === id)?.display_name ?? id}
                action={(id, reason) =>
                  providersApi.changePanelStatus(id, { panel_status: PanelStatus.ACTIVE, reason })
                }
                invalidateKey={["providers"]}
                verb="reactivated on panel"
                noun="practitioner"
                onDone={selection.clearSelection}
              />
            </SelectionBar>
          ) : undefined
        }
      />
    </PageShell>
  )
}

function ProviderRow({
  provider,
  isSelected,
  onToggle,
  onEdit,
}: {
  provider: Provider
  isSelected: boolean
  onToggle: () => void
  onEdit?: () => void
}) {
  const profile = provider.provider_profile
  return (
    <TableRow className={`group h-9 ${ROW_BORDER}`}>
      <TableCell className="px-3">
        <Checkbox
          aria-label={`Select ${provider.display_name}`}
          checked={isSelected}
          onCheckedChange={onToggle}
        />
      </TableCell>
      <TableCell className="max-w-[14rem] truncate">
        <Link
          to="/providers/$providerId"
          params={{ providerId: provider.id }}
          className="flex items-center gap-2.5"
        >
          <EntityNameCell
            initials={nameInitials(provider.display_name)}
            name={provider.formal_name || provider.display_name}
          />
        </Link>
      </TableCell>
      <TableCell className="py-1.5">
        <ProviderTierBadge tier={profile.tier} />
      </TableCell>
      <TableCell className="py-1.5 text-xs text-fg/70">{profile.region}</TableCell>
      <TableCell className="py-1.5 text-center">
        <StatusBadge status={profile.panel_status} size="sm" iconOnly />
      </TableCell>
      <TableCell className="py-1.5 text-center">
        <StatusBadge status={profile.accreditation_status} size="sm" iconOnly />
      </TableCell>
      <TableCell className="max-w-[14rem] truncate py-1.5 text-xs text-fg/70">
        {provider.email ?? <span className="text-fg-subtle">-</span>}
      </TableCell>
      <TableCell className="whitespace-nowrap py-1.5 text-xs text-fg/70">
        {provider.phone ?? <span className="text-fg-subtle">-</span>}
      </TableCell>
      <TableCell className="py-1.5 text-xs text-fg/70">
        {provider.user_id ? "Linked" : "None"}
      </TableCell>
      <TableCell className="py-1.5 text-right">
        <div className="flex items-center justify-end gap-0.5 opacity-0 transition-opacity focus-within:opacity-100 group-hover:opacity-100">
          <Link
            to="/providers/$providerId"
            params={{ providerId: provider.id }}
            aria-label={`Open ${provider.display_name}`}
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
                aria-label={`More actions for ${provider.display_name}`}
                className="size-7 p-0 text-fg/65"
              >
                <MoreHorizontal className="size-4" />
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem asChild>
                <Link to="/providers/$providerId" params={{ providerId: provider.id }}>
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
