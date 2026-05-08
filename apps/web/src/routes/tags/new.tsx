import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { z } from "zod"

import { clientTagsApi } from "@/api/endpoints/client-tags"
import { FormField } from "@/components/common/FormField"
import { TagsPageHeader } from "@/components/TagsPageHeader"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useApiForm } from "@/hooks/useApiForm"

export const Route = createFileRoute("/tags/new")({
  component: TagCreatePage,
})

const hexColorRegex = /^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$/

const tagCreateSchema = z.object({
  name: z.string().trim().min(1, "Name is required"),
  color: z
    .string()
    .trim()
    .optional()
    .refine((v) => !v || hexColorRegex.test(v), "Must be a hex color (e.g. #103a10)"),
  description: z.string().optional(),
})

function TagCreatePage() {
  const navigate = useNavigate()

  const { register, watch, formState, submit, serverError } = useApiForm<z.infer<typeof tagCreateSchema>>({
    schema: tagCreateSchema,
    defaultValues: { name: "", color: "", description: "" },
    successToast: "Tag created",
    onSubmit: async (values) => {
      await clientTagsApi.create({
        name: values.name,
        color: values.color || undefined,
        description: values.description || undefined,
      })
      navigate({ to: "/tags" })
    },
  })

  const color = watch("color")

  return (
    <TagsPageHeader breadcrumb="Tags > New">
      <div className="content-area-scroll flex-1 min-h-0 overflow-x-auto overflow-y-auto p-4">
        <div className="max-w-md">
          <h1 className="text-xl font-semibold text-fg">New tag</h1>
          <form onSubmit={submit} className="mt-6 space-y-4" noValidate>
            {serverError && (
              <p className="text-sm text-fg" role="alert">
                {serverError}
              </p>
            )}
            <FormField
              label="Name"
              required
              error={formState.errors.name?.message as string | undefined}
              htmlFor="name"
            >
              <Input id="name" className="rounded-none" {...register("name")} />
            </FormField>
            <FormField
              label="Color (hex)"
              error={formState.errors.color?.message as string | undefined}
              htmlFor="color"
            >
              <div className="flex gap-2 items-center">
                <Input
                  id="color"
                  type="text"
                  placeholder="#103a10"
                  className="rounded-none flex-1"
                  {...register("color")}
                />
                {color && hexColorRegex.test(color) && (
                  <span
                    className="h-8 w-8 shrink-0 border border-fg/30"
                    style={{ backgroundColor: color }}
                  />
                )}
              </div>
            </FormField>
            <FormField
              label="Description"
              error={formState.errors.description?.message as string | undefined}
              htmlFor="description"
            >
              <Input id="description" className="rounded-none" {...register("description")} />
            </FormField>
            <div className="flex gap-2">
              <Button
                type="submit"
                disabled={formState.isSubmitting}
                className="rounded-none bg-primary hover:bg-primary"
              >
                {formState.isSubmitting ? "Creating…" : "Create tag"}
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
