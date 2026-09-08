import { useCallback, useEffect, useMemo, useState } from "react"

import { AlertTriangle, Check } from "lucide-react"

import { diagnosesApi, type DiagnosisAlias } from "@/api/endpoints/diagnoses"
import { ErrorState } from "@/components/common/ErrorState"
import { Button } from "@/components/ui/button"
import { normalizeErrorMessage } from "@/lib/errors"
import type { DiagnosisTree } from "@/types/entities"

/**
 * Review queue for legacy spellings whose mapping nobody has signed off.
 *
 * The alias table decides what a legacy session is counted as. Four mappings
 * were loaded as `inferred` so the import could proceed, on the understanding
 * that a clinical owner would check them. Without a surface, "listable for
 * review" means running SQL, so in practice they would never be reviewed.
 *
 * Confirming is the only action offered. Correcting a mapping means choosing a
 * different taxonomy row, which is the form sheet's job, and getting it wrong
 * silently is worse than leaving it flagged.
 */
export function AliasReviewPanel({ tree }: { tree: DiagnosisTree | null }) {
  const [aliases, setAliases] = useState<DiagnosisAlias[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [busy, setBusy] = useState<string | null>(null)

  const load = useCallback(async () => {
    setError(null)
    try {
      setAliases(await diagnosesApi.listAliases("inferred"))
    } catch (err) {
      setError(normalizeErrorMessage(err, "Could not load the alias review queue."))
    }
  }, [])

  useEffect(() => {
    void load()
  }, [load])

  const labels = useMemo(() => {
    const byId = new Map<string, string>()
    for (const type of tree?.types ?? []) {
      byId.set(type.id, type.name)
      for (const diagnosis of type.diagnoses) {
        byId.set(diagnosis.id, `${type.name} / ${diagnosis.name}`)
      }
    }
    return byId
  }, [tree])

  const confirm = async (alias: DiagnosisAlias) => {
    setBusy(alias.id)
    try {
      await diagnosesApi.upsertAlias({
        raw_value: alias.raw_value,
        diagnosis_type_id: alias.diagnosis_type_id,
        diagnosis_id: alias.diagnosis_id,
        source: alias.source,
        confidence: "confirmed",
      })
      await load()
    } catch (err) {
      setError(normalizeErrorMessage(err, "Could not confirm this mapping."))
    } finally {
      setBusy(null)
    }
  }

  if (error) return <ErrorState message={error} onRetry={() => void load()} />
  if (aliases === null) return null
  if (aliases.length === 0) return null

  return (
    <section className="border-b border-fg/10" aria-labelledby="alias-review-heading">
      <div className="flex items-center gap-2 bg-warning/10 px-3 py-2">
        <AlertTriangle className="size-3.5 text-warning-fg" aria-hidden />
        <h2 id="alias-review-heading" className="text-sm font-medium text-fg">
          {aliases.length} legacy {aliases.length === 1 ? "spelling" : "spellings"} awaiting review
        </h2>
        <p className="text-xs text-fg-muted">
          Imported under an inferred mapping. Confirm each one, or correct it first.
        </p>
      </div>
      <ul>
        {aliases.map((alias) => (
          <li key={alias.id} className="flex items-center gap-3 border-t border-fg/10 px-3 py-2">
            <span className="min-w-0 flex-1 truncate text-sm text-fg" title={alias.raw_value}>
              {alias.raw_value}
            </span>
            <span className="text-xs text-fg-muted">
              {labels.get(alias.diagnosis_id ?? alias.diagnosis_type_id) ?? alias.diagnosis_type_id}
            </span>
            <Button
              size="sm"
              variant="outline"
              className="h-7 gap-1.5 px-2.5"
              disabled={busy === alias.id}
              onClick={() => void confirm(alias)}
            >
              <Check className="size-3.5" />
              {busy === alias.id ? "Confirming…" : "Confirm"}
            </Button>
          </li>
        ))}
      </ul>
    </section>
  )
}
