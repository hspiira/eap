import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { Controller } from "react-hook-form"
import { z } from "zod"

import { serviceSessionsApi } from "@/api/endpoints/service-sessions"
import { DiagnosisSelector } from "@/components/common/DiagnosisSelector"
import { FormField } from "@/components/common/FormField"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useApiForm } from "@/hooks/useApiForm"

export const Route = createFileRoute("/service-sessions/new")({
  component: ServiceSessionCreatePage,
})

const FREETEXT_FALLBACK_ENABLED =
  typeof import.meta !== "undefined" &&
  import.meta.env?.VITE_DIAGNOSIS_FREETEXT_FALLBACK === "true"

const sessionCreateSchema = z.object({
  service_id: z.string().trim().min(1, "Service ID is required"),
  person_id: z.string().trim().min(1, "Person ID is required"),
  scheduled_at: z
    .string()
    .min(1, "Scheduled time is required")
    .refine((s) => !Number.isNaN(Date.parse(s)), "Must be a valid date/time"),
  diagnosis_id: z.string().nullable().optional(),
  diagnosis_text: z.string().optional(),
})

function ServiceSessionCreatePage() {
  const navigate = useNavigate()

  const { register, control, formState, submit, serverError } = useApiForm<
    z.infer<typeof sessionCreateSchema>
  >({
    schema: sessionCreateSchema,
    defaultValues: {
      service_id: "",
      person_id: "",
      scheduled_at: "",
      diagnosis_id: null,
      diagnosis_text: "",
    },
    successToast: "Session created",
    onSubmit: async (values) => {
      await serviceSessionsApi.create({
        service_id: values.service_id,
        person_id: values.person_id,
        scheduled_at: new Date(values.scheduled_at).toISOString(),
        diagnosis_id: values.diagnosis_id || null,
        diagnosis_text: FREETEXT_FALLBACK_ENABLED
          ? values.diagnosis_text || null
          : null,
      })
      navigate({ to: "/service-sessions" })
    },
  })

  return (
    <div className="p-6 max-w-md">
      <h1 className="text-xl font-semibold text-ink">Add session</h1>
      <form onSubmit={submit} className="mt-6 space-y-4" noValidate>
        {serverError && <p className="text-sm text-ink" role="alert">{serverError}</p>}
        <FormField
          label="Service ID"
          required
          error={formState.errors.service_id?.message as string | undefined}
          htmlFor="service_id"
        >
          <Input id="service_id" className="rounded-none" {...register("service_id")} />
        </FormField>
        <FormField
          label="Person ID"
          required
          error={formState.errors.person_id?.message as string | undefined}
          htmlFor="person_id"
        >
          <Input id="person_id" className="rounded-none" {...register("person_id")} />
        </FormField>
        <FormField
          label="Scheduled at"
          required
          error={formState.errors.scheduled_at?.message as string | undefined}
          htmlFor="scheduled_at"
        >
          <Input
            id="scheduled_at"
            type="datetime-local"
            className="rounded-none"
            {...register("scheduled_at")}
          />
        </FormField>
        <FormField
          label="Diagnosis"
          error={formState.errors.diagnosis_id?.message as string | undefined}
          htmlFor="diagnosis"
        >
          <Controller
            control={control}
            name="diagnosis_id"
            render={({ field }) => (
              <DiagnosisSelector
                value={field.value ?? null}
                onChange={(id) => field.onChange(id ?? null)}
              />
            )}
          />
        </FormField>
        {FREETEXT_FALLBACK_ENABLED && (
          <FormField
            label="Diagnosis (free text — legacy)"
            error={formState.errors.diagnosis_text?.message as string | undefined}
            htmlFor="diagnosis_text"
          >
            <Input
              id="diagnosis_text"
              className="rounded-none"
              placeholder="Only use if no taxonomy match exists"
              {...register("diagnosis_text")}
            />
          </FormField>
        )}
        <div className="flex gap-2">
          <Button type="submit" disabled={formState.isSubmitting} className="rounded-none">
            {formState.isSubmitting ? "Creating…" : "Create session"}
          </Button>
          <Button
            type="button"
            variant="secondary"
            className="rounded-none"
            onClick={() => navigate({ to: "/service-sessions" })}
          >
            Cancel
          </Button>
        </div>
      </form>
    </div>
  )
}
