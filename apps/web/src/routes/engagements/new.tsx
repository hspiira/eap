import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { z } from "zod"

import { engagementsApi } from "@/api/endpoints/engagements"
import { FormField } from "@/components/common/FormField"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useApiForm } from "@/hooks/useApiForm"
import { useEntityMutation } from "@/lib/queries"
import { EngagementType } from "@/types/enums"

export const Route = createFileRoute("/engagements/new")({
  component: EngagementCreatePage,
})

const TYPE_VALUES = [
  EngagementType.POLICY_DRAFT,
  EngagementType.TRAINING,
  EngagementType.ASSESSMENT,
  EngagementType.ADVISORY,
  EngagementType.AUDIT,
  EngagementType.OTHER,
] as const

const engagementCreateSchema = z
  .object({
    client_id: z.string().trim().min(1, "Client ID is required"),
    name: z.string().trim().min(3, "Name must be at least 3 chars"),
    description: z.string().trim().optional(),
    engagement_type: z.enum(TYPE_VALUES as readonly [string, ...string[]]),
    start_date: z.string().min(1, "Start date is required"),
    due_date: z.string().optional(),
    hourly_rate: z.coerce.number().min(0).optional(),
    currency: z.string().trim().optional(),
    budget_hours: z.coerce.number().min(0).optional(),
    lead_user_id: z.string().trim().optional(),
  })
  .refine(
    (v) => !v.due_date || Date.parse(v.due_date) >= Date.parse(v.start_date),
    { message: "Due date must be on or after the start date", path: ["due_date"] },
  )

function EngagementCreatePage() {
  const navigate = useNavigate()
  const createEngagement = useEntityMutation({
    resource: "engagements",
    mutationFn: engagementsApi.create,
  })

  const { register, formState, submit, serverError } = useApiForm<
    z.infer<typeof engagementCreateSchema>
  >({
    schema: engagementCreateSchema,
    defaultValues: {
      client_id: "",
      name: "",
      description: "",
      engagement_type: EngagementType.POLICY_DRAFT,
      start_date: "",
      due_date: "",
      hourly_rate: undefined,
      currency: "USD",
      budget_hours: undefined,
      lead_user_id: "",
    },
    successToast: "Engagement created",
    onSubmit: async (values) => {
      const created = await createEngagement.mutateAsync({
        client_id: values.client_id,
        name: values.name,
        description: values.description?.trim() || null,
        engagement_type: values.engagement_type as EngagementType,
        start_date: values.start_date,
        due_date: values.due_date || null,
        hourly_rate: values.hourly_rate ?? null,
        currency: values.currency?.trim() || null,
        budget_hours: values.budget_hours ?? null,
        lead_user_id: values.lead_user_id?.trim() || null,
      })
      navigate({ to: "/engagements/$engagementId", params: { engagementId: created.id } })
    },
  })

  return (
    <div className="content-area-scroll flex-1 min-h-0 overflow-y-auto p-6">
      <div className="mx-auto max-w-2xl space-y-4">
        <h1 className="text-xl font-semibold text-fg">New engagement</h1>
        <form onSubmit={submit} className="space-y-4" noValidate>
          {serverError && (
            <p
              className="text-sm text-fg border border-fg/30 bg-neutral-50 px-3 py-2"
              role="alert"
            >
              {serverError}
            </p>
          )}
          <FormField
            label="Client ID"
            required
            error={formState.errors.client_id?.message as string | undefined}
            htmlFor="client_id"
          >
            <Input id="client_id" className="rounded-none" {...register("client_id")} />
          </FormField>
          <FormField
            label="Name"
            required
            error={formState.errors.name?.message as string | undefined}
            htmlFor="name"
          >
            <Input id="name" className="rounded-none" {...register("name")} />
          </FormField>
          <FormField
            label="Description"
            error={formState.errors.description?.message as string | undefined}
            htmlFor="description"
          >
            <textarea
              id="description"
              rows={3}
              className="flex w-full border border-fg/30 bg-white px-3 py-2 text-sm text-fg rounded-none"
              {...register("description")}
            />
          </FormField>
          <FormField
            label="Type"
            required
            error={formState.errors.engagement_type?.message as string | undefined}
            htmlFor="engagement_type"
          >
            <select
              id="engagement_type"
              className="flex h-9 w-full border border-fg/30 bg-white px-3 py-2 rounded-none text-fg"
              {...register("engagement_type")}
            >
              {TYPE_VALUES.map((v) => (
                <option key={v} value={v}>
                  {v}
                </option>
              ))}
            </select>
          </FormField>
          <div className="grid gap-4 sm:grid-cols-2">
            <FormField
              label="Start date"
              required
              error={formState.errors.start_date?.message as string | undefined}
              htmlFor="start_date"
            >
              <Input
                id="start_date"
                type="date"
                className="rounded-none"
                {...register("start_date")}
              />
            </FormField>
            <FormField
              label="Due date"
              error={formState.errors.due_date?.message as string | undefined}
              htmlFor="due_date"
            >
              <Input
                id="due_date"
                type="date"
                className="rounded-none"
                {...register("due_date")}
              />
            </FormField>
          </div>
          <div className="grid gap-4 sm:grid-cols-3">
            <FormField
              label="Hourly rate"
              error={formState.errors.hourly_rate?.message as string | undefined}
              htmlFor="hourly_rate"
            >
              <Input
                id="hourly_rate"
                type="number"
                min={0}
                step="0.01"
                className="rounded-none"
                {...register("hourly_rate")}
              />
            </FormField>
            <FormField
              label="Currency"
              error={formState.errors.currency?.message as string | undefined}
              htmlFor="currency"
            >
              <Input id="currency" className="rounded-none" {...register("currency")} />
            </FormField>
            <FormField
              label="Budget (hours)"
              error={formState.errors.budget_hours?.message as string | undefined}
              htmlFor="budget_hours"
            >
              <Input
                id="budget_hours"
                type="number"
                min={0}
                className="rounded-none"
                {...register("budget_hours")}
              />
            </FormField>
          </div>
          <FormField
            label="Lead user ID"
            error={formState.errors.lead_user_id?.message as string | undefined}
            htmlFor="lead_user_id"
          >
            <Input id="lead_user_id" className="rounded-none" {...register("lead_user_id")} />
          </FormField>
          <div className="flex gap-2">
            <Button
              type="submit"
              disabled={formState.isSubmitting}
              className="rounded-none bg-primary text-white hover:bg-primary"
            >
              {formState.isSubmitting ? "Creating…" : "Create engagement"}
            </Button>
            <Button
              type="button"
              variant="secondary"
              className="rounded-none border-fg/30 text-fg"
              onClick={() => navigate({ to: "/engagements" })}
            >
              Cancel
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
