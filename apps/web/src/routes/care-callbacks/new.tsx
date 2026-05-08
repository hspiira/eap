import { useQuery } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { z } from "zod"

import { careCallbacksApi } from "@/api/endpoints/care-callbacks"
import { questionnairesApi } from "@/api/endpoints/questionnaires"
import { FormField } from "@/components/common/FormField"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { useApiForm } from "@/hooks/useApiForm"
import { useEntityMutation } from "@/lib/queries"
import { CallbackSamplingStrategy, QuestionnaireAdministration } from "@/types/enums"

export const Route = createFileRoute("/care-callbacks/new")({
  component: CampaignCreatePage,
})

const SAMPLING_VALUES = [
  CallbackSamplingStrategy.FULL,
  CallbackSamplingStrategy.RANDOM,
  CallbackSamplingStrategy.STRATIFIED,
] as const

const campaignCreateSchema = z
  .object({
    client_id: z.string().trim().min(1, "Client ID is required"),
    name: z.string().trim().min(3, "Name must be at least 3 chars"),
    description: z.string().trim().optional(),
    period_start: z.string().min(1, "Start date is required"),
    period_end: z.string().min(1, "End date is required"),
    sampling: z.enum(SAMPLING_VALUES as readonly [string, ...string[]]),
    sample_size: z.coerce.number().int().min(1).optional(),
    counsellor_user_ids_csv: z
      .string()
      .trim()
      .min(1, "List at least one counsellor user ID"),
    questionnaire_code: z.string().min(1, "Pick a triage questionnaire"),
    followup_questionnaire_code: z.string().optional(),
  })
  .refine((v) => Date.parse(v.period_end) >= Date.parse(v.period_start), {
    message: "End date must be on or after the start date",
    path: ["period_end"],
  })
  .refine(
    (v) => v.sampling === CallbackSamplingStrategy.FULL || (v.sample_size ?? 0) > 0,
    { message: "Sample size required for non-Full sampling", path: ["sample_size"] },
  )

function CampaignCreatePage() {
  const navigate = useNavigate()
  const questionnairesQuery = useQuery({
    queryKey: ["questionnaires", "list"],
    queryFn: () => questionnairesApi.list(),
    staleTime: 60_000,
  })
  const allQuestionnaires = questionnairesQuery.data ?? []
  const triageOptions = allQuestionnaires.filter(
    (q) => q.administration !== QuestionnaireAdministration.POST,
  )
  const followupOptions = allQuestionnaires.filter(
    (q) => q.administration === QuestionnaireAdministration.POST,
  )

  const createCampaign = useEntityMutation({
    resource: "care-callback-campaigns",
    mutationFn: careCallbacksApi.createCampaign,
  })

  const { register, formState, submit, serverError } = useApiForm<
    z.infer<typeof campaignCreateSchema>
  >({
    schema: campaignCreateSchema,
    defaultValues: {
      client_id: "",
      name: "",
      description: "",
      period_start: "",
      period_end: "",
      sampling: CallbackSamplingStrategy.FULL,
      sample_size: undefined,
      counsellor_user_ids_csv: "",
      questionnaire_code: "joseph-7var-v1",
      followup_questionnaire_code: "wos5-post-v1",
    },
    successToast: "Campaign created",
    onSubmit: async (values) => {
      const counsellor_user_ids = values.counsellor_user_ids_csv
        .split(",")
        .map((s) => s.trim())
        .filter(Boolean)
      const created = await createCampaign.mutateAsync({
        client_id: values.client_id,
        name: values.name,
        description: values.description?.trim() || null,
        period_start: values.period_start,
        period_end: values.period_end,
        sampling: values.sampling as CallbackSamplingStrategy,
        sample_size:
          values.sampling === CallbackSamplingStrategy.FULL ? null : (values.sample_size ?? null),
        counsellor_user_ids,
        questionnaire_code: values.questionnaire_code,
        followup_questionnaire_code: values.followup_questionnaire_code || null,
      })
      navigate({ to: "/care-callbacks/$campaignId", params: { campaignId: created.id } })
    },
  })

  return (
    <div className="content-area-scroll flex-1 min-h-0 overflow-y-auto p-6">
      <div className="mx-auto max-w-2xl space-y-4">
        <h1 className="text-xl font-semibold text-fg">New care-callback campaign</h1>
        <p className="text-sm text-fg/70">
          Define audience, sampling, and the counsellor pool. Cases are generated to each
          counsellor's worklist when the campaign is activated.
        </p>
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
          <div className="grid gap-4 sm:grid-cols-2">
            <FormField
              label="Sampling"
              required
              error={formState.errors.sampling?.message as string | undefined}
              htmlFor="sampling"
            >
              <select
                id="sampling"
                className="flex h-9 w-full border border-fg/30 bg-white px-3 py-2 rounded-none text-fg"
                {...register("sampling")}
              >
                {SAMPLING_VALUES.map((s) => (
                  <option key={s} value={s}>
                    {s}
                  </option>
                ))}
              </select>
            </FormField>
            <FormField
              label="Sample size"
              error={formState.errors.sample_size?.message as string | undefined}
              htmlFor="sample_size"
            >
              <Input
                id="sample_size"
                type="number"
                min={1}
                placeholder="Required unless sampling = Full"
                className="rounded-none"
                {...register("sample_size")}
              />
            </FormField>
          </div>
          <FormField
            label="Counsellor user IDs (comma-separated)"
            required
            error={formState.errors.counsellor_user_ids_csv?.message as string | undefined}
            htmlFor="counsellor_user_ids_csv"
          >
            <Input
              id="counsellor_user_ids_csv"
              placeholder="user-helen, user-mary"
              className="rounded-none"
              {...register("counsellor_user_ids_csv")}
            />
          </FormField>
          <div className="grid gap-4 sm:grid-cols-2">
            <FormField
              label="Triage questionnaire"
              required
              error={formState.errors.questionnaire_code?.message as string | undefined}
              htmlFor="questionnaire_code"
            >
              <select
                id="questionnaire_code"
                className="flex h-9 w-full border border-fg/30 bg-white px-3 py-2 rounded-none text-fg"
                {...register("questionnaire_code")}
              >
                {triageOptions.map((q) => (
                  <option key={q.code} value={q.code}>
                    {q.title}
                  </option>
                ))}
              </select>
            </FormField>
            <FormField
              label="Follow-up questionnaire"
              error={formState.errors.followup_questionnaire_code?.message as string | undefined}
              htmlFor="followup_questionnaire_code"
            >
              <select
                id="followup_questionnaire_code"
                className="flex h-9 w-full border border-fg/30 bg-white px-3 py-2 rounded-none text-fg"
                {...register("followup_questionnaire_code")}
              >
                <option value="">— None —</option>
                {followupOptions.map((q) => (
                  <option key={q.code} value={q.code}>
                    {q.title}
                  </option>
                ))}
              </select>
            </FormField>
          </div>
          <div className="flex gap-2">
            <Button
              type="submit"
              disabled={formState.isSubmitting}
              className="rounded-none bg-primary text-white hover:bg-primary"
            >
              {formState.isSubmitting ? "Creating…" : "Create campaign"}
            </Button>
            <Button
              type="button"
              variant="secondary"
              className="rounded-none border-fg/30 text-fg"
              onClick={() => navigate({ to: "/care-callbacks" })}
            >
              Cancel
            </Button>
          </div>
        </form>
      </div>
    </div>
  )
}
