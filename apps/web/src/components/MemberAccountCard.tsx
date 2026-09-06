import { useState } from "react"

import { useQuery } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"

import { membersApi } from "@/api/endpoints/members"
import { usersApi } from "@/api/endpoints/users"
import { DetailCard } from "@/components/common/DetailPrimitives"
import { UserPicker } from "@/components/common/EntityPicker"
import { StatusBadge } from "@/components/common/StatusBadge"
import { Button } from "@/components/ui/button"
import { useToast } from "@/contexts/ToastContext"
import { useCurrentRole } from "@/hooks/useCanWrite"
import { normalizeErrorMessage } from "@/lib/errors"
import { entityDetailKey } from "@/lib/queries"
import type { Member } from "@/types/entities"
import { TenantRole } from "@/types/enums"

export function MemberAccountCard({
  member,
  onChanged,
}: {
  member: Member
  onChanged: (member: Member) => void
}) {
  const toast = useToast()
  const isAdmin = useCurrentRole() === TenantRole.ADMIN
  const [selectedUserId, setSelectedUserId] = useState("")
  const [saving, setSaving] = useState(false)
  const account = useQuery({
    queryKey: entityDetailKey("users", member.user_id ?? ""),
    queryFn: () => usersApi.getById(member.user_id!),
    enabled: Boolean(member.user_id),
  })

  const change = async (operation: () => Promise<Member>, message: string) => {
    setSaving(true)
    try {
      const updated = await operation()
      onChanged(updated)
      setSelectedUserId("")
      toast.showSuccess(message)
    } catch (error) {
      toast.showError(normalizeErrorMessage(error, "Could not update account link"))
    } finally {
      setSaving(false)
    }
  }

  return (
    <DetailCard title="Account access">
      <p className="mb-4 text-sm text-fg-muted">
        Link an existing tenant user explicitly. This identifies the member's login account; the
        user's role and access scopes remain managed in Users & Invitations.
      </p>
      {member.user_id ? (
        account.isPending ? (
          <p className="text-sm text-fg-muted">Loading linked account…</p>
        ) : account.isError || !account.data ? (
          <p role="alert" className="text-sm text-danger-fg">
            Linked account is unavailable.
          </p>
        ) : (
          <div className="flex items-center justify-between gap-4 border border-fg/10 p-4">
            <div>
              <Link
                to="/users/$userId"
                params={{ userId: account.data.id }}
                className="font-medium text-primary hover:underline"
              >
                {account.data.display_name || account.data.email}
              </Link>
              <p className="mt-1 text-xs text-fg-muted">{account.data.email}</p>
              <div className="mt-2">
                <StatusBadge status={account.data.status} />
              </div>
            </div>
            {isAdmin ? (
              <Button
                variant="outline"
                disabled={saving}
                onClick={() =>
                  void change(() => membersApi.unlinkAccount(member.id), "Account unlinked")
                }
              >
                Unlink
              </Button>
            ) : null}
          </div>
        )
      ) : isAdmin ? (
        <div className="space-y-3">
          <UserPicker value={selectedUserId} onChange={setSelectedUserId} />
          <Button
            disabled={!selectedUserId || saving}
            onClick={() =>
              void change(() => membersApi.linkAccount(member.id, selectedUserId), "Account linked")
            }
          >
            {saving ? "Linking…" : "Link account"}
          </Button>
        </div>
      ) : (
        <p className="text-sm text-fg-muted">No account is linked. A tenant admin can link one.</p>
      )}
    </DetailCard>
  )
}
