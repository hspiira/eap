import { useCallback, useEffect, useMemo, useState } from "react"

import { createFileRoute } from "@tanstack/react-router"
import { ChevronDown, ChevronRight, Eye, EyeOff, Pencil, Plus, Stethoscope } from "lucide-react"

import {
  diagnosesApi,
  type DiagnosisCapabilities,
  type DiagnosisOverlay,
} from "@/api/endpoints/diagnoses"
import { AppLayout } from "@/components/AppLayout"
import { EmptyState } from "@/components/common/EmptyState"
import { ErrorState } from "@/components/common/ErrorState"
import { IconButton } from "@/components/common/IconButton"
import { PageShell } from "@/components/common/PageShell"
import { TableSkeleton } from "@/components/common/PageSkeletons"
import { DiagnosisFormSheet } from "@/components/DiagnosisFormSheet"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { normalizeErrorMessage } from "@/lib/errors"
import type { Diagnosis, DiagnosisTree, DiagnosisType } from "@/types/entities"

export const Route = createFileRoute("/diagnoses")({
  component: DiagnosesPage,
})

const ROW = "border-b border-safe/20"

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

function DiagnosesPage() {
  const { tree, overlay, caps, error, loading, reload } = useTaxonomy()
  const [expanded, setExpanded] = useState<Set<string>>(new Set())
  const [search, setSearch] = useState("")
  const [sheet, setSheet] = useState<{
    target: { kind: "type" } | { kind: "diagnosis"; typeId: string }
    editing: DiagnosisType | Diagnosis | null
  } | null>(null)

  const canManage = caps?.can_manage_taxonomy ?? false
  const canOverlay = caps?.can_manage_overlay ?? false

  const types = useMemo(() => {
    const all = tree?.types ?? []
    const q = search.trim().toLowerCase()
    if (!q) return all
    return all
      .map((t) => ({
        ...t,
        diagnoses: t.diagnoses.filter((d) => d.name.toLowerCase().includes(q)),
      }))
      .filter((t) => t.name.toLowerCase().includes(q) || t.diagnoses.length > 0)
  }, [tree, search])

  const toggle = (id: string) =>
    setExpanded((prev) => {
      const next = new Set(prev)
      if (next.has(id)) next.delete(id)
      else next.add(id)
      return next
    })

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

  const counts = useMemo(() => {
    const t = tree?.types ?? []
    return { types: t.length, diagnoses: t.reduce((n, x) => n + x.diagnoses.length, 0) }
  }, [tree])

  return (
    <AppLayout>
      <PageShell
        icon={Stethoscope}
        breadcrumb="Reference / Diagnoses"
        title="Diagnoses"
        actions={
          canManage ? (
            <Button
              size="sm"
              className="gap-1.5 rounded-none"
              onClick={() => setSheet({ target: { kind: "type" }, editing: null })}
            >
              <Plus className="size-4" />
              Add type
            </Button>
          ) : null
        }
      >
        <div className="flex items-center justify-between gap-3 border-b border-safe/20 p-4">
          <Input
            className="max-w-sm rounded-none"
            placeholder="Search types and diagnoses"
            value={search}
            onChange={(e) => setSearch(e.target.value)}
          />
          <p className="text-sm text-safe">
            {counts.types} types · {counts.diagnoses} diagnoses
            {canManage ? " · shared across all tenants" : ""}
          </p>
        </div>

        {loading ? (
          <div className="p-5">
            <TableSkeleton cols={4} />
          </div>
        ) : error ? (
          <ErrorState message={error} onRetry={() => void reload()} />
        ) : types.length === 0 ? (
          <EmptyState
            icon={Stethoscope}
            title="No diagnoses match your search"
            description="Try a different term."
          />
        ) : (
          <div>
            {types.map((type) => (
              <TypeRow
                key={type.id}
                type={type}
                expanded={expanded.has(type.id)}
                onToggle={() => toggle(type.id)}
                hidden={isHidden(type.id, null)}
                canManage={canManage}
                canOverlay={canOverlay}
                localLabel={overlay.get(keyOf(type.id, null))?.local_label ?? null}
                onEdit={() => setSheet({ target: { kind: "type" }, editing: type })}
                onAddChild={() =>
                  setSheet({ target: { kind: "diagnosis", typeId: type.id }, editing: null })
                }
                onSetVisible={(v) => void setVisible(type.id, null, v)}
                renderChild={(d) => (
                  <DiagnosisRow
                    key={d.id}
                    diagnosis={d}
                    hidden={isHidden(type.id, d.id)}
                    canManage={canManage}
                    canOverlay={canOverlay}
                    localLabel={overlay.get(keyOf(type.id, d.id))?.local_label ?? null}
                    onEdit={() =>
                      setSheet({ target: { kind: "diagnosis", typeId: type.id }, editing: d })
                    }
                    onSetVisible={(v) => void setVisible(type.id, d.id, v)}
                  />
                )}
              />
            ))}
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
    </AppLayout>
  )
}

interface TypeRowProps {
  type: DiagnosisType & { diagnoses: Diagnosis[] }
  expanded: boolean
  hidden: boolean
  canManage: boolean
  canOverlay: boolean
  localLabel: string | null
  onToggle: () => void
  onEdit: () => void
  onAddChild: () => void
  onSetVisible: (visible: boolean) => void
  renderChild: (d: Diagnosis) => React.ReactNode
}

function TypeRow({
  type,
  expanded,
  hidden,
  canManage,
  canOverlay,
  localLabel,
  onToggle,
  onEdit,
  onAddChild,
  onSetVisible,
  renderChild,
}: TypeRowProps) {
  const Chevron = expanded ? ChevronDown : ChevronRight
  return (
    <div className={ROW}>
      <div className={`flex items-center gap-2 px-4 py-2.5 ${hidden ? "opacity-50" : ""}`}>
        <Button
          variant="ghost"
          onClick={onToggle}
          className="flex h-auto flex-1 items-center justify-start gap-2 rounded-none px-0 text-left font-normal"
        >
          <Chevron className="size-4 text-safe" />
          <span className="font-medium">{localLabel ?? type.name}</span>
          {localLabel && <RelabelBadge original={type.name} />}
          <span className="text-sm text-safe">{type.code}</span>
          <span className="text-sm text-safe">({type.diagnoses.length})</span>
        </Button>
        <RowActions
          hidden={hidden}
          canManage={canManage}
          canOverlay={canOverlay}
          onEdit={onEdit}
          onSetVisible={onSetVisible}
          onAdd={canManage ? onAddChild : undefined}
        />
      </div>
      {expanded && <div className="bg-surface">{type.diagnoses.map(renderChild)}</div>}
    </div>
  )
}

function DiagnosisRow({
  diagnosis,
  hidden,
  canManage,
  canOverlay,
  localLabel,
  onEdit,
  onSetVisible,
}: {
  diagnosis: Diagnosis
  hidden: boolean
  canManage: boolean
  canOverlay: boolean
  localLabel: string | null
  onEdit: () => void
  onSetVisible: (visible: boolean) => void
}) {
  return (
    <div
      className={`flex items-center gap-2 border-t border-safe/10 py-2 pl-12 pr-4 ${
        hidden ? "opacity-50" : ""
      }`}
    >
      <span className="flex-1">
        {localLabel ?? diagnosis.name}
        {localLabel && <RelabelBadge original={diagnosis.name} />}
      </span>
      <span className="text-sm text-safe">{diagnosis.code}</span>
      <RowActions
        hidden={hidden}
        canManage={canManage}
        canOverlay={canOverlay}
        onEdit={onEdit}
        onSetVisible={onSetVisible}
      />
    </div>
  )
}

function RelabelBadge({ original }: { original: string }) {
  return (
    <span className="ml-2 border border-nurturing px-1.5 py-0.5 text-xs text-nurturing">
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
  onAdd,
}: {
  hidden: boolean
  canManage: boolean
  canOverlay: boolean
  onEdit: () => void
  onSetVisible: (visible: boolean) => void
  onAdd?: () => void
}) {
  return (
    <div className="flex items-center gap-1">
      {canOverlay && (
        <IconButton
          label={hidden ? "Show for this tenant" : "Hide for this tenant"}
          icon={hidden ? EyeOff : Eye}
          onClick={() => onSetVisible(hidden)}
        />
      )}
      {canManage && <IconButton label="Edit shared row" icon={Pencil} onClick={onEdit} />}
      {onAdd && <IconButton label="Add diagnosis" icon={Plus} onClick={onAdd} />}
    </div>
  )
}
