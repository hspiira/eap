import { useCallback, useEffect, useState } from "react"

import { createFileRoute, useNavigate } from "@tanstack/react-router"

import { serviceSessionsApi } from "@/api/endpoints/service-sessions"
import { LifecycleActions } from "@/components/common/LifecycleActions"
import { StatusBadge } from "@/components/common/StatusBadge"
import { Button } from "@/components/ui/button"
import type { ServiceSession } from "@/types/entities"
import type { LifecycleAction } from "@/utils/lifecycleConfig"

export const Route = createFileRoute("/service-sessions/$sessionId")({
  component: ServiceSessionDetailPage,
})

function ServiceSessionDetailPage() {
  const { sessionId } = Route.useParams()
  const navigate = useNavigate()
  const [session, setSession] = useState<ServiceSession | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)

  const fetchSession = useCallback(async () => {
    try {
      setLoading(true)
      setSession(await serviceSessionsApi.getById(sessionId))
    } catch {
      setSession(null)
    } finally {
      setLoading(false)
    }
  }, [sessionId])

  useEffect(() => { fetchSession() }, [fetchSession])

  const handleAction = useCallback(async (id: string, action: LifecycleAction) => {
    setActionLoading(true)
    try {
      if (action === "complete") await serviceSessionsApi.complete(id)
      else if (action === "cancel") await serviceSessionsApi.cancel(id)
      else if (action === "no-show") await serviceSessionsApi.noShow(id)
      else if (action === "archive") await serviceSessionsApi.archive(id)
      else if (action === "restore") await serviceSessionsApi.restore(id)
      await fetchSession()
    } finally {
      setActionLoading(false)
    }
  }, [fetchSession])

  if (loading) return <div className="p-8 text-fg">Loading…</div>
  if (!session) {
    return (
      <div className="p-8">
        <p className="text-fg">Session not found.</p>
        <Button variant="secondary" className="mt-4 rounded-none" onClick={() => navigate({ to: "/service-sessions" })}>Back to sessions</Button>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <Button variant="ghost" size="sm" className="rounded-none" onClick={() => navigate({ to: "/service-sessions" })}>← Sessions</Button>
      <div className="border border-fg/30 rounded-none p-6 bg-surface/30">
        <h1 className="text-xl font-semibold text-fg">Session {session.scheduled_at ? new Date(session.scheduled_at).toLocaleString() : session.id.slice(0, 8)}</h1>
        <dl className="mt-4 grid gap-2 sm:grid-cols-2">
          <div><dt className="text-sm text-fg/80">Status</dt><dd><StatusBadge status={session.status} /></dd></div>
          <div><dt className="text-sm text-fg/80">Scheduled</dt><dd>{session.scheduled_at ? new Date(session.scheduled_at).toLocaleString() : "—"}</dd></div>
          <div><dt className="text-sm text-fg/80">Service ID</dt><dd>{session.service_id}</dd></div>
          <div><dt className="text-sm text-fg/80">Person ID</dt><dd>{session.person_id}</dd></div>
        </dl>
        <div className="mt-6">
          <h2 className="text-sm font-medium text-fg mb-2">Actions</h2>
          <LifecycleActions entityId={session.id} currentStatus={session.status} kind="session" onAction={handleAction} loading={actionLoading} />
        </div>
      </div>
    </div>
  )
}
