import { z } from "zod"

import { clientTagsApi } from "@/api/endpoints/client-tags"
import { FormField } from "@/components/common/FormField"
import { SheetForm } from "@/components/common/SheetForm"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useEntityFormSheet } from "@/hooks/useEntityFormSheet"
import { TAG_HEX_COLOR_REGEX, TAG_SUGGESTED_COLORS } from "@/lib/tag-colors"
import type { ClientTag } from "@/types/entities"

const tagSchema = z.object({
  name: z.string().trim().min(1, "Name is required"),
  color: z
    .string()
    .trim()
    .optional()
    .refine((v) => !v || TAG_HEX_COLOR_REGEX.test(v), "Use a hex color"),
  description: z.string().optional(),
})

type TagFormValues = z.infer<typeof tagSchema>

const DEFAULTS: TagFormValues = { name: "", color: "", description: "" }

interface TagFormSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  tag?: ClientTag | null
  onSaved?: () => void
}

export function TagFormSheet({ open, onOpenChange, tag, onSaved }: TagFormSheetProps) {
  const { register, watch, setValue, formState, submit, serverError, isEdit } =
    useEntityFormSheet<TagFormValues, Parameters<typeof clientTagsApi.create>[0], ClientTag, ClientTag>({
      resource: "client-tags",
      schema: tagSchema,
      defaultValues: DEFAULTS,
      open,
      onOpenChange,
      entity: tag,
      toFormValues: (t) => ({
        name: t.name,
        color: t.color ?? "",
        description: t.description ?? "",
      }),
      parsePayload: (values) => ({
        name: values.name,
        color: values.color || undefined,
        description: values.description || undefined,
      }),
      save: ({ payload, entity, isEdit }) =>
        isEdit && entity ? clientTagsApi.update(entity.id, payload) : clientTagsApi.create(payload),
      successToast: { create: "Tag created", update: "Tag updated" },
      onSaved: () => onSaved?.(),
    })

  const errors = formState.errors
  const color = watch("color")
  const validHex = color ? TAG_HEX_COLOR_REGEX.test(color) : false

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
      <FormField label="Name" required error={errors.name?.message} htmlFor="tag-name">
        <Input id="tag-name" placeholder="e.g. VIP" {...register("name")} />
      </FormField>

      <FormField
        label="Color"
        optional
        description="Hex code shown as a swatch on the tag."
        error={errors.color?.message}
        htmlFor="tag-color"
      >
        <div className="flex items-center gap-2">
          <Input
            id="tag-color"
            type="text"
            placeholder="Hex e.g. 6 chars after #"
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
          {TAG_SUGGESTED_COLORS.map((c) => (
            <Button
              key={c}
              type="button"
              variant="ghost"
              aria-label={`Use color ${c}`}
              onClick={() => setValue("color", c, { shouldDirty: true, shouldValidate: true })}
              className="size-5 rounded-sm border border-fg/15 p-0 transition-transform hover:scale-110 hover:bg-transparent focus-visible:ring-ring focus-visible:ring-offset-1 focus-visible:ring-offset-bg"
              style={{ backgroundColor: c }}
            />
          ))}
        </div>
      </FormField>

      <FormField
        label="Description"
        optional
        error={errors.description?.message}
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
