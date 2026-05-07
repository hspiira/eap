import { useCallback, useEffect, useState } from "react"

import { createFileRoute, useNavigate } from "@tanstack/react-router"

import { serviceAssignmentsApi } from "@/api/endpoints/service-assignments"
import { LifecycleActions } from "@/components/common/LifecycleActions"
import { StatusBadge } from "@/components/common/StatusBadge"
import { Button } from "@/components/ui/button"
import type { ServiceAssignment } from "@/types/entities"
import type { LifecycleAction } from "@/utils/lifecycleConfig"

export const Route = createFileRoute("/service-assignments/$assignmentId")({
  component: ServiceAssignmentDetailPage,
})

function ServiceAssignmentDetailPage() {
  const { assignmentId } = Route.useParams()
  const navigate = useNavigate()
  const [assignment, setAssignment] = useState<ServiceAssignment | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)

  const fetchAssignment = useCallback(async () => {
    try {
      setLoading(true)
      setAssignment(await serviceAssignmentsApi.getById(assignmentId))
    } catch {
      setAssignment(null)
    } finally {
      setLoading(false)
    }
  }, [assignmentId])

  useEffect(() => { fetchAssignment() }, [fetchAssignment])

  const handleAction = useCallback(async (id: string, action: LifecycleAction) => {
    setActionLoading(true)
    try {
      if (action === "activate") await serviceAssignmentsApi.activate(id)
      else if (action === "deactivate") await serviceAssignmentsApi.deactivate(id)
      else if (action === "archive") await serviceAssignmentsApi.archive(id)
      else if (action === "restore") await serviceAssignmentsApi.restore(id)
      await fetchAssignment()
    } finally {
      setActionLoading(false)
    }
  }, [fetchAssignment])

  if (loading) return <div className="p-8 text-[#5A626A]">Loading…</div>
  if (!assignment) {
    return (
      <div className="p-8">
        <p className="text-[#5A626A]">Assignment not found.</p>
        <Button variant="secondary" className="mt-4 rounded-none" onClick={() => navigate({ to: "/service-assignments" })}>Back</Button>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <Button variant="ghost" size="sm" className="rounded-none" onClick={() => navigate({ to: "/service-assignments" })}>← Assignments</Button>
      <div className="border border-[#5A626A]/30 rounded-none p-6 bg-[#E6E0D7]/30">
        <h1 className="text-xl font-semibold text-[#5A626A]">Assignment {assignment.id.slice(0, 8)}…</h1>
        <dl className="mt-4 grid gap-2 sm:grid-cols-2">
          <div><dt className="text-sm text-[#5A626A]/80">Status</dt><dd><StatusBadge status={assignment.status} /></dd></div>
          <div><dt className="text-sm text-[#5A626A]/80">Contract ID</dt><dd>{assignment.contract_id}</dd></div>
          <div><dt className="text-sm text-[#5A626A]/80">Service ID</dt><dd>{assignment.service_id}</dd></div>
        </dl>
        <div className="mt-6">
          <h2 className="text-sm font-medium text-[#5A626A] mb-2">Actions</h2>
          <LifecycleActions entityId={assignment.id} currentStatus={assignment.status} kind="base" onAction={handleAction} loading={actionLoading} />
        </div>
      </div>
    </div>
  )
}
