import { z } from "zod"
import { Controller } from "react-hook-form"

import { servicesApi } from "@/api/endpoints/services"
import { FormField } from "@/components/common/FormField"
import { FormSection } from "@/components/common/FormSection"
import { SheetForm } from "@/components/common/SheetForm"
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

const SERVICE_TYPE_OPTIONS = [
  "INDIVIDUAL_COUNSELLING",
  "COUPLE_COUNSELLING",
  "FAMILY_THERAPY",
  "GROUP_COUNSELLING",
  "HEALTH_TALK",
  "EMPOWERMENT_TALK",
  "COACHING",
  "CARE_CALLBACK",
  "POLICY_ADVISORY",
  "SURVEY",
  "AWARENESS",
  "CISM_DEFUSING",
  "CISM_DEBRIEFING",
  "CRITICAL_INCIDENT_RESPONSE",
] as const

const schema = z
  .object({
    name: z.string().trim().min(1, "Name is required"),
    description: z.string().optional(),
    service_type: z.string().optional(),
    category: z.string().optional(),
    duration_minutes: z
      .string()
      .optional()
      .refine((v) => !v || /^\d+$/.test(v), "Must be a positive integer"),
    allow_group_sessions: z.boolean().optional(),
    min_group_size: z
      .string()
      .optional()
      .refine((v) => !v || /^\d+$/.test(v), "Must be a positive integer"),
    max_group_size: z
      .string()
      .optional()
      .refine((v) => !v || /^\d+$/.test(v), "Must be a positive integer"),
  })
  .refine(
    (d) =>
      !d.allow_group_sessions ||
      !d.min_group_size ||
      !d.max_group_size ||
      Number(d.min_group_size) <= Number(d.max_group_size),
    {
      path: ["max_group_size"],
      message: "Max must be ≥ min",
    },
  )

type Values = z.infer<typeof schema>

const EMPTY: Values = {
  name: "",
  description: "",
  service_type: "",
  category: "",
  duration_minutes: "",
  allow_group_sessions: false,
  min_group_size: "",
  max_group_size: "",
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
    parsePayload: (values) => ({
      name: values.name,
      description: values.description?.trim() || undefined,
      service_type: values.service_type?.trim() || undefined,
      category: values.category?.trim() || undefined,
      duration_minutes: values.duration_minutes ? Number(values.duration_minutes) : undefined,
      group_settings:
        values.allow_group_sessions || values.min_group_size || values.max_group_size
          ? {
              allow_group_sessions: Boolean(values.allow_group_sessions),
              min_group_size: values.min_group_size ? Number(values.min_group_size) : null,
              max_group_size: values.max_group_size ? Number(values.max_group_size) : null,
            }
          : undefined,
    }),
    save: ({ payload, entity, isEdit }) =>
      isEdit && entity ? servicesApi.update(entity.id, payload) : servicesApi.create(payload),
    successToast: { create: "Service created", update: "Service updated" },
    onSaved,
  })

  const allowGroup = watch("allow_group_sessions")

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
        title="Classification"
        description="Used by reports and to map to delivery taxonomies."
      >
        <FormField
          label="Type"
          optional
          error={errors.service_type?.message}
          htmlFor="sv-type"
        >
          <Controller
            control={control}
            name="service_type"
            render={({ field }) => (
              <Select value={field.value ?? ""} onValueChange={field.onChange}>
                <SelectTrigger id="sv-type">
                  <SelectValue placeholder="Unset" />
                </SelectTrigger>
                <SelectContent>
                  {SERVICE_TYPE_OPTIONS.map((t) => (
                    <SelectItem key={t} value={t}>
                      {humanize(t)}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </FormField>
        <FormField
          label="Category"
          optional
          error={errors.category?.message}
          htmlFor="sv-category"
        >
          <Input id="sv-category" placeholder="e.g. Counselling" {...register("category")} />
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
        <label className="flex items-center gap-2 text-sm text-fg">
          <input
            type="checkbox"
            className="size-3.5 cursor-pointer accent-primary"
            {...register("allow_group_sessions")}
          />
          Allow group sessions
        </label>
        {allowGroup ? (
          <div className="grid grid-cols-2 gap-3">
            <FormField
              label="Min group size"
              optional
              error={errors.min_group_size?.message}
              htmlFor="sv-min"
            >
              <Input
                id="sv-min"
                type="number"
                inputMode="numeric"
                min={0}
                className="font-mono"
                {...register("min_group_size")}
              />
            </FormField>
            <FormField
              label="Max group size"
              optional
              error={errors.max_group_size?.message}
              htmlFor="sv-max"
            >
              <Input
                id="sv-max"
                type="number"
                inputMode="numeric"
                min={0}
                className="font-mono"
                {...register("max_group_size")}
              />
            </FormField>
          </div>
        ) : null}
      </FormSection>
    </SheetForm>
  )
}

function toFormValues(s: Service): Values {
  return {
    name: s.name,
    description: s.description ?? "",
    service_type: s.service_type ?? "",
    category: s.category ?? "",
    duration_minutes:
      s.duration_minutes != null ? String(s.duration_minutes) : "",
    allow_group_sessions: Boolean(s.group_settings?.allow_group_sessions),
    min_group_size:
      s.group_settings?.min_group_size != null
        ? String(s.group_settings.min_group_size)
        : "",
    max_group_size:
      s.group_settings?.max_group_size != null
        ? String(s.group_settings.max_group_size)
        : "",
  }
}

function humanize(value: string): string {
  return value
    .split("_")
    .map((w) => w[0] + w.slice(1).toLowerCase())
    .join(" ")
}

export { humanize as humanizeServiceType }
