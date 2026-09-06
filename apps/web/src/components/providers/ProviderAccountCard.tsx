import { useState } from "react"

import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"

import { providersApi } from "@/api/endpoints/providers"
import { usersApi } from "@/api/endpoints/users"
import { DetailCard } from "@/components/common/DetailPrimitives"
import { UserPicker } from "@/components/common/EntityPicker"
import { StatusBadge } from "@/components/common/StatusBadge"
import { ReasonDialog } from "@/components/providers/ReasonDialog"
import { Button } from "@/components/ui/button"
import { useToast } from "@/contexts/ToastContext"
import { useCurrentRole } from "@/hooks/useCanWrite"
import { normalizeErrorMessage } from "@/lib/errors"
import { entityDetailKey } from "@/lib/queries"
import type { Provider } from "@/types/entities"
import { TenantRole } from "@/types/enums"

/**
 * The optional link between a practitioner and a login.
 *
 * Linking grants no role and copies no contact details in either direction,
 * and unlinking leaves the practitioner and their sessions in place.
 */
export function ProviderAccountCard({
  provider,
  onChanged,
}: {
  provider: Provider
  onChanged: (provider: Provider) => void
}) {
  const toast = useToast()
  const isAdmin = useCurrentRole() === TenantRole.ADMIN
  const [selectedUserId, setSelectedUserId] = useState("")
  const [action, setAction] = useState<"link" | "unlink" | null>(null)

  const account = useQuery({
    queryKey: entityDetailKey("users", provider.user_id ?? ""),
    queryFn: () => usersApi.getById(provider.user_id!),
    enabled: Boolean(provider.user_id),
  })

  const run = async (reason: string) => {
    try {
      const updated =
        action === "link"
          ? await providersApi.linkAccount(provider.id, { user_id: selectedUserId, reason })
          : await providersApi.unlinkAccount(provider.id, { reason })
      onChanged(updated)
      setSelectedUserId("")
      setAction(null)
      toast.showSuccess(action === "link" ? "Account linked" : "Account unlinked")
    } catch (error) {
      toast.showError(normalizeErrorMessage(error, "Could not update the account link"))
    }
  }

  return (
    <DetailCard title="Linked account">
      <p className="mb-4 text-sm text-fg-muted">
        A practitioner does not need a login. Linking one records which account belongs to this
        person; it grants no role and does not copy contact details either way.
      </p>

      {provider.user_id ? (
        <LinkedAccount
          pending={account.isPending}
          error={account.isError || !account.data}
          account={account.data ?? null}
          canUnlink={isAdmin}
          onUnlink={() => setAction("unlink")}
        />
      ) : isAdmin ? (
        <div className="space-y-3">
          <UserPicker value={selectedUserId} onChange={setSelectedUserId} />
          <Button
            type="button"
            size="sm"
            disabled={!selectedUserId}
            onClick={() => setAction("link")}
          >
            Link account
          </Button>
        </div>
      ) : (
        <p className="text-sm text-fg-muted">No account is linked. A tenant admin can link one.</p>
      )}

      <ReasonDialog
        open={action !== null}
        onOpenChange={(open) => (open ? null : setAction(null))}
        title={action === "link" ? "Link this account" : "Unlink this account"}
        description={
          action === "link"
            ? "The account must belong to this tenant, and neither it nor the practitioner may already be linked to another."
            : "The practitioner and every past session stay visible. Only the link to the login is removed."
        }
        confirmLabel={action === "link" ? "Link account" : "Unlink account"}
        onConfirm={run}
      />
    </DetailCard>
  )
}

function LinkedAccount({
  pending,
  error,
  account,
  canUnlink,
  onUnlink,
}: {
  pending: boolean
  error: boolean
  account: { id: string; display_name?: string | null; email: string; status: string } | null
  canUnlink: boolean
  onUnlink: () => void
}) {
  if (pending) return <p className="text-sm text-fg-muted">Loading linked account…</p>
  if (error || !account) {
    return (
      <p role="alert" className="text-sm text-danger-fg">
        The linked account is unavailable. The practitioner and their sessions are unaffected.
      </p>
    )
  }
  return (
    <div className="flex items-center justify-between gap-4 border border-fg/10 p-4">
      <div className="min-w-0">
        <Link
          to="/users/$userId"
          params={{ userId: account.id }}
          className="font-medium text-primary hover:underline"
        >
          {account.display_name || account.email}
        </Link>
        <p className="mt-1 truncate text-xs text-fg-muted">{account.email}</p>
        <div className="mt-2">
          <StatusBadge status={account.status} size="sm" />
        </div>
      </div>
      {canUnlink ? (
        <Button type="button" variant="outline" size="sm" onClick={onUnlink}>
          Unlink
        </Button>
      ) : null}
    </div>
  )
}
