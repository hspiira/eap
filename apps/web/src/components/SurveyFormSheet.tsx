
import { Controller } from "react-hook-form"
import { z } from "zod"

import { clientsApi } from "@/api/endpoints/clients"
import { surveysApi } from "@/api/endpoints/surveys"
import { ClientPicker } from "@/components/common/EntityPicker"
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
import { nameInitials } from "@/lib/display"
import { useEntityList } from "@/lib/queries"
import type { Client, Survey } from "@/types/entities"
import { SurveySource } from "@/types/enums"

const SOURCE_VALUES = [
  SurveySource.MICROSOFT_FORMS,
  SurveySource.GOOGLE_FORMS,
  SurveySource.TYPEFORM,
  SurveySource.SURVEY_MONKEY,
  SurveySource.CUSTOM,
] as const

const schema = z
  .object({
    client_id: z.string().trim().min(1, "Client is required"),
    name: z.string().trim().min(3, "Name must be at least 3 characters"),
    description: z.string().trim().optional(),
    source: z.enum(SOURCE_VALUES as readonly [string, ...string[]]),
    period_start: z.string().min(1, "Start date is required"),
    period_end: z.string().min(1, "End date is required"),
  })
  .refine((v) => Date.parse(v.period_end) >= Date.parse(v.period_start), {
    path: ["period_end"],
    message: "End date must be on or after start date",
  })

type Values = z.infer<typeof schema>

const EMPTY: Values = {
  client_id: "",
  name: "",
  description: "",
  source: SurveySource.GOOGLE_FORMS,
  period_start: "",
  period_end: "",
}

interface SurveyFormSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** When set, locks the client. */
  clientId?: string
  client?: Client | null
  onSaved?: (survey: Survey) => void
}

export function SurveyFormSheet({
  open,
  onOpenChange,
  clientId,
  client,
  onSaved,
}: SurveyFormSheetProps) {
  const lockedClientId = clientId

  const { register, control, formState, submit, serverError, setValue, watch } = useEntityFormSheet<
    Values,
    Parameters<typeof surveysApi.create>[0],
    Survey,
    Survey
  >({
    resource: "surveys",
    schema,
    defaultValues: { ...EMPTY, client_id: clientId ?? "" },
    open,
    onOpenChange,
    parsePayload: (values) => ({
      client_id: values.client_id,
      name: values.name,
      description: values.description?.trim() || null,
      source: values.source as SurveySource,
      period_start: values.period_start,
      period_end: values.period_end,
    }),
    save: ({ payload }) => surveysApi.create(payload),
    successToast: { create: "Survey created — webhook ready to wire" },
    onSaved,
  })

  const watchedClient = watch("client_id")

  const errors = formState.errors

  return (
    <SheetForm
      open={open}
      onOpenChange={onOpenChange}
      title="New survey"
      description="Define the response window. After saving, copy the webhook URL + token from the detail page into your survey provider."
      size="md"
      onSubmit={submit}
      isSubmitting={formState.isSubmitting}
      serverError={serverError}
      submitLabel="Create survey"
      submittingLabel="Creating…"
    >
      <FormSection title="Client">
        <FormField label="Client" required error={errors.client_id?.message}>
          {lockedClientId ? (
            <LockedClientSummary clientId={lockedClientId} client={client ?? null} />
          ) : (
            <ClientPicker
              value={watchedClient ?? ""}
              onChange={(id) =>
                setValue("client_id", id, { shouldValidate: true, shouldDirty: true })
              }
            />
          )}
        </FormField>
        <Input type="hidden" {...register("client_id")} />
      </FormSection>

      <FormSection title="Identity">
        <FormField label="Name" required error={errors.name?.message} htmlFor="sf-name">
          <Input
            id="sf-name"
            placeholder="e.g. Q2 post-engagement satisfaction"
            {...register("name")}
          />
        </FormField>
        <FormField
          label="Description"
          optional
          error={errors.description?.message}
          htmlFor="sf-description"
        >
          <Input
            id="sf-description"
            placeholder="Internal notes for the team."
            {...register("description")}
          />
        </FormField>
      </FormSection>

      <FormSection title="Source" description="The platform hosting the form.">
        <FormField label="Provider" required error={errors.source?.message} htmlFor="sf-source">
          <Controller
            control={control}
            name="source"
            render={({ field }) => (
              <Select value={field.value ?? ""} onValueChange={field.onChange}>
                <SelectTrigger id="sf-source">
                  <SelectValue />
                </SelectTrigger>
                <SelectContent>
                  {SOURCE_VALUES.map((v) => (
                    <SelectItem key={v} value={v}>
                      {v}
                    </SelectItem>
                  ))}
                </SelectContent>
              </Select>
            )}
          />
        </FormField>
      </FormSection>

      <FormSection title="Response window">
        <div className="grid grid-cols-2 gap-3">
          <FormField
            label="Start date"
            required
            error={errors.period_start?.message}
            htmlFor="sf-start"
          >
            <Input id="sf-start" type="date" {...register("period_start")} />
          </FormField>
          <FormField
            label="End date"
            required
            description="The survey closes for new responses at the end of this date."
            error={errors.period_end?.message}
            htmlFor="sf-end"
          >
            <Input id="sf-end" type="date" {...register("period_end")} />
          </FormField>
        </div>
      </FormSection>
    </SheetForm>
  )
}

function LockedClientSummary({
  clientId,
  client,
}: {
  clientId: string
  client: Client | null
}) {
  const enabled = !client && Boolean(clientId)
  const detail = useEntityList<Client>({
    resource: "clients",
    params: { page: 1, limit: 1, search: clientId },
    listFn: clientsApi.list,
    enabled,
  })
  const resolved =
    client ?? (detail.data?.items ?? []).find((c) => c.id === clientId) ?? null
  return (
    <div className="flex items-center gap-2.5 rounded-sm border border-fg/15 bg-surface px-3 py-2">
      <span
        aria-hidden
        className="grid size-7 shrink-0 place-items-center bg-primary/10 font-mono text-[10px] font-semibold text-primary"
      >
        {resolved ? nameInitials(resolved.name) : "··"}
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-fg">
          {resolved?.name ?? "Selected client"}
        </p>
        <p className="truncate font-mono text-[11px] text-fg/55">
          {resolved?.code ?? clientId}
        </p>
      </div>
      <span className="shrink-0 rounded-sm border border-fg/15 bg-bg px-1.5 py-0.5 text-[10px] font-medium tracking-wide text-fg/55">
        Locked
      </span>
    </div>
  )
}

