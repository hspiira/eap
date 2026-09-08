import { useQuery } from "@tanstack/react-query"
import { History } from "lucide-react"

import { auditApi } from "@/api/endpoints/audit"
import { EmptyState } from "@/components/common/EmptyState"
import { formatDateTime } from "@/lib/format"
import type { AuditLog } from "@/types/entities"
import { getStatusLabel } from "@/utils/statusColors"

/** The changed fields an audit row names, without their values. */
function changedFields(entry: AuditLog): string[] {
  const changes = entry.changes
  if (!changes || typeof changes !== "object") return []
  if (Array.isArray(changes)) {
    return changes
      .map((change) =>
        change && typeof change === "object" && "field_name" in change
          ? String((change as { field_name: unknown }).field_name)
          : null,
      )
      .filter((field): field is string => Boolean(field))
  }
  return Object.keys(changes)
}

/**
 * Every recorded change to this practitioner.
 *
 * Each lifecycle command carries a reason, which is what makes this readable as
 * a history rather than a list of timestamps. A practitioner is not clinical
 * data, so values are not redacted here.
 */
export function ProviderActivityPanel({ providerId }: { providerId: string }) {
  const query = useQuery({
    queryKey: ["audit", "Provider", providerId],
    queryFn: () => auditApi.getEntityHistory("Provider", providerId),
  })

  if (query.isPending) return <p className="text-sm text-fg-muted">Loading activity…</p>
  if (query.isError) {
    return (
      <p className="text-sm text-danger-fg" role="alert">
        Could not load the activity trail.
      </p>
    )
  }

  const entries = query.data ?? []
  if (entries.length === 0) {
    return (
      <EmptyState
        icon={History}
        title="No recorded activity"
        description="Profile edits and lifecycle commands appear here once they happen."
      />
    )
  }

  return (
    <ol className="space-y-0">
      {entries.map((entry) => {
        const fields = changedFields(entry)
        return (
          <li
            key={entry.id}
            className="flex items-baseline gap-3 border-b border-fg/10 py-2 last:border-b-0"
          >
            <span className="w-40 shrink-0 text-xs tabular-nums text-fg-muted">
              {formatDateTime(entry.created_at)}
            </span>
            <span className="min-w-0 flex-1">
              <span className="block text-sm text-fg">{getStatusLabel(entry.action_type)}</span>
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
