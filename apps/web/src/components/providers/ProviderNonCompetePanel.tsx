import { useState } from "react"

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query"

import { nonCompeteClausesApi } from "@/api/endpoints/non-compete-clauses"
import { DetailCard } from "@/components/common/DetailPrimitives"
import { StatusBadge } from "@/components/common/StatusBadge"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useToast } from "@/contexts/ToastContext"
import { normalizeErrorMessage } from "@/lib/errors"
import { entityDetailKey } from "@/lib/queries"
import type { NonCompeteClause } from "@/types/entities"
import { NonCompeteStatus } from "@/types/enums"

/**
 * Non-compete clauses on file for a practitioner.
 *
 * These are recorded but not enforced: no booking is refused on their account.
 */
export function ProviderNonCompetePanel({ providerId }: { providerId: string }) {
  const queryClient = useQueryClient()
  const toast = useToast()

  const list = useQuery({
    queryKey: ["non-compete", "list", providerId],
    queryFn: () => nonCompeteClausesApi.listForProvider(providerId),
    staleTime: 30_000,
  })

  const refetch = () => {
    void queryClient.invalidateQueries({ queryKey: ["non-compete", "list", providerId] })
    void queryClient.invalidateQueries({ queryKey: entityDetailKey("providers", providerId) })
  }

  return (
    <DetailCard title="Non-compete clauses">
      <p className="mb-4 text-sm text-fg-muted">
        Recorded for reference. A clause does not currently restrict a booking, and it is not a
        supplier contract.
      </p>
      <NonCompeteList
        pending={list.isPending}
        error={list.isError ? normalizeErrorMessage(list.error, "Could not load clauses") : null}
        clauses={list.data ?? []}
        onChanged={refetch}
        toast={toast}
      />
    </DetailCard>
  )
}

interface ToastApi {
  showError: (message: string) => void
  showSuccess: (message: string) => void
}

function NonCompeteList({
  pending,
  error,
  clauses,
  onChanged,
  toast,
}: {
  pending: boolean
  error: string | null
  clauses: NonCompeteClause[]
  onChanged: () => void
  toast: ToastApi
}) {
  if (pending) return <p className="text-sm text-fg-muted">Loading non-compete clauses…</p>
  if (error) {
    return (
      <p role="alert" className="text-sm text-danger-fg">
        {error}
      </p>
    )
  }
  if (clauses.length === 0) {
    return <p className="text-sm text-fg-muted">No non-compete clauses on file.</p>
  }
  return (
    <ul className="space-y-3">
      {clauses.map((clause) => (
        <NonCompeteRow key={clause.id} clause={clause} onChanged={onChanged} toast={toast} />
      ))}
    </ul>
  )
}

function NonCompeteRow({
  clause,
  onChanged,
  toast,
}: {
  clause: NonCompeteClause
  onChanged: () => void
  toast: ToastApi
}) {
  const [revokeReason, setRevokeReason] = useState("")
  const [revokeOpen, setRevokeOpen] = useState(false)

  const sign = useMutation({
    mutationFn: () => nonCompeteClausesApi.sign(clause.id, { signed_by: clause.tenant_id }),
    onSuccess: () => {
      toast.showSuccess("Clause signed")
      onChanged()
    },
    onError: (error) => toast.showError(normalizeErrorMessage(error, "Could not sign clause")),
  })

  const revoke = useMutation({
    mutationFn: () => nonCompeteClausesApi.revoke(clause.id, { reason: revokeReason.trim() }),
    onSuccess: () => {
      toast.showSuccess("Clause revoked")
      setRevokeOpen(false)
      setRevokeReason("")
      onChanged()
    },
    onError: (error) => toast.showError(normalizeErrorMessage(error, "Could not revoke clause")),
  })

  return (
    <li className="border border-fg/10 p-3">
      <div className="flex flex-wrap items-baseline justify-between gap-2">
        <p className="text-sm font-semibold text-fg">{clause.terms_summary}</p>
        <StatusBadge status={clause.status} size="sm" />
      </div>
      <p className="mt-1 text-xs text-fg-muted">
        Effective {clause.effective_from} to {clause.effective_until ?? "indefinite"}
      </p>
      {clause.revoked_reason ? (
        <p className="mt-2 text-xs text-fg/70">Revoked: {clause.revoked_reason}</p>
      ) : null}

      <div className="mt-3 flex flex-wrap gap-2">
        {clause.status === NonCompeteStatus.DRAFT ? (
          <Button type="button" size="sm" onClick={() => sign.mutate()} disabled={sign.isPending}>
            {sign.isPending ? "Signing…" : "Sign"}
          </Button>
        ) : null}
        {clause.status === NonCompeteStatus.ACTIVE && !revokeOpen ? (
          <Button type="button" size="sm" variant="outline" onClick={() => setRevokeOpen(true)}>
            Revoke
          </Button>
        ) : null}
      </div>

      {revokeOpen ? (
        <div className="mt-3 grid gap-2 border-t border-fg/10 pt-3">
          <label htmlFor={`revoke-${clause.id}`} className="text-xs text-fg-muted">
            Reason for revoking
          </label>
          <Input
            id={`revoke-${clause.id}`}
            type="text"
            value={revokeReason}
            onChange={(event) => setRevokeReason(event.target.value)}
            placeholder="e.g. practitioner moved to a different client portfolio"
          />
          <div className="flex gap-2">
            <Button
              type="button"
              size="sm"
              onClick={() => revoke.mutate()}
              disabled={!revokeReason.trim() || revoke.isPending}
            >
              {revoke.isPending ? "Revoking…" : "Confirm revoke"}
            </Button>
            <Button
              type="button"
              size="sm"
              variant="outline"
              onClick={() => {
                setRevokeOpen(false)
                setRevokeReason("")
              }}
            >
              Cancel
            </Button>
          </div>
        </div>
      ) : null}
    </li>
  )
}
