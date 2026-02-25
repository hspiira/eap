import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { useCallback, useEffect, useState } from "react"
import { usersApi } from "@/api/endpoints/users"
import type { User } from "@/types/entities"
import { LifecycleActions } from "@/components/common/LifecycleActions"
import { StatusBadge } from "@/components/common/StatusBadge"
import type { LifecycleAction } from "@/utils/lifecycleConfig"
import { Button } from "@/components/ui/button"

export const Route = createFileRoute("/users/$userId")({
  component: UserDetailPage,
})

function UserDetailPage() {
  const { userId } = Route.useParams()
  const navigate = useNavigate()
  const [user, setUser] = useState<User | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)

  const fetchUser = useCallback(async () => {
    try {
      setLoading(true)
      const data = await usersApi.getById(userId)
      setUser(data)
    } catch {
      setUser(null)
    } finally {
      setLoading(false)
    }
  }, [userId])

  useEffect(() => {
    fetchUser()
  }, [fetchUser])

  const handleAction = useCallback(
    async (id: string, action: LifecycleAction) => {
      setActionLoading(true)
      try {
        if (action === "activate") await usersApi.activate(id)
        else if (action === "suspend") await usersApi.suspend(id)
        else if (action === "ban") await usersApi.ban(id)
        else if (action === "terminate") await usersApi.terminate(id, "Terminated from UI")
        else if (action === "deactivate") await usersApi.deactivate(id)
        await fetchUser()
      } finally {
        setActionLoading(false)
      }
    },
    [fetchUser]
  )

  if (loading) {
    return (
      <div className="p-8 text-[#5A626A]">
        Loading…
      </div>
    )
  }

  if (!user) {
    return (
      <div className="p-8">
        <p className="text-[#5A626A]">User not found.</p>
        <Button variant="secondary" className="mt-4 rounded-none" onClick={() => navigate({ to: "/users" })}>
          Back to users
        </Button>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <div className="flex items-center justify-between">
        <Button
          variant="ghost"
          size="sm"
          className="rounded-none"
          onClick={() => navigate({ to: "/users" })}
        >
          ← Users
        </Button>
      </div>
      <div className="border border-[#5A626A]/30 rounded-none p-6 bg-[#E6E0D7]/30">
        <h1 className="text-xl font-semibold text-[#5A626A]">{user.email}</h1>
        <dl className="mt-4 grid gap-2 sm:grid-cols-2">
          <div>
            <dt className="text-sm text-[#5A626A]/80">Status</dt>
            <dd><StatusBadge status={user.status} /></dd>
          </div>
          <div>
            <dt className="text-sm text-[#5A626A]/80">Email verified</dt>
            <dd>{user.is_email_verified ? "Yes" : "No"}</dd>
          </div>
          <div>
            <dt className="text-sm text-[#5A626A]/80">2FA</dt>
            <dd>{user.is_two_factor_enabled ? "On" : "Off"}</dd>
          </div>
          {user.last_login_at && (
            <div>
              <dt className="text-sm text-[#5A626A]/80">Last login</dt>
              <dd>{new Date(user.last_login_at).toLocaleString()}</dd>
            </div>
          )}
        </dl>
        <div className="mt-6">
          <h2 className="text-sm font-medium text-[#5A626A] mb-2">Actions</h2>
          <LifecycleActions
            entityId={user.id}
            currentStatus={user.status}
            kind="user"
            onAction={handleAction}
            loading={actionLoading}
          />
        </div>
      </div>
    </div>
  )
}
