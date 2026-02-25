import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { useCallback, useEffect, useState } from "react"
import { clientsApi } from "@/api/endpoints/clients"
import type { Client } from "@/types/entities"
import { LifecycleActions } from "@/components/common/LifecycleActions"
import { StatusBadge } from "@/components/common/StatusBadge"
import { Button } from "@/components/ui/button"
import type { LifecycleAction } from "@/utils/lifecycleConfig"

export const Route = createFileRoute("/clients/$clientId")({
  component: ClientDetailPage,
})

function ClientDetailPage() {
  const { clientId } = Route.useParams()
  const navigate = useNavigate()
  const [client, setClient] = useState<Client | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)

  const fetchClient = useCallback(async () => {
    try {
      setLoading(true)
      const data = await clientsApi.getById(clientId)
      setClient(data)
    } catch {
      setClient(null)
    } finally {
      setLoading(false)
    }
  }, [clientId])

  useEffect(() => {
    fetchClient()
  }, [fetchClient])

  const handleAction = useCallback(
    async (id: string, action: LifecycleAction) => {
      setActionLoading(true)
      try {
        if (action === "activate") await clientsApi.activate(id)
        else if (action === "deactivate") await clientsApi.deactivate(id)
        else if (action === "archive") await clientsApi.archive(id)
        else if (action === "restore") await clientsApi.restore(id)
        else if (action === "terminate") await clientsApi.terminate(id, "Terminated from UI")
        await fetchClient()
      } finally {
        setActionLoading(false)
      }
    },
    [fetchClient]
  )

  if (loading) return <div className="p-8 text-[#5A626A]">Loading…</div>
  if (!client) {
    return (
      <div className="p-8">
        <p className="text-[#5A626A]">Client not found.</p>
        <Button variant="secondary" className="mt-4 rounded-none" onClick={() => navigate({ to: "/clients" })}>
          Back to clients
        </Button>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <Button variant="ghost" size="sm" className="rounded-none" onClick={() => navigate({ to: "/clients" })}>
        ← Clients
      </Button>
      <div className="border border-[#5A626A]/30 rounded-none p-6 bg-[#E6E0D7]/30">
        <h1 className="text-xl font-semibold text-[#5A626A]">{client.name}</h1>
        <dl className="mt-4 grid gap-2 sm:grid-cols-2">
          <div>
            <dt className="text-sm text-[#5A626A]/80">Code</dt>
            <dd>{client.code}</dd>
          </div>
          <div>
            <dt className="text-sm text-[#5A626A]/80">Status</dt>
            <dd><StatusBadge status={client.status} /></dd>
          </div>
          {client.contact_info?.email && (
            <div>
              <dt className="text-sm text-[#5A626A]/80">Email</dt>
              <dd>{client.contact_info.email}</dd>
            </div>
          )}
          {client.contact_info?.phone && (
            <div>
              <dt className="text-sm text-[#5A626A]/80">Phone</dt>
              <dd>{client.contact_info.phone}</dd>
            </div>
          )}
        </dl>
        <div className="mt-6">
          <h2 className="text-sm font-medium text-[#5A626A] mb-2">Actions</h2>
          <LifecycleActions
            entityId={client.id}
            currentStatus={client.status}
            kind="client"
            onAction={handleAction}
            loading={actionLoading}
          />
        </div>
      </div>
    </div>
  )
}
