import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { z } from "zod"

import { surveysApi } from "@/api/endpoints/surveys"
import { FormField } from "@/components/common/FormField"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useApiForm } from "@/hooks/useApiForm"
import { useEntityMutation } from "@/lib/queries"
import { SurveySource } from "@/types/enums"

export const Route = createFileRoute("/surveys/new")({
  component: SurveyCreatePage,
})

const SOURCE_VALUES = [
  SurveySource.GOOGLE_FORMS,
  SurveySource.TYPEFORM,
  SurveySource.SURVEY_MONKEY,
  SurveySource.CUSTOM,
] as const

const surveyCreateSchema = z
  .object({
    client_id: z.string().trim().min(1, "Client ID is required"),
    name: z.string().trim().min(3, "Name must be at least 3 chars"),
    description: z.string().trim().optional(),
    source: z.enum(SOURCE_VALUES as readonly [string, ...string[]]),
    period_start: z.string().min(1, "Start date is required"),
    period_end: z.string().min(1, "End date is required"),
  })
  .refine((v) => Date.parse(v.period_end) >= Date.parse(v.period_start), {
    message: "End date must be on or after the start date",
    path: ["period_end"],
  })

function SurveyCreatePage() {
  const navigate = useNavigate()
  const createSurvey = useEntityMutation({
    resource: "surveys",
    mutationFn: surveysApi.create,
  })

  const { register, formState, submit, serverError } = useApiForm<
    z.infer<typeof surveyCreateSchema>
  >({
    schema: surveyCreateSchema,
    defaultValues: {
      client_id: "",
      name: "",
      description: "",
      source: SurveySource.GOOGLE_FORMS,
      period_start: "",
      period_end: "",
    },
    successToast: "Survey created — webhook ready to wire",
    onSubmit: async (values) => {
      const created = await createSurvey.mutateAsync({
        client_id: values.client_id,
        name: values.name,
        description: values.description?.trim() || null,
        source: values.source as SurveySource,
        period_start: values.period_start,
        period_end: values.period_end,
      })
      navigate({ to: "/surveys/$surveyId", params: { surveyId: created.id } })
    },
  })

  return (
    <div className="content-area-scroll flex-1 min-h-0 overflow-y-auto p-6">
      <div className="mx-auto max-w-2xl space-y-4">
        <h1 className="text-xl font-semibold text-ink">New survey</h1>
        <p className="text-sm text-ink/70">
          Define the response window. The next screen shows the webhook URL + token to paste
          into your survey provider.
        </p>
        <form onSubmit={submit} className="space-y-4" noValidate>
          {serverError && (
            <p
              className="text-sm text-ink border border-ink/30 bg-neutral-50 px-3 py-2"
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
              className="flex w-full border border-ink/30 bg-white px-3 py-2 text-sm text-ink rounded-none"
              {...register("description")}
            />
          </FormField>
          <FormField
            label="Source"
            required
            error={formState.errors.source?.message as string | undefined}
            htmlFor="source"
          >
            <select
              id="source"
              className="flex h-9 w-full border border-ink/30 bg-white px-3 py-2 rounded-none text-ink"
              {...register("source")}
            >
              {SOURCE_VALUES.map((v) => (
                <option key={v} value={v}>
                  {v}
                </option>
              ))}
            </select>
          </FormField>
          <div className="grid gap-4 sm:grid-cols-2">
            <FormField
              label="Period start"
              required
              error={formState.errors.period_start?.message as string | undefined}
              htmlFor="period_start"
            >
              <Input
                id="period_start"
                type="date"
                className="rounded-none"
                {...register("period_start")}
              />
            </FormField>
            <FormField
              label="Period end"
              required
              error={formState.errors.period_end?.message as string | undefined}
              htmlFor="period_end"
            >
              <Input
                id="period_end"
                type="date"
                className="rounded-none"
                {...register("period_end")}
              />
            </FormField>
          </div>
          <div className="flex gap-2">
            <Button
              type="submit"
              disabled={formState.isSubmitting}
              className="rounded-none bg-natural text-white hover:bg-natural-dark"
            >
              {formState.isSubmitting ? "Creating…" : "Create survey"}
            </Button>
            <Button
              type="button"
              variant="secondary"
              className="rounded-none border-ink/30 text-ink"
              onClick={() => navigate({ to: "/surveys" })}
            >
              Cancel
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
