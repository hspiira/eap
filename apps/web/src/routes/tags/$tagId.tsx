import { useEffect } from "react"

import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { z } from "zod"

import { clientTagsApi } from "@/api/endpoints/client-tags"
import { FormField } from "@/components/common/FormField"
import { TagsPageHeader } from "@/components/TagsPageHeader"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useApiForm } from "@/hooks/useApiForm"
import { isNotFound, normalizeErrorMessage } from "@/lib/errors"
import { useEntityDetail } from "@/lib/queries"
import { TAG_HEX_COLOR_REGEX } from "@/lib/tag-colors"
import type { ClientTag } from "@/types/entities"

export const Route = createFileRoute("/tags/$tagId")({
  component: TagEditPage,
})

const tagEditSchema = z.object({
  name: z.string().trim().min(1, "Name is required"),
  color: z
    .string()
    .trim()
    .optional()
    .refine((v) => !v || TAG_HEX_COLOR_REGEX.test(v), "Must be a hex color"),
  description: z.string().optional(),
})

function TagEditPage() {
  const { tagId } = Route.useParams()
  const navigate = useNavigate()

  const { register, watch, reset, formState, submit, serverError } = useApiForm<z.infer<typeof tagEditSchema>>({
    schema: tagEditSchema,
    defaultValues: { name: "", color: "", description: "" },
    successToast: "Tag updated",
    onSubmit: async (values) => {
      await clientTagsApi.update(tagId, {
        name: values.name,
        color: values.color || undefined,
        description: values.description || undefined,
      })
      navigate({ to: "/tags" })
    },
  })

  const tagQuery = useEntityDetail<ClientTag>({
    resource: "client-tags",
    id: tagId,
    detailFn: clientTagsApi.getById,
  })
  const tag = tagQuery.data

  // Hydrate the form once the tag arrives. Keyed on the fetched value rather
  // than on tagId so a cache hit populates the form without a round trip.
  useEffect(() => {
    if (!tag) return
    reset({
      name: tag.name,
      color: tag.color ?? "",
      description: tag.description ?? "",
    })
  }, [tag, reset])

  const loadError = tagQuery.isError
    ? isNotFound(tagQuery.error)
      ? "This tag no longer exists."
      : normalizeErrorMessage(tagQuery.error, "Failed to load tag")
    : null

  const color = watch("color")

  if (tagQuery.isPending) {
    return (
      <TagsPageHeader breadcrumb="Tags > Edit">
        <div className="content-area-scroll flex-1 min-h-0 overflow-x-auto overflow-y-auto p-4">
          <p className="text-fg">Loading…</p>
        </div>
      </TagsPageHeader>
    )
  }

  return (
    <TagsPageHeader breadcrumb="Tags > Edit">
      <div className="content-area-scroll flex-1 min-h-0 overflow-x-auto overflow-y-auto p-4">
        <div className="max-w-md">
          <h1 className="text-xl font-semibold text-fg">Edit tag</h1>
          <form onSubmit={submit} className="mt-6 space-y-4" noValidate>
            {(serverError || loadError) && (
              <p className="text-sm text-fg" role="alert">
                {serverError ?? loadError}
              </p>
            )}
            <FormField
              label="Name"
              required
              error={formState.errors.name?.message}
              htmlFor="name"
            >
              <Input id="name" className="rounded-none" {...register("name")} />
            </FormField>
            <FormField
              label="Color (hex)"
              error={formState.errors.color?.message}
              htmlFor="color"
            >
              <div className="flex gap-2 items-center">
                <Input
                  id="color"
                  type="text"
                  placeholder="Hex e.g. 6 chars after #"
                  className="rounded-none flex-1"
                  {...register("color")}
                />
                {color && TAG_HEX_COLOR_REGEX.test(color) && (
                  <span
                    className="h-8 w-8 shrink-0 border border-fg/30"
                    style={{ backgroundColor: color }}
                  />
                )}
              </div>
            </FormField>
            <FormField
              label="Description"
              error={formState.errors.description?.message}
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
                {formState.isSubmitting ? "Saving…" : "Save"}
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
