import { useState } from "react"

import { createFileRoute, useNavigate } from "@tanstack/react-router"

import { clientTagsApi } from "@/api/endpoints/client-tags"
import { FormField } from "@/components/common/FormField"
import { TagsPageHeader } from "@/components/TagsPageHeader"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"

export const Route = createFileRoute("/tags/new")({
  component: TagCreatePage,
})

function TagCreatePage() {
  const navigate = useNavigate()
  const [name, setName] = useState("")
  const [color, setColor] = useState("")
  const [description, setDescription] = useState("")
  const [error, setError] = useState<string | null>(null)
  const [fieldErrors, setFieldErrors] = useState<Record<string, string>>({})
  const [loading, setLoading] = useState(false)

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError(null)
    setFieldErrors({})
    setLoading(true)
    try {
      await clientTagsApi.create({
        name,
        color: color || undefined,
        description: description || undefined,
      })
      navigate({ to: "/tags" })
    } catch (err: unknown) {
      setError(err instanceof Error ? err.message : "Failed to create tag")
      if (err && typeof err === "object" && "fieldErrors" in err) {
        setFieldErrors((err as { fieldErrors?: Record<string, string> }).fieldErrors ?? {})
      }
    } finally {
      setLoading(false)
    }
  }

  return (
    <TagsPageHeader breadcrumb="Tags > New">
      <div className="content-area-scroll flex-1 min-h-0 overflow-x-auto overflow-y-auto p-4">
        <div className="max-w-md">
          <h1 className="text-xl font-semibold text-[#5A626A]">New tag</h1>
          <form onSubmit={handleSubmit} className="mt-6 space-y-4">
            {error && (
              <p className="text-sm text-[#5A626A]" role="alert">
                {error}
              </p>
            )}
            <FormField label="Name" required error={fieldErrors.name} htmlFor="name">
              <Input
                id="name"
                value={name}
                onChange={(e) => setName(e.target.value)}
                required
                className="rounded-none"
              />
            </FormField>
            <FormField label="Color (hex)" error={fieldErrors.color} htmlFor="color">
              <div className="flex gap-2 items-center">
                <Input
                  id="color"
                  type="text"
                  placeholder="#103a10"
                  value={color}
                  onChange={(e) => setColor(e.target.value)}
                  className="rounded-none flex-1"
                />
                {color && (
                  <span
                    className="h-8 w-8 shrink-0 border border-[#5A626A]/30"
                    style={{ backgroundColor: color }}
                  />
                )}
              </div>
            </FormField>
            <FormField label="Description" error={fieldErrors.description} htmlFor="description">
              <Input
                id="description"
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                className="rounded-none"
              />
            </FormField>
            <div className="flex gap-2">
              <Button type="submit" disabled={loading} className="rounded-none bg-natural hover:bg-natural-dark">
                {loading ? "Creating…" : "Create tag"}
              </Button>
              <Button
                type="button"
                variant="secondary"
                className="rounded-none"
                onClick={() => navigate({ to: "/tags" })}
              >
                Cancel
              </Button>
            </div>
          </form>
        </div>
      </div>
    </TagsPageHeader>
  )
}
