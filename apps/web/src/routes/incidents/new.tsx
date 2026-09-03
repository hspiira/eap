import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { Controller } from "react-hook-form"
import { z } from "zod"

import { incidentsApi } from "@/api/endpoints/incidents"
import { FormField } from "@/components/common/FormField"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { Textarea } from "@/components/ui/textarea"
import { useApiForm } from "@/hooks/useApiForm"
import { useEntityMutation } from "@/lib/queries"
import { IncidentSeverity } from "@/types/enums"

export const Route = createFileRoute("/incidents/new")({
  component: IncidentCreatePage,
})

const SEVERITY_VALUES = [
  IncidentSeverity.LOW,
  IncidentSeverity.MEDIUM,
  IncidentSeverity.HIGH,
  IncidentSeverity.CRITICAL,
] as const

const incidentCreateSchema = z.object({
  client_id: z.string().trim().min(1, "Client ID is required"),
  title: z.string().trim().min(1, "Title is required"),
  description: z.string().trim().min(10, "Add a brief description (≥10 chars)"),
  severity: z.enum(SEVERITY_VALUES as readonly [string, ...string[]]),
  occurred_at: z
    .string()
    .min(1, "Occurred-at time is required")
    .refine((s) => !Number.isNaN(Date.parse(s)), "Must be a valid date/time"),
  affected_population: z.coerce.number().int().min(0, "Must be a non-negative integer"),
})

function IncidentCreatePage() {
  const navigate = useNavigate()
  const createIncident = useEntityMutation({
    resource: "incidents",
    mutationFn: incidentsApi.create,
  })

  const { register, control, formState, submit, serverError } = useApiForm<z.infer<typeof incidentCreateSchema>>({
    schema: incidentCreateSchema,
    defaultValues: {
      client_id: "",
      title: "",
      description: "",
      severity: IncidentSeverity.MEDIUM,
      occurred_at: "",
      affected_population: 0,
    },
    successToast: "Incident logged",
    onSubmit: async (values) => {
      const created = await createIncident.mutateAsync({
        client_id: values.client_id,
        title: values.title,
        description: values.description,
        severity: values.severity as IncidentSeverity,
        occurred_at: new Date(values.occurred_at).toISOString(),
        affected_population: values.affected_population,
      })
      navigate({ to: "/incidents/$incidentId", params: { incidentId: created.id } })
    },
  })

  return (
    <div className="content-area-scroll flex-1 min-h-0 overflow-y-auto p-6">
      <div className="mx-auto max-w-2xl space-y-4">
        <h1 className="text-xl font-semibold text-fg">Log critical incident</h1>
        <form onSubmit={submit} className="space-y-4" noValidate>
          {serverError && (
            <p className="text-sm text-fg border border-fg/30 bg-neutral-50 px-3 py-2" role="alert">
              {serverError}
            </p>
          )}
          <FormField
            label="Client ID"
            required
            error={formState.errors.client_id?.message}
            htmlFor="client_id"
          >
            <Input id="client_id" className="rounded-none" {...register("client_id")} />
          </FormField>
          <FormField
            label="Title"
            required
            error={formState.errors.title?.message}
            htmlFor="title"
          >
            <Input id="title" className="rounded-none" {...register("title")} />
          </FormField>
          <FormField
            label="Description"
            required
            error={formState.errors.description?.message}
            htmlFor="description"
          >
            <Textarea
              id="description"
              rows={4}
              className="rounded-none"
              {...register("description")}
            />
          </FormField>
          <div className="grid gap-4 sm:grid-cols-2">
            <FormField
              label="Severity"
              required
              error={formState.errors.severity?.message}
              htmlFor="severity"
            >
              <Controller
                control={control}
                name="severity"
                render={({ field }) => (
                  <Select value={field.value} onValueChange={field.onChange}>
                    <SelectTrigger id="severity">
                      <SelectValue />
                    </SelectTrigger>
                    <SelectContent>
                      {SEVERITY_VALUES.map((s) => (
                        <SelectItem key={s} value={s}>
                          {s}
                        </SelectItem>
                      ))}
                    </SelectContent>
                  </Select>
                )}
              />
            </FormField>
            <FormField
              label="Affected population"
              required
              error={formState.errors.affected_population?.message}
              htmlFor="affected_population"
            >
              <Input
                id="affected_population"
                type="number"
                min={0}
                className="rounded-none"
                {...register("affected_population")}
              />
            </FormField>
          </div>
          <FormField
            label="Occurred at"
            required
            error={formState.errors.occurred_at?.message}
            htmlFor="occurred_at"
          >
            <Input
              id="occurred_at"
              type="datetime-local"
              className="rounded-none"
              {...register("occurred_at")}
            />
          </FormField>
          <div className="flex gap-2">
            <Button
              type="submit"
              disabled={formState.isSubmitting}
              className="rounded-none bg-primary text-white hover:bg-primary"
            >
              {formState.isSubmitting ? "Logging…" : "Log incident"}
            </Button>
            <Button
              type="button"
              variant="secondary"
              className="rounded-none border-fg/30 text-fg"
              onClick={() => navigate({ to: "/incidents" })}
            >
              Cancel
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
