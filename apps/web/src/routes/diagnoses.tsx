import { useCallback, useEffect, useMemo, useState } from "react"

import { createFileRoute } from "@tanstack/react-router"
import {
  ChevronDown,
  ChevronRight,
  ChevronUp,
  Eye,
  EyeOff,
  Plus,
  SquarePen,
  Stethoscope,
} from "lucide-react"

import {
  diagnosesApi,
  type DiagnosisCapabilities,
  type DiagnosisOverlay,
} from "@/api/endpoints/diagnoses"
import { AuthedLayout } from "@/components/common/AuthedLayout"
import { EmptyState } from "@/components/common/EmptyState"
import { ErrorState } from "@/components/common/ErrorState"
import { FilterBar, FilterSearch } from "@/components/common/FilterBar"
import { IconButton } from "@/components/common/IconButton"
import { PageShell } from "@/components/common/PageShell"
import { TableSkeleton } from "@/components/common/PageSkeletons"
import { ROW_BORDER, STICKY_TABLE_HEAD } from "@/components/common/tableStyles"
import { DiagnosisFormSheet } from "@/components/DiagnosisFormSheet"
import { Button } from "@/components/ui/button"
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table"
import { normalizeErrorMessage } from "@/lib/errors"
import { cn } from "@/lib/utils"
import type { Diagnosis, DiagnosisTree, DiagnosisType } from "@/types/entities"

export const Route = createFileRoute("/diagnoses")({
  component: DiagnosesPage,
})

type TypeWithDiagnoses = DiagnosisType & { diagnoses: Diagnosis[] }

type OverlayKey = string
const keyOf = (typeId: string, diagnosisId: string | null): OverlayKey =>
  `${typeId}::${diagnosisId ?? ""}`

function useTaxonomy() {
  const [tree, setTree] = useState<DiagnosisTree | null>(null)
  const [overlay, setOverlay] = useState<Map<OverlayKey, DiagnosisOverlay>>(new Map())
  const [caps, setCaps] = useState<DiagnosisCapabilities | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(true)

  const load = useCallback(async () => {
    setLoading(true)
    setError(null)
    try {
      const [t, c] = await Promise.all([diagnosesApi.getTree(), diagnosesApi.capabilities()])
      setTree(t)
      setCaps(c)
      if (c.can_manage_overlay) {
        const rows = await diagnosesApi.listOverlay()
        setOverlay(new Map(rows.map((r) => [keyOf(r.diagnosis_type_id, r.diagnosis_id), r])))
      }
    } catch (err) {
      setError(normalizeErrorMessage(err, "Could not load the diagnosis taxonomy."))
    } finally {
      setLoading(false)
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  return { tree, overlay, caps, error, loading, reload: load }
}

/** Types whose own name matches, plus types holding a matching diagnosis. */
function filterTypes(tree: DiagnosisTree | null, search: string): TypeWithDiagnoses[] {
  const all = tree?.types ?? []
  const q = search.trim().toLowerCase()
  if (!q) return all
  return all
    .map((t) => ({ ...t, diagnoses: t.diagnoses.filter((d) => d.name.toLowerCase().includes(q)) }))
    .filter((t) => t.name.toLowerCase().includes(q) || t.diagnoses.length > 0)
}

function DiagnosesPage() {
  const { tree, overlay, caps, error, loading, reload } = useTaxonomy()
  const [search, setSearch] = useState("")
  const [selectedId, setSelectedId] = useState<string | null>(null)
  const [openDiagnosisId, setOpenDiagnosisId] = useState<string | null>(null)
  const [sheet, setSheet] = useState<{
    target: { kind: "type" } | { kind: "diagnosis"; typeId: string }
    editing: DiagnosisType | Diagnosis | null
  } | null>(null)

  const canManage = caps?.can_manage_taxonomy ?? false
  const canOverlay = caps?.can_manage_overlay ?? false
  const types = useMemo(() => filterTypes(tree, search), [tree, search])
  // Falls back to the first row, so the panel is never blank while the list has
  // something in it, including after a search removes the previous selection.
  const selected = types.find((t) => t.id === selectedId) ?? types[0] ?? null

  const setVisible = async (typeId: string, diagnosisId: string | null, isEnabled: boolean) => {
    await diagnosesApi.setOverlay({
      diagnosis_type_id: typeId,
      diagnosis_id: diagnosisId,
      is_enabled: isEnabled,
    })
    await reload()
  }

  const isHidden = (typeId: string, diagnosisId: string | null) =>
    overlay.get(keyOf(typeId, diagnosisId))?.is_enabled === false

  const labelOf = (typeId: string, diagnosisId: string | null) =>
    overlay.get(keyOf(typeId, diagnosisId))?.local_label ?? null

  /**
   * Move a row one place within its siblings.
   *
   * Every sibling is written, not just the two that swap. A null sort_order
   * means "inherit the shared order", so a partial write would leave the moved
   * row tied with rows that still inherit, and the tie then breaks on name
   * rather than on what the user asked for. Writing the whole list makes the
   * tenant's order explicit and independent of the shared one.
   */
  const move = async (
    siblings: ReadonlyArray<{ id: string }>,
    index: number,
    direction: -1 | 1,
    typeId: string,
    asDiagnosis: boolean,
  ) => {
    const swapIndex = index + direction
    if (swapIndex < 0 || swapIndex >= siblings.length) return
    const next = [...siblings]
    ;[next[index], next[swapIndex]] = [next[swapIndex], next[index]]
    await Promise.all(
      next.map((row, position) =>
        diagnosesApi.setOverlay({
          diagnosis_type_id: asDiagnosis ? typeId : row.id,
          diagnosis_id: asDiagnosis ? row.id : null,
          sort_order: position,
        }),
      ),
    )
    await reload()
  }

  const counts = useMemo(() => {
    const t = tree?.types ?? []
    return { types: t.length, diagnoses: t.reduce((n, x) => n + x.diagnoses.length, 0) }
  }, [tree])
  // Positions written from a filtered list would not be the real ones.
  const canReorder = canOverlay && !search.trim()

  return (
    <AuthedLayout>
      <PageShell
        icon={Stethoscope}
        breadcrumb="Reference · Diagnoses"
        actions={
          canManage ? (
            <Button
              size="sm"
              className="h-7 gap-1.5 px-2.5"
              onClick={() => setSheet({ target: { kind: "type" }, editing: null })}
            >
              <Plus className="size-3.5" />
              Add type
            </Button>
          ) : null
        }
      >
        <FilterBar>
          <p className="shrink-0 text-xs text-fg-muted">
            {counts.types} types · {counts.diagnoses} diagnoses
            {canManage ? " · shared across all tenants" : ""}
          </p>
          <div className="ml-auto" />
          <FilterSearch
            value={search}
            onChange={setSearch}
            placeholder="Search types and diagnoses"
          />
        </FilterBar>

        {/* Legacy mappings nobody has signed off. Above the taxonomy because it
            is a queue that should empty, not part of browsing it. */}

        {loading ? (
          <div className="p-3">
            <TableSkeleton cols={4} />
          </div>
        ) : error ? (
          <ErrorState message={error} onRetry={() => void reload()} />
        ) : (
          <div className="grid min-h-0 flex-1 grid-cols-12 gap-3 overflow-hidden bg-bg p-3">
            <div className="col-span-12 flex min-h-0 min-w-0 flex-col overflow-hidden border border-fg/10 bg-surface lg:col-span-6">
              {types.length === 0 ? (
                <EmptyState
                  icon={Stethoscope}
                  title="No diagnoses match your search"
                  description="Try a different term."
                />
              ) : (
                <div className="min-h-0 flex-1 overflow-y-auto">
                  <Table className="w-full text-sm" scrollable={false}>
                    <TableHeader className={STICKY_TABLE_HEAD}>
                      <TableRow className={`hover:bg-transparent ${ROW_BORDER}`}>
                        <TableHead>Type</TableHead>
                        <TableHead className="text-fg/65">Code</TableHead>
                        <TableHead className="text-right text-fg/65">Diagnoses</TableHead>
                        <TableHead className="w-32 text-right text-fg/65">
                          <span className="sr-only">Actions</span>
                        </TableHead>
                      </TableRow>
                    </TableHeader>
                    <TableBody>
                      {types.map((type, index) => (
                        <TypeRow
                          key={type.id}
                          type={type}
                          localLabel={labelOf(type.id, null)}
                          hidden={isHidden(type.id, null)}
                          selected={selected?.id === type.id}
                          onSelect={() => setSelectedId(type.id)}
                          canManage={canManage}
                          canOverlay={canOverlay}
                          onEdit={() => setSheet({ target: { kind: "type" }, editing: type })}
                          onSetVisible={(v) => void setVisible(type.id, null, v)}
                          onMove={
                            canReorder
                              ? (direction) => void move(types, index, direction, type.id, false)
                              : undefined
                          }
                          isFirst={index === 0}
                          isLast={index === types.length - 1}
                        />
                      ))}
                    </TableBody>
                  </Table>
                </div>
              )}
            </div>

            <div className="col-span-12 flex min-h-0 min-w-0 flex-col lg:col-span-6">
              {selected ? (
                <TypeDetailsCard
                  type={selected}
                  localLabel={labelOf(selected.id, null)}
                  canManage={canManage}
                  canOverlay={canOverlay}
                  onAddChild={() =>
                    setSheet({ target: { kind: "diagnosis", typeId: selected.id }, editing: null })
                  }
                  renderChild={(d, index) => (
                    <DiagnosisRow
                      key={d.id}
                      open={openDiagnosisId === d.id}
                      onToggle={() => setOpenDiagnosisId((prev) => (prev === d.id ? null : d.id))}
                      diagnosis={d}
                      localLabel={labelOf(selected.id, d.id)}
                      hidden={isHidden(selected.id, d.id)}
                      canManage={canManage}
                      canOverlay={canOverlay}
                      onEdit={() =>
                        setSheet({
                          target: { kind: "diagnosis", typeId: selected.id },
                          editing: d,
                        })
                      }
                      onSetVisible={(v) => void setVisible(selected.id, d.id, v)}
                      onMove={
                        canReorder
                          ? (direction) =>
                              void move(selected.diagnoses, index, direction, selected.id, true)
                          : undefined
                      }
                      isFirst={index === 0}
                      isLast={index === selected.diagnoses.length - 1}
                    />
                  )}
                />
              ) : (
                <DetailsPlaceholder />
              )}
            </div>
          </div>
        )}
      </PageShell>

      {sheet && (
        <DiagnosisFormSheet
          open
          onOpenChange={(o) => !o && setSheet(null)}
          target={sheet.target}
          editing={sheet.editing}
          onSaved={() => void reload()}
        />
      )}
    </AuthedLayout>
  )
}

function TypeRow({
  type,
  localLabel,
  hidden,
  selected,
  onSelect,
  canManage,
  canOverlay,
  onEdit,
  onSetVisible,
  onMove,
  isFirst,
  isLast,
}: {
  type: TypeWithDiagnoses
  localLabel: string | null
  hidden: boolean
  selected: boolean
  onSelect: () => void
  canManage: boolean
  canOverlay: boolean
  onEdit: () => void
  onSetVisible: (visible: boolean) => void
  /** Omitted when the caller may not reorder, or while a search is filtering. */
  onMove?: (direction: -1 | 1) => void
  isFirst: boolean
  isLast: boolean
}) {
  return (
    <TableRow
      onClick={onSelect}
      className={cn(
        "group h-9 cursor-pointer",
        ROW_BORDER,
        hidden && "opacity-50",
        selected && "bg-primary/5 hover:bg-primary/5",
      )}
    >
      <TableCell>
        <span className={cn("font-medium", selected ? "text-primary" : "text-fg")}>
          {localLabel ?? type.name}
        </span>
        {localLabel && <RelabelBadge original={type.name} />}
      </TableCell>
      <TableCell className="text-xs text-fg/65">{type.code}</TableCell>
      <TableCell className="text-right tabular-nums text-xs text-fg/65">
        {type.diagnoses.length}
      </TableCell>
      <TableCell className="text-right">
        <RowActions
          hidden={hidden}
          canManage={canManage}
          canOverlay={canOverlay}
          onEdit={onEdit}
          onSetVisible={onSetVisible}
          onMove={onMove}
          isFirst={isFirst}
          isLast={isLast}
          label={type.name}
        />
      </TableCell>
    </TableRow>
  )
}

/** The selected type: what it means, and every diagnosis filed under it. */
function TypeDetailsCard({
  type,
  localLabel,
  canManage,
  canOverlay,
  onAddChild,
  renderChild,
}: {
  type: TypeWithDiagnoses
  localLabel: string | null
  canManage: boolean
  canOverlay: boolean
  onAddChild: () => void
  renderChild: (d: Diagnosis, index: number) => React.ReactNode
}) {
  return (
    <div className="flex min-h-0 flex-col overflow-hidden border border-fg/10 bg-surface">
      <header className="flex items-start gap-2.5 border-b border-fg/10 px-3 py-2.5">
        <span
          aria-hidden
          className="grid size-7 shrink-0 place-items-center bg-primary/10 text-primary"
        >
          <Stethoscope className="size-3.5" />
        </span>
        <div className="min-w-0 flex-1">
          <h3 className="truncate text-sm font-semibold leading-tight text-fg">
            {localLabel ?? type.name}
          </h3>
          <p className="mt-0.5 text-[11px] text-fg-muted">
            {type.code} · {type.diagnoses.length} diagnoses
          </p>
        </div>
        {canManage && <IconButton label="Add diagnosis" icon={Plus} onClick={onAddChild} />}
      </header>

      <div className="flex min-h-0 flex-1 flex-col gap-3 overflow-y-auto overscroll-contain p-3">
        {type.description ? <p className="text-xs text-fg/70">{type.description}</p> : null}
        {type.diagnoses.length === 0 ? (
          <p className="text-sm text-fg-muted">Nothing filed under this type yet.</p>
        ) : (
          <ul className="divide-y divide-fg/10">
            {type.diagnoses.map((d, index) => renderChild(d, index))}
          </ul>
        )}
        {!canManage && !canOverlay ? (
          <p className="mt-auto border-t border-fg/10 pt-2.5 text-[11px] text-fg-muted">
            This taxonomy is shared. Ask a platform administrator to change it.
          </p>
        ) : null}
      </div>
    </div>
  )
}

function DiagnosisRow({
  diagnosis,
  localLabel,
  hidden,
  open,
  onToggle,
  canManage,
  canOverlay,
  onEdit,
  onSetVisible,
  onMove,
  isFirst,
  isLast,
}: {
  diagnosis: Diagnosis
  localLabel: string | null
  hidden: boolean
  open: boolean
  onToggle: () => void
  canManage: boolean
  canOverlay: boolean
  onEdit: () => void
  onSetVisible: (visible: boolean) => void
  onMove?: (direction: -1 | 1) => void
  isFirst: boolean
  isLast: boolean
}) {
  const hasDescription = Boolean(diagnosis.description)
  const panelId = `dx-desc-${diagnosis.id}`
  const label = (
    <>
      {localLabel ?? diagnosis.name}
      {localLabel && <RelabelBadge original={diagnosis.name} />}
      <span className="ml-1.5 text-xs text-fg/65">{diagnosis.code}</span>
    </>
  )

  return (
    <li className={cn("py-2", hidden && "opacity-50")}>
      <div className="flex items-center gap-2">
        {hasDescription ? (
          <Button
            type="button"
            variant="ghost"
            onClick={onToggle}
            aria-expanded={open}
            aria-controls={panelId}
            className="h-auto min-w-0 flex-1 justify-start gap-1.5 rounded-none px-0 py-0 text-left text-sm font-normal text-fg hover:bg-transparent hover:text-primary"
          >
            <ChevronRight
              aria-hidden
              className={cn(
                "size-3.5 shrink-0 text-fg-muted transition-transform",
                open && "rotate-90",
              )}
            />
            <span className="min-w-0 truncate">{label}</span>
          </Button>
        ) : (
          <span className="min-w-0 flex-1 pl-5 text-sm text-fg">{label}</span>
        )}
        <RowActions
          hidden={hidden}
          canManage={canManage}
          canOverlay={canOverlay}
          onEdit={onEdit}
          onSetVisible={onSetVisible}
          onMove={onMove}
          isFirst={isFirst}
          isLast={isLast}
          label={diagnosis.name}
        />
      </div>
      {hasDescription && open ? (
        <p id={panelId} className="mt-1 pl-5 text-xs text-fg-muted">
          {diagnosis.description}
        </p>
      ) : null}
    </li>
  )
}

function DetailsPlaceholder() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-1 border border-dashed border-fg/15 p-8 text-center">
      <div className="mb-2 grid size-9 place-items-center bg-primary/10">
        <Stethoscope className="size-4 text-primary" />
      </div>
      <h3 className="text-sm font-semibold text-fg">Pick a type</h3>
      <p className="max-w-[24ch] text-xs text-fg/60">
        Select a row to read its definition and the diagnoses under it.
      </p>
    </div>
  )
}

function RelabelBadge({ original }: { original: string }) {
  return (
    <span className="ml-2 border border-info/40 px-1.5 py-0.5 text-[11px] text-info-fg">
      renamed from {original}
    </span>
  )
}

function RowActions({
  hidden,
  canManage,
  canOverlay,
  onEdit,
  onSetVisible,
  onMove,
  isFirst,
  isLast,
  label,
}: {
  hidden: boolean
  canManage: boolean
  canOverlay: boolean
  onEdit: () => void
  onSetVisible: (visible: boolean) => void
  onMove?: (direction: -1 | 1) => void
  isFirst?: boolean
  isLast?: boolean
  label?: string
}) {
  return (
    <div
      className="flex items-center justify-end gap-0.5"
      // The row is a select control; its buttons are not.
      onClick={(event) => event.stopPropagation()}
    >
      {onMove && (
        <>
          <IconButton
            label={`Move ${label ?? "row"} up`}
            icon={ChevronUp}
            disabled={isFirst}
            onClick={() => onMove(-1)}
          />
          <IconButton
            label={`Move ${label ?? "row"} down`}
            icon={ChevronDown}
            disabled={isLast}
            onClick={() => onMove(1)}
          />
        </>
      )}
      {canOverlay && (
        <IconButton
          label={hidden ? "Show for this tenant" : "Hide for this tenant"}
          icon={hidden ? EyeOff : Eye}
          onClick={() => onSetVisible(hidden)}
        />
      )}
      {canManage && <IconButton label="Edit shared row" icon={SquarePen} onClick={onEdit} />}
    </div>
  )
}
