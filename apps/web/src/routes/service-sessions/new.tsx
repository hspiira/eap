import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { useState } from "react"
import { serviceSessionsApi } from "@/api/endpoints/service-sessions"
import { FormField } from "@/components/common/FormField"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

export const Route = createFileRoute("/service-sessions/new")({
  component: ServiceSessionCreatePage,
})

function ServiceSessionCreatePage() {
  const navigate = useNavigate()
  const [serviceId, setServiceId] = useState("")
  const [personId, setPersonId] = useState("")
  const [scheduledAt, setScheduledAt] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await serviceSessionsApi.create({
        service_id: serviceId,
        person_id: personId,
        scheduled_at: new Date(scheduledAt).toISOString(),
      })
      navigate({ to: "/service-sessions" })
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create session")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 max-w-md">
      <h1 className="text-xl font-semibold text-[#5A626A]">Add session</h1>
      <form onSubmit={handleSubmit} className="mt-6 space-y-4">
        {error && <p className="text-sm text-[#5A626A]" role="alert">{error}</p>}
        <FormField label="Service ID" required htmlFor="service_id">
          <Input id="service_id" value={serviceId} onChange={(e) => setServiceId(e.target.value)} required className="rounded-none" />
        </FormField>
        <FormField label="Person ID" required htmlFor="person_id">
          <Input id="person_id" value={personId} onChange={(e) => setPersonId(e.target.value)} required className="rounded-none" />
        </FormField>
        <FormField label="Scheduled at (ISO)" required htmlFor="scheduled_at">
          <Input id="scheduled_at" type="datetime-local" value={scheduledAt} onChange={(e) => setScheduledAt(e.target.value)} required className="rounded-none" />
        </FormField>
        <div className="flex gap-2">
          <Button type="submit" disabled={loading} className="rounded-none">{loading ? "Creating…" : "Create session"}</Button>
          <Button type="button" variant="secondary" className="rounded-none" onClick={() => navigate({ to: "/service-sessions" })}>Cancel</Button>
        </div>
      </form>
    </div>
  )
}
