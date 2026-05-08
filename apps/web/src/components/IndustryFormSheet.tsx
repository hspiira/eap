import { useEffect } from "react"

import { useQueryClient } from "@tanstack/react-query"
import { z } from "zod"

import { industriesApi } from "@/api/endpoints/industries"
import { FormField } from "@/components/common/FormField"
import { SheetForm } from "@/components/common/SheetForm"
import { Input } from "@/components/ui/input"
import { useApiForm } from "@/hooks/useApiForm"
import type { Industry } from "@/types/entities"

const industrySchema = z.object({
  name: z.string().trim().min(1, "Name is required"),
  code: z
    .string()
    .trim()
    .optional()
    .refine((v) => !v || v.length <= 12, "Keep code under 12 characters"),
  level: z
    .string()
    .optional()
    .refine(
      (v) => !v || (/^\d+$/.test(v) && Number.parseInt(v, 10) >= 0),
      "Use a non-negative integer",
    ),
  parent_id: z.string().optional(),
})

type IndustryFormValues = z.infer<typeof industrySchema>

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
  const isEdit = Boolean(industry)
  const queryClient = useQueryClient()

  const { register, reset, formState, submit, serverError } = useApiForm<IndustryFormValues>({
    schema: industrySchema,
    defaultValues: { name: "", code: "", level: "", parent_id: "" },
    successToast: isEdit ? "Industry updated" : "Industry created",
    onSubmit: async (values) => {
      const payload = {
        name: values.name,
        code: values.code?.trim() ? values.code.trim().toUpperCase() : null,
        level: values.level?.trim() ? Number.parseInt(values.level, 10) : null,
        parent_id: values.parent_id?.trim() ? values.parent_id.trim() : null,
      }
      const result = industry
        ? await industriesApi.update(industry.id, payload)
        : await industriesApi.create(payload)
      await queryClient.invalidateQueries({ queryKey: ["industries", "list"] })
      onSaved?.(result)
      onOpenChange(false)
      reset()
    },
  })

  useEffect(() => {
    if (!open) return
    if (industry) {
      reset({
        name: industry.name,
        code: industry.code ?? "",
        level: industry.level != null ? String(industry.level) : "",
        parent_id: industry.parent_id ?? "",
      })
    } else {
      reset({ name: "", code: "", level: "", parent_id: "" })
    }
  }, [open, industry, reset])

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
      <FormField
        label="Name"
        required
        error={formState.errors.name?.message as string | undefined}
        htmlFor="ind-name"
      >
        <Input id="ind-name" placeholder="e.g. Renewable Energy" {...register("name")} />
      </FormField>

      <FormField
        label="Code"
        optional
        description="Short identifier shown next to the name (e.g. ENR-REN)."
        error={formState.errors.code?.message as string | undefined}
        htmlFor="ind-code"
      >
        <Input
          id="ind-code"
          placeholder="ENR-REN"
          maxLength={12}
          className="font-mono uppercase"
          {...register("code")}
        />
      </FormField>

      <FormField
        label="Level"
        optional
        description="Depth in the hierarchy (0 = top level)."
        error={formState.errors.level?.message as string | undefined}
        htmlFor="ind-level"
      >
        <Input
          id="ind-level"
          type="number"
          min={0}
          placeholder="0"
          {...register("level")}
        />
      </FormField>

      <FormField
        label="Parent industry"
        optional
        description="Paste the parent industry's ID. Leave empty for a top-level industry."
        error={formState.errors.parent_id?.message as string | undefined}
        htmlFor="ind-parent"
      >
        <Input
          id="ind-parent"
          placeholder="cln…"
          className="font-mono"
          {...register("parent_id")}
        />
      </FormField>
    </SheetForm>
  )
}
