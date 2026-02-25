import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { useCallback, useEffect, useState } from "react"
import { personsApi } from "@/api/endpoints/persons"
import type { Person } from "@/types/entities"
import { LifecycleActions } from "@/components/common/LifecycleActions"
import { StatusBadge } from "@/components/common/StatusBadge"
import { Button } from "@/components/ui/button"
import type { LifecycleAction } from "@/utils/lifecycleConfig"

export const Route = createFileRoute("/persons/$personId")({
  component: PersonDetailPage,
})

function PersonDetailPage() {
  const { personId } = Route.useParams()
  const navigate = useNavigate()
  const [person, setPerson] = useState<Person | null>(null)
  const [loading, setLoading] = useState(true)
  const [actionLoading, setActionLoading] = useState(false)

  const fetchPerson = useCallback(async () => {
    try {
      setLoading(true)
      setPerson(await personsApi.getById(personId))
    } catch {
      setPerson(null)
    } finally {
      setLoading(false)
    }
  }, [personId])

  useEffect(() => { fetchPerson() }, [fetchPerson])

  const handleAction = useCallback(async (id: string, action: LifecycleAction) => {
    setActionLoading(true)
    try {
      if (action === "activate") await personsApi.activate(id)
      else if (action === "deactivate") await personsApi.deactivate(id)
      else if (action === "archive") await personsApi.archive(id)
      else if (action === "restore") await personsApi.restore(id)
      else if (action === "terminate") await personsApi.terminate(id, "Terminated from UI")
      await fetchPerson()
    } finally {
      setActionLoading(false)
    }
  }, [fetchPerson])

  if (loading) return <div className="p-8 text-[#5A626A]">Loading…</div>
  if (!person) {
    return (
      <div className="p-8">
        <p className="text-[#5A626A]">Person not found.</p>
        <Button variant="secondary" className="mt-4 rounded-none" onClick={() => navigate({ to: "/persons" })}>Back to persons</Button>
      </div>
    )
  }

  return (
    <div className="p-6 space-y-6">
      <Button variant="ghost" size="sm" className="rounded-none" onClick={() => navigate({ to: "/persons" })}>← Persons</Button>
      <div className="border border-[#5A626A]/30 rounded-none p-6 bg-[#E6E0D7]/30">
        <h1 className="text-xl font-semibold text-[#5A626A]">{person.first_name} {person.last_name}</h1>
        <dl className="mt-4 grid gap-2 sm:grid-cols-2">
          <div><dt className="text-sm text-[#5A626A]/80">Type</dt><dd>{person.person_type}</dd></div>
          <div><dt className="text-sm text-[#5A626A]/80">Status</dt><dd><StatusBadge status={person.status} /></dd></div>
        </dl>
        <div className="mt-6">
          <h2 className="text-sm font-medium text-[#5A626A] mb-2">Actions</h2>
          <LifecycleActions entityId={person.id} currentStatus={person.status} kind="base" onAction={handleAction} loading={actionLoading} />
        </div>
      </div>
    </div>
  )
}
