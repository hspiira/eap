import { useQuery } from "@tanstack/react-query"
import { History } from "lucide-react"

import { auditApi } from "@/api/endpoints/audit"
import { EmptyState } from "@/components/common/EmptyState"
import { formatDateTime } from "@/lib/format"
import type { FieldChange } from "@/types/entities"
import { getStatusLabel } from "@/utils/statusColors"

/**
 * Every recorded change to one record, newest first.
 *
 * Two requests rather than one: the log carries when and who, the entity
 * changes carry which fields, and they are joined here on the audit log id.
 * Field values are not shown. For a clinical resource the audit feed redacts
 * them, and for everything else the field name is the auditable fact a reader
 * needs; the values belong on the record itself.
 */
export function EntityActivityPanel({
  resourceType,
  resourceId,
  emptyDescription = "Changes appear here once they happen.",
}: {
  resourceType: string
  resourceId: string
  emptyDescription?: string
}) {
  const logs = useQuery({
    queryKey: ["audit", "logs", resourceType, resourceId],
    queryFn: () => auditApi.getEntityHistory(resourceType, resourceId),
  })
  const changes = useQuery({
    queryKey: ["audit", "changes", resourceType, resourceId],
    queryFn: () => auditApi.getEntityFieldChanges(resourceType, resourceId),
  })

  if (logs.isPending) return <p className="text-sm text-fg-muted">Loading activity…</p>
  if (logs.isError) {
    return (
      <p className="text-sm text-danger-fg" role="alert">
        Could not load the activity trail.
      </p>
    )
  }

  const entries = logs.data ?? []
  if (entries.length === 0) {
    return <EmptyState icon={History} title="No recorded activity" description={emptyDescription} />
  }

  const fieldsByLog = new Map<string, string[]>()
  for (const change of changes.data ?? []) {
    const names = change.field_changes.map((field: FieldChange) => field.field_name)
    fieldsByLog.set(change.audit_log_id, [
      ...(fieldsByLog.get(change.audit_log_id) ?? []),
      ...names,
    ])
  }

  return (
    <ol className="space-y-0">
      {entries.map((entry) => {
        const fields = fieldsByLog.get(entry.id) ?? []
        return (
          <li
            key={entry.id}
            className="flex items-baseline gap-3 border-b border-fg/10 py-2 last:border-b-0"
          >
            <span className="w-40 shrink-0 text-xs tabular-nums text-fg-muted">
              {formatDateTime(entry.occurred_at)}
            </span>
            <span className="min-w-0 flex-1">
              <span className="block text-sm text-fg">
                {entry.description || getStatusLabel(entry.action_type)}
              </span>
              {fields.length > 0 ? (
                <span className="block text-xs text-fg-muted">{fields.join(", ")}</span>
              ) : null}
            </span>
          </li>
        )
      })}
    </ol>
  )
}
