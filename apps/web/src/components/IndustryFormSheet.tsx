import { z } from "zod"

import { industriesApi } from "@/api/endpoints/industries"
import { FormField } from "@/components/common/FormField"
import { SheetForm } from "@/components/common/SheetForm"
import { Input } from "@/components/ui/input"
import { useEntityFormSheet } from "@/hooks/useEntityFormSheet"
import type { Industry } from "@/types/entities"

const industrySchema = z.object({
  name: z.string().trim().min(1, "Name is required"),
  code: z
    .string()
    .trim()
    .optional()
    .refine((v) => !v || v.length <= 12, "Keep code under 12 characters"),
  parent_industry_id: z.string().optional(),
})

type IndustryFormValues = z.infer<typeof industrySchema>

const DEFAULTS: IndustryFormValues = { name: "", code: "", parent_industry_id: "" }

interface IndustryFormSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  industry?: Industry | null
  onSaved?: (industry: Industry) => void
}

export function IndustryFormSheet({
  open,
  onOpenChange,
  industry,
  onSaved,
}: IndustryFormSheetProps) {
  const { register, formState, submit, serverError, isEdit } = useEntityFormSheet<
    IndustryFormValues,
    Parameters<typeof industriesApi.create>[0],
    Industry,
    Industry
  >({
    resource: "industries",
    schema: industrySchema,
    defaultValues: DEFAULTS,
    open,
    onOpenChange,
    entity: industry,
    toFormValues: (i) => ({
      name: i.name,
      code: i.code ?? "",
      parent_industry_id: i.parent_industry_id ?? "",
    }),
    parsePayload: (values): Parameters<typeof industriesApi.create>[0] => ({
      name: values.name,
      code: values.code?.trim() ? values.code.trim().toUpperCase() : null,
      parent_industry_id: values.parent_industry_id?.trim()
        ? values.parent_industry_id.trim()
        : null,
    }),
    save: ({ payload, entity, isEdit }) =>
      isEdit && entity ? industriesApi.update(entity.id, payload) : industriesApi.create(payload),
    successToast: { create: "Industry created", update: "Industry updated" },
    onSaved,
  })

  const errors = formState.errors

  return (
    <SheetForm
      open={open}
      onOpenChange={onOpenChange}
      title={isEdit ? "Edit industry" : "New industry"}
      description={
        isEdit
          ? "Update name, code, and hierarchy."
          : "Add an industry classification used to tag clients."
      }
      size="md"
      onSubmit={submit}
      isSubmitting={formState.isSubmitting}
      serverError={serverError}
      submitLabel={isEdit ? "Save changes" : "Create industry"}
      submittingLabel={isEdit ? "Saving…" : "Creating…"}
    >
      <FormField label="Name" required error={errors.name?.message} htmlFor="ind-name">
        <Input id="ind-name" placeholder="e.g. Renewable Energy" {...register("name")} />
      </FormField>

      <FormField
        label="Code"
        description="Short identifier shown next to the name (e.g. ENR-REN)."
        error={errors.code?.message}
        htmlFor="ind-code"
      >
        <Input
          id="ind-code"
          placeholder="ENR-REN"
          maxLength={12}

          {...register("code")}
        />
      </FormField>

      <FormField
        label="Parent industry"
        description="Paste the parent industry's ID. Leave empty for a top-level industry."
        error={errors.parent_industry_id?.message}
        htmlFor="ind-parent"
      >
        <Input
          id="ind-parent"
          placeholder="cln…"

          {...register("parent_industry_id")}
        />
      </FormField>
    </SheetForm>
  )
}
