import { useState } from "react"

import { useQueries, useQueryClient } from "@tanstack/react-query"
import { createFileRoute, useNavigate, useSearch } from "@tanstack/react-router"
import { Plus, Tags } from "lucide-react"

import {
  type ProviderAlias,
  providerAliasesApi,
  type ProviderAliasListParams,
} from "@/api/endpoints/provider-aliases"
import { providersApi } from "@/api/endpoints/providers"
import { EmptyState } from "@/components/common/EmptyState"
import { EntityListView, type ListColumn } from "@/components/common/EntityListView"
import { FilterBar, FilterChip, FilterTrigger } from "@/components/common/FilterBar"
import { PageShell } from "@/components/common/PageShell"
import { ROW_BORDER } from "@/components/common/tableStyles"
import { AliasQueueDialog } from "@/components/providers/AliasQueueDialog"
import { AliasResolveDialog } from "@/components/providers/AliasResolveDialog"
import { ProviderSectionTabs } from "@/components/providers/ProviderSectionTabs"
import { ReasonDialog } from "@/components/providers/ReasonDialog"
import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import { TableCell, TableRow } from "@/components/ui/table"
import { useToast } from "@/contexts/ToastContext"
import { useCurrentRole } from "@/hooks/useCanWrite"
import { useListPage } from "@/hooks/useListPage"
import { normalizeErrorMessage } from "@/lib/errors"
import { useEntityList } from "@/lib/queries"
import { queryKeys } from "@/lib/query-keys"
import { enumOptions, enumParam, listSearchSchema } from "@/lib/search-params"
import { useTenantStore } from "@/store/slices/tenantSlice"
import { AliasResolutionState, TenantRole } from "@/types/enums"

/**
 * Aliases are keyed by source system, and the two importers do not share a
 * namespace: resolving a name under one does nothing for the other. Session
 * import reads `activity-log-workbook`; staging a practitioner workbook queues
 * its own names under `practitioners-orgs-workbook` automatically.
 */
const SOURCE_SYSTEMS = {
  "activity-log-workbook": "Activity log",
  "practitioners-orgs-workbook": "Practitioner workbook",
} as const

type SourceSystem = keyof typeof SOURCE_SYSTEMS

const DEFAULT_SOURCE_SYSTEM: SourceSystem = "activity-log-workbook"

const SOURCE_OPTIONS = Object.entries(SOURCE_SYSTEMS).map(([value, label]) => ({
  value,
  label,
}))

const STATE_OPTIONS = enumOptions(AliasResolutionState, "All states")

const STATE_VARIANTS: Record<
  AliasResolutionState,
  "default" | "secondary" | "destructive" | "outline"
> = {
  [AliasResolutionState.UNMAPPED]: "outline",
  [AliasResolutionState.AMBIGUOUS]: "secondary",
  [AliasResolutionState.RESOLVED]: "default",
  [AliasResolutionState.REJECTED]: "destructive",
}

const COLUMNS: ListColumn[] = [
  { header: "Name in source" },
  { header: "Matched as", className: "text-fg/65" },
  { header: "State", className: "text-fg/65" },
  { header: "Practitioner", className: "text-fg/65" },
  { header: "Note", className: "text-fg/65" },
]

export const Route = createFileRoute("/provider-aliases/")({
  component: ProviderAliasesPage,
  validateSearch: listSearchSchema({
    state: enumParam(AliasResolutionState),
    source: enumParam(
      Object.fromEntries(Object.keys(SOURCE_SYSTEMS).map((key) => [key, key])) as Record<
        SourceSystem,
        SourceSystem
      >,
    ),
  }),
})

function ProviderAliasesPage() {
  const searchParams = useSearch({ from: "/provider-aliases/" })
  const navigate = useNavigate({ from: "/provider-aliases/" })
  const list = useListPage({ searchParams, navigate })
  const tenantId = useTenantStore((state) => state.currentTenantId)
  const isAdmin = useCurrentRole() === TenantRole.ADMIN
  const toast = useToast()
  const queryClient = useQueryClient()

  const [resolving, setResolving] = useState<ProviderAlias | null>(null)
  const [rejecting, setRejecting] = useState<ProviderAlias | null>(null)
  const sourceSystem: SourceSystem = searchParams.source ?? DEFAULT_SOURCE_SYSTEM

  const query = useEntityList<ProviderAlias, ProviderAliasListParams>({
    resource: "provider-aliases",
    params: {
      tenant_id: tenantId ?? "",
      source_system: sourceSystem,
      state: searchParams.state,
      page: list.page,
      limit: list.limit,
    },
    listFn: providerAliasesApi.list,
    enabled: Boolean(tenantId),
  })

  const items = query.data?.items ?? []
  const names = useProviderNames(items)

  const refresh = () => queryClient.invalidateQueries({ queryKey: ["provider-aliases"] })

  /**
   * Every write shares one shape: act, report, refresh. A failed write leaves
   * its dialog open so the input is not lost.
   */
  const run = async (action: () => Promise<unknown>, success: string, failure: string) => {
    if (!tenantId) return
    try {
      await action()
      toast.showSuccess(success)
      await refresh()
      setResolving(null)
      setRejecting(null)
      list.setAddOpen(false)
    } catch (error) {
      toast.showError(normalizeErrorMessage(error, failure))
    }
  }

  return (
    <PageShell
      icon={Tags}
      trail={[{ label: "Providers" }]}
      title="Name aliases"
      actions={
        isAdmin ? (
          <Button
            size="sm"
            className="h-7 gap-1.5 rounded-none px-2.5"
            onClick={() => list.setAddOpen(true)}
          >
            <Plus className="size-3.5" />
            Queue a name
          </Button>
        ) : null
      }
    >
      <ProviderSectionTabs />

      <p className="border-b border-fg/10 px-3 py-2 text-xs leading-relaxed text-fg-muted">
        How each spelling in the {SOURCE_SYSTEMS[sourceSystem]} import is reconciled to a
        practitioner. Import reads these decisions and never makes one, so a name left unmapped
        holds its rows instead of guessing. The two source systems are separate namespaces:
        resolving a name here does nothing for the other. Accreditation and panel status are not
        consulted, because a past session may name someone no longer eligible for new work.
      </p>

      <FilterBar>
        {searchParams.state ? (
          <FilterChip
            label={`State: ${searchParams.state}`}
            onRemove={() => list.setFilter("state", undefined)}
          />
        ) : null}
        <FilterTrigger
          label="All states"
          value={searchParams.state ?? "all"}
          options={STATE_OPTIONS}
          onChange={(value) => list.setFilter("state", value === "all" ? undefined : value)}
        />
        <FilterTrigger
          label="Source"
          value={sourceSystem}
          options={SOURCE_OPTIONS}
          onChange={(value) => list.setFilter("source", value)}
        />
      </FilterBar>

      <AliasQueueDialog
        sourceSystem={SOURCE_SYSTEMS[sourceSystem]}
        open={list.addOpen}
        onOpenChange={list.setAddOpen}
        onConfirm={(sourceValue) =>
          run(
            () =>
              providerAliasesApi.create(tenantId!, {
                source_system: sourceSystem,
                source_value: sourceValue,
              }),
            "Name queued for review",
            "Could not queue the name",
          )
        }
      />

      <AliasResolveDialog
        alias={resolving}
        open={resolving !== null}
        onOpenChange={(open) => !open && setResolving(null)}
        onConfirm={(providerId) =>
          run(
            () => providerAliasesApi.resolve(tenantId!, resolving!.id, providerId),
            "Practitioner named",
            "Could not resolve the alias",
          )
        }
      />

      <ReasonDialog
        open={rejecting !== null}
        onOpenChange={(open) => !open && setRejecting(null)}
        title="Not a practitioner"
        description={`Record that ${rejecting?.source_value ?? "this value"} does not name a practitioner. Rows using it stay held.`}
        confirmLabel="Reject"
        onConfirm={(note) =>
          run(
            () => providerAliasesApi.reject(tenantId!, rejecting!.id, note),
            "Alias rejected",
            "Could not reject the alias",
          )
        }
      />

      <EntityListView
        columns={COLUMNS}
        items={items}
        selectable={false}
        rowKey={(row) => row.id}
        renderRow={(row) => (
          <AliasRow
            alias={row}
            providerName={row.provider_id ? names[row.provider_id] : undefined}
            onResolve={isAdmin ? () => setResolving(row) : undefined}
            onReject={isAdmin ? () => setRejecting(row) : undefined}
          />
        )}
        loading={query.isPending && Boolean(tenantId)}
        error={
          !tenantId
            ? "No tenant selected."
            : query.isError
              ? normalizeErrorMessage(query.error, "Failed to load aliases")
              : null
        }
        onRetry={() => void query.refetch()}
        empty={
          <EmptyState
            icon={Tags}
            title={searchParams.state ? "No aliases in this state" : "No names queued yet"}
            description={
              searchParams.state
                ? "Try a different state, or clear the filter."
                : "Names reach this queue when somebody adds them or the seeding script runs. Until a name is here, an import cannot be told who it means."
            }
            action={
              isAdmin && !searchParams.state ? (
                <Button size="sm" className="rounded-none" onClick={() => list.setAddOpen(true)}>
                  Queue a name
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
      />
    </PageShell>
  )
}

/** Resolve the practitioner ids on this page to display names, once each. */
function useProviderNames(aliases: ProviderAlias[]): Record<string, string> {
  const ids = [...new Set(aliases.map((a) => a.provider_id).filter((id): id is string => !!id))]
  const results = useQueries({
    queries: ids.map((id) => ({
      queryKey: queryKeys.providers.detail(id),
      queryFn: () => providersApi.getById(id),
      staleTime: 5 * 60_000,
    })),
  })
  return Object.fromEntries(ids.map((id, index) => [id, results[index]?.data?.display_name ?? id]))
}

function AliasRow({
  alias,
  providerName,
  onResolve,
  onReject,
}: {
  alias: ProviderAlias
  providerName?: string
  onResolve?: () => void
  onReject?: () => void
}) {
  const state = alias.state as AliasResolutionState
  const resolved = state === AliasResolutionState.RESOLVED
  const candidates = alias.candidate_provider_ids.length

  return (
    <TableRow className={ROW_BORDER}>
      <TableCell className="px-3 py-2 text-sm font-medium text-fg">{alias.source_value}</TableCell>
      <TableCell className="px-3 py-2 text-xs text-fg-muted">{alias.normalized_value}</TableCell>
      <TableCell className="px-3 py-2">
        <Badge variant={STATE_VARIANTS[state]} size="sm">
          {state}
        </Badge>
        {candidates > 0 && !resolved ? (
          <span className="ml-1.5 text-xs text-fg-muted">
            {candidates} candidate{candidates === 1 ? "" : "s"}
          </span>
        ) : null}
      </TableCell>
      <TableCell className="px-3 py-2 text-xs text-fg/80">{providerName ?? "-"}</TableCell>
      <TableCell className="max-w-48 truncate px-3 py-2 text-xs text-fg-muted">
        {alias.review_note ?? "-"}
      </TableCell>
      <TableCell className="px-3 py-2 text-right">
        <div className="flex justify-end gap-1">
          {onResolve ? (
            <Button variant="link" size="sm" className="h-auto px-0 text-xs" onClick={onResolve}>
              {resolved ? "Reassign" : "Resolve"}
            </Button>
          ) : null}
          {onReject && state !== AliasResolutionState.REJECTED ? (
            <Button
              variant="link"
              size="sm"
              className="h-auto px-0 text-xs text-fg-muted"
              onClick={onReject}
            >
              Reject
            </Button>
          ) : null}
        </div>
      </TableCell>
    </TableRow>
  )
}
