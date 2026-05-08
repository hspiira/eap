import { useCallback, useEffect, useState } from "react"

import { createFileRoute, useNavigate } from "@tanstack/react-router"

import { contractsApi } from "@/api/endpoints/contracts"
import { LifecycleActions } from "@/components/common/LifecycleActions"
import { StatusBadge } from "@/components/common/StatusBadge"
import { Button } from "@/components/ui/button"
import type { Contract } from "@/types/entities"
import type { LifecycleAction } from "@/utils/lifecycleConfig"

export const Route = createFileRoute("/contracts/$contractId")({
  component: ContractDetailPage,
})

function ContractDetailPage() {
  const { contractId } = Route.useParams()
  const navigate = useNavigate()
  const [contract, setContract] = useState<Contract | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)

  const fetchContract = useCallback(async () => {
    try {
      setLoading(true)
      setContract(await contractsApi.getById(contractId))
    } catch {
      setContract(null)
    } finally {
      setLoading(false)
    }
  }, [contractId])

  useEffect(() => { fetchContract() }, [fetchContract])

  const handleAction = useCallback(async (id: string, action: LifecycleAction) => {
    setActionLoading(true)
    try {
      if (action === "activate") await contractsApi.activate(id)
      else if (action === "terminate") await contractsApi.terminate(id, "Terminated from UI")
      else if (action === "renew") await contractsApi.renew(id, {})
      await fetchContract()
    } finally {
      setActionLoading(false)
    }
  }, [fetchContract])

  if (loading) return <div className="p-8 text-fg">Loading…</div>
  if (!contract) {
    return (
      <div className="p-8">
        <p className="text-fg">Contract not found.</p>
        <Button variant="secondary" className="mt-4 rounded-none" onClick={() => navigate({ to: "/contracts" })}>Back to contracts</Button>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <Button variant="ghost" size="sm" className="rounded-none" onClick={() => navigate({ to: "/contracts" })}>← Contracts</Button>
      <div className="border border-fg/30 rounded-none p-6 bg-surface/30">
        <h1 className="text-xl font-semibold text-fg">{contract.contract_number ?? contract.id}</h1>
        <dl className="mt-4 grid gap-2 sm:grid-cols-2">
          <div><dt className="text-sm text-fg/80">Status</dt><dd><StatusBadge status={contract.status} /></dd></div>
          <div><dt className="text-sm text-fg/80">Client ID</dt><dd>{contract.client_id}</dd></div>
          <div><dt className="text-sm text-fg/80">Start</dt><dd>{contract.start_date}</dd></div>
          <div><dt className="text-sm text-fg/80">End</dt><dd>{contract.end_date ?? "—"}</dd></div>
        </dl>
        <div className="mt-6">
          <h2 className="text-sm font-medium text-fg mb-2">Actions</h2>
          <LifecycleActions entityId={contract.id} currentStatus={contract.status} kind="contract" onAction={handleAction} loading={actionLoading} />
        </div>
      </div>
    </div>
  )
}
