import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { useState } from "react"
import { servicesApi } from "@/api/endpoints/services"
import { FormField } from "@/components/common/FormField"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

export const Route = createFileRoute("/services/new")({
  component: ServiceCreatePage,
})

function ServiceCreatePage() {
  const navigate = useNavigate()
  const [name, setName] = useState("")
  const [description, setDescription] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setLoading(true)
    try {
      await servicesApi.create({ name, description: description || undefined })
      navigate({ to: "/services" })
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create service")
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="p-6 max-w-md">
      <h1 className="text-xl font-semibold text-[#5A626A]">Add service</h1>
      <form onSubmit={handleSubmit} className="mt-6 space-y-4">
        {error && <p className="text-sm text-[#5A626A]" role="alert">{error}</p>}
        <FormField label="Name" required htmlFor="name">
          <Input id="name" value={name} onChange={(e) => setName(e.target.value)} required className="rounded-none" />
        </FormField>
        <FormField label="Description" htmlFor="description">
          <Input id="description" value={description} onChange={(e) => setDescription(e.target.value)} className="rounded-none" />
        </FormField>
        <div className="flex gap-2">
          <Button type="submit" disabled={loading} className="rounded-none">{loading ? "Creating…" : "Create service"}</Button>
          <Button type="button" variant="secondary" className="rounded-none" onClick={() => navigate({ to: "/services" })}>Cancel</Button>
        </div>
      </form>
    </div>
  )
}
