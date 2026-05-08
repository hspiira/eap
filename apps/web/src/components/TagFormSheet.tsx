import { useEffect } from "react"

import { useQueryClient } from "@tanstack/react-query"
import { z } from "zod"

import { clientTagsApi } from "@/api/endpoints/client-tags"
import { FormField } from "@/components/common/FormField"
import { SheetForm } from "@/components/common/SheetForm"
import { Input } from "@/components/ui/input"
import { useApiForm } from "@/hooks/useApiForm"
import type { ClientTag } from "@/types/entities"

const hexColorRegex = /^#([0-9A-Fa-f]{3}|[0-9A-Fa-f]{6})$/

const tagSchema = z.object({
  name: z.string().trim().min(1, "Name is required"),
  color: z
    .string()
    .trim()
    .optional()
    .refine((v) => !v || hexColorRegex.test(v), "Use a hex color e.g. #103a10"),
  description: z.string().optional(),
})

type TagFormValues = z.infer<typeof tagSchema>

const SUGGESTED_COLORS = [
  "#0f5132",
  "#15803d",
  "#1d4ed8",
  "#b45309",
  "#b91c1c",
  "#737373",
] as const

interface TagFormSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  tag?: ClientTag | null
  onSaved?: () => void
}

export function TagFormSheet({ open, onOpenChange, tag, onSaved }: TagFormSheetProps) {
  const isEdit = Boolean(tag)
  const queryClient = useQueryClient()

  const { register, watch, setValue, reset, formState, submit, serverError } = useApiForm<TagFormValues>({
    schema: tagSchema,
    defaultValues: { name: "", color: "", description: "" },
    successToast: isEdit ? "Tag updated" : "Tag created",
    onSubmit: async (values) => {
      const payload = {
        name: values.name,
        color: values.color || undefined,
        description: values.description || undefined,
      }
      if (tag) {
        await clientTagsApi.update(tag.id, payload)
      } else {
        await clientTagsApi.create(payload)
      }
      await queryClient.invalidateQueries({ queryKey: ["client-tags", "list"] })
      onSaved?.()
      onOpenChange(false)
      reset()
    },
  })

  useEffect(() => {
    if (!open) return
    if (tag) {
      reset({
        name: tag.name,
        color: tag.color ?? "",
        description: tag.description ?? "",
      })
    } else {
      reset({ name: "", color: "", description: "" })
    }
  }, [open, tag, reset])

  const color = watch("color")
  const validHex = color ? hexColorRegex.test(color) : false

  return (
    <SheetForm
      open={open}
      onOpenChange={onOpenChange}
      title={isEdit ? "Edit tag" : "New tag"}
      description={
        isEdit
          ? "Update label, color, and description."
          : "Reusable label for grouping clients across the platform."
      }
      size="md"
      onSubmit={submit}
      isSubmitting={formState.isSubmitting}
      serverError={serverError}
      submitLabel={isEdit ? "Save changes" : "Create tag"}
      submittingLabel={isEdit ? "Saving…" : "Creating…"}
    >
      <FormField
        label="Name"
        required
        error={formState.errors.name?.message as string | undefined}
        htmlFor="tag-name"
      >
        <Input id="tag-name" placeholder="e.g. VIP" {...register("name")} />
      </FormField>

      <FormField
        label="Color"
        optional
        description="Hex code shown as a swatch on the tag."
        error={formState.errors.color?.message as string | undefined}
        htmlFor="tag-color"
      >
        <div className="flex items-center gap-2">
          <Input
            id="tag-color"
            type="text"
            placeholder="#103a10"
            className="font-mono"
            {...register("color")}
          />
          <span
            aria-hidden
            className="size-9 shrink-0 rounded-sm border border-fg/20"
            style={validHex ? { backgroundColor: color } : undefined}
          />
        </div>
        <div className="mt-2 flex flex-wrap items-center gap-1.5">
          {SUGGESTED_COLORS.map((c) => (
            <button
              key={c}
              type="button"
              aria-label={`Use color ${c}`}
              onClick={() => setValue("color", c, { shouldDirty: true, shouldValidate: true })}
              className="size-5 rounded-sm border border-fg/15 transition-transform hover:scale-110 focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-1 focus-visible:ring-offset-bg"
              style={{ backgroundColor: c }}
            />
          ))}
        </div>
      </FormField>

      <FormField
        label="Description"
        optional
        error={formState.errors.description?.message as string | undefined}
        htmlFor="tag-description"
      >
        <Input
          id="tag-description"
          placeholder="What is this tag used for?"
          {...register("description")}
        />
      </FormField>
    </SheetForm>
  )
}
