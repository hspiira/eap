import { Controller } from "react-hook-form"
import { z } from "zod"

import { servicesApi } from "@/api/endpoints/services"
import type { ServiceCreate, ServiceUpdateGroupSettings } from "@/api/generated"
import { FormField } from "@/components/common/FormField"
import { FormSection } from "@/components/common/FormSection"
import { SheetForm } from "@/components/common/SheetForm"
import { Checkbox } from "@/components/ui/checkbox"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useEntityFormSheet } from "@/hooks/useEntityFormSheet"
import type { Service } from "@/types/entities"

// Note: BE `ServiceCreate` does not have a `service_type` field. The category
// label below is freeform per BE; service_type is intentionally dropped from
// the create payload until BE adds it (file ticket if needed).
const CATEGORY_OPTIONS = [
  "Individual counselling",
  "Couple counselling",
  "Family therapy",
  "Group counselling",
  "Health talk",
  "Empowerment talk",
  "Coaching",
  "Care callback",
  "Policy advisory",
  "Survey",
  "Awareness",
  "CISM",
  "Critical incident response",
] as const

const schema = z.object({
  name: z.string().trim().min(1, "Name is required"),
  description: z.string().optional(),
  category: z.string().optional(),
  duration_minutes: z
    .string()
    .optional()
    .refine((v) => !v || /^\d+$/.test(v), "Must be a positive integer"),
  is_group_service: z.boolean().optional(),
  max_participants: z
    .string()
    .optional()
    .refine((v) => !v || /^\d+$/.test(v), "Must be a positive integer"),
})

type Values = z.infer<typeof schema>

const EMPTY: Values = {
  name: "",
  description: "",
  category: "",
  duration_minutes: "",
  is_group_service: false,
  max_participants: "",
}

interface ServiceFormSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  service?: Service | null
  onSaved?: (service: Service) => void
}

export function ServiceFormSheet({
  open,
  onOpenChange,
  service,
  onSaved,
}: ServiceFormSheetProps) {
  const { register, control, formState, submit, serverError, watch, isEdit } = useEntityFormSheet<
    Values,
    Parameters<typeof servicesApi.create>[0],
    Service,
    Service
  >({
    resource: "services",
    schema,
    defaultValues: EMPTY,
    open,
    onOpenChange,
    entity: service,
    toFormValues,
    parsePayload: (values): ServiceCreate => ({
      name: values.name,
      description: values.description?.trim() || null,
      category: values.category?.trim() || null,
      duration_minutes: values.duration_minutes ? Number(values.duration_minutes) : null,
      is_group_service: Boolean(values.is_group_service),
      max_participants:
        values.is_group_service && values.max_participants
          ? Number(values.max_participants)
          : null,
    }),
    save: async ({ payload, entity, isEdit }) => {
      if (isEdit && entity) {
        // BE `ServiceUpdate` doesn't accept `is_group_service`/`max_participants`.
        // Send the basic fields first, then PATCH group settings via the
        // dedicated route if they changed.
        const { is_group_service, max_participants, ...basic } = payload
        const updated = await servicesApi.update(entity.id, basic)
        const groupSettings: ServiceUpdateGroupSettings = {
          is_group_service,
          max_participants,
        }
        if (
          is_group_service !== entity.is_group_service ||
          max_participants !== entity.max_participants
        ) {
          return servicesApi.updateGroupSettings(entity.id, groupSettings)
        }
        return updated
      }
      return servicesApi.create(payload)
    },
    successToast: { create: "Service created", update: "Service updated" },
    onSaved,
  })

  const allowGroup = watch("is_group_service")

  const errors = formState.errors

  return (
    <SheetForm
      open={open}
      onOpenChange={onOpenChange}
      title={isEdit ? "Edit service" : "Add service"}
      description={
        isEdit
          ? "Update the service catalog entry, defaults, and group constraints."
          : "Create a service that contracts can cover. You can refine pricing via contract assignments."
      }
      size="md"
      onSubmit={submit}
      isSubmitting={formState.isSubmitting}
      serverError={serverError}
      submitLabel={isEdit ? "Save changes" : "Create service"}
      submittingLabel={isEdit ? "Saving…" : "Creating…"}
    >
      <FormSection title="Identity">
        <FormField label="Name" required error={errors.name?.message} htmlFor="sv-name">
          <Input
            id="sv-name"
            placeholder="e.g. Individual counselling"
            {...register("name")}
          />
        </FormField>
        <FormField
          label="Description"
          optional
          error={errors.description?.message}
          htmlFor="sv-description"
        >
          <Input
            id="sv-description"
            placeholder="Short description used on contracts and reports."
            {...register("description")}
          />
        </FormField>
      </FormSection>

      <FormSection
        title="Category"
        description="Used by reports and to map to delivery taxonomies."
      >
        <FormField
          label="Category"
          optional
          error={errors.category?.message}
          htmlFor="sv-category"
        >
          <Controller
            control={control}
            name="category"
            render={({ field }) => (
              <Select value={field.value ?? ""} onValueChange={field.onChange}>
                <SelectTrigger id="sv-category">
                  <SelectValue placeholder="Unset" />
                </SelectTrigger>
                <SelectContent>
                  {CATEGORY_OPTIONS.map((c) => (
                    <SelectItem key={c} value={c}>
                      {c}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </FormField>
      </FormSection>

      <FormSection title="Defaults">
        <FormField
          label="Default duration (minutes)"
          optional
          description="Used to pre-fill session length."
          error={errors.duration_minutes?.message}
          htmlFor="sv-duration"
        >
          <Input
            id="sv-duration"
            type="number"
            inputMode="numeric"
            min={0}
            placeholder="60"
            className="font-mono"
            {...register("duration_minutes")}
          />
        </FormField>
      </FormSection>

      <FormSection
        title="Group settings"
        description="Enable to allow sessions with multiple subjects."
      >
        <div className="flex items-center gap-2">
          <Controller
            control={control}
            name="is_group_service"
            render={({ field }) => (
              <Checkbox
                id="sv-is-group"
                checked={field.value}
                onCheckedChange={field.onChange}
              />
            )}
          />
          <label htmlFor="sv-is-group" className="cursor-pointer text-sm text-fg">
            This is a group service
          </label>
        </div>
        {allowGroup ? (
          <FormField
            label="Max participants"
            optional
            error={errors.max_participants?.message}
            htmlFor="sv-max"
          >
            <Input
              id="sv-max"
              type="number"
              inputMode="numeric"
              min={1}
              className="font-mono"
              {...register("max_participants")}
            />
          </FormField>
        ) : null}
      </FormSection>
    </SheetForm>
  )
}

function toFormValues(s: Service): Values {
  return {
    name: s.name,
    description: s.description ?? "",
    category: s.category ?? "",
    duration_minutes:
      s.duration_minutes != null ? String(s.duration_minutes) : "",
    is_group_service: Boolean(s.is_group_service),
    max_participants:
      s.max_participants != null ? String(s.max_participants) : "",
  }
}

export function humanizeServiceType(value: string): string {
  return value
    .split("_")
    .map((w) => w[0] + w.slice(1).toLowerCase())
    .join(" ")
}
