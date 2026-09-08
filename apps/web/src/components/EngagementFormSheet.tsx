import { z } from "zod"

import { clientsApi } from "@/api/endpoints/clients"
import { engagementsApi } from "@/api/endpoints/engagements"
import type { EngagementCreate } from "@/api/generated"
import { ClientPicker } from "@/components/common/EntityPicker"
import { FormField } from "@/components/common/FormField"
import { FormSection } from "@/components/common/FormSection"
import { SheetForm } from "@/components/common/SheetForm"
import { Input } from "@/components/ui/input"
import { useEntityFormSheet } from "@/hooks/useEntityFormSheet"
import { nameInitials } from "@/lib/display"
import { useEntityList } from "@/lib/queries"
import { cn } from "@/lib/utils"
import type { Client, Engagement } from "@/types/entities"

const schema = z
  .object({
    client_id: z.string().trim().min(1, "Client is required"),
    name: z.string().trim().min(3, "Name must be at least 3 characters"),
    description: z.string().trim().optional(),
    period_start: z.string().optional(),
    period_end: z.string().optional(),
  })
  .refine(
    (v) =>
      !v.period_start || !v.period_end || Date.parse(v.period_end) >= Date.parse(v.period_start),
    { path: ["period_end"], message: "Period end must be on or after the start" },
  )

type Values = z.infer<typeof schema>

const EMPTY: Values = {
  client_id: "",
  name: "",
  description: "",
  period_start: "",
  period_end: "",
}

interface EngagementFormSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** When set, locks the client. */
  clientId?: string
  client?: Client | null
  onSaved?: (engagement: Engagement) => void
}

export function EngagementFormSheet({
  open,
  onOpenChange,
  clientId,
  client,
  onSaved,
}: EngagementFormSheetProps) {
  const lockedClientId = clientId

  const { register, formState, submit, serverError, setValue, watch } = useEntityFormSheet<
    Values,
    Parameters<typeof engagementsApi.create>[0],
    Engagement,
    Engagement
  >({
    resource: "engagements",
    schema,
    defaultValues: { ...EMPTY, client_id: clientId ?? "" },
    open,
    onOpenChange,
    parsePayload: (values): EngagementCreate => ({
      client_id: values.client_id,
      name: values.name,
      description: values.description?.trim() || null,
      period_start: values.period_start || null,
      period_end: values.period_end || null,
    }),
    save: ({ payload }) => engagementsApi.create(payload),
    successToast: { create: "Engagement created" },
    onSaved,
  })

  const watchedClient = watch("client_id")
  const errors = formState.errors

  return (
    <SheetForm
      open={open}
      onOpenChange={onOpenChange}
      title="New consultancy engagement"
      description="Scope the work and the agreed period. Deliverables and hours are logged from the engagement detail page."
      size="lg"
      onSubmit={submit}
      isSubmitting={formState.isSubmitting}
      serverError={serverError}
      submitLabel="Create engagement"
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
        <FormField label="Name" required error={errors.name?.message} htmlFor="ef-name">
          <Input
            id="ef-name"
            placeholder="e.g. Wellness policy refresh: Q3"
            {...register("name")}
          />
        </FormField>
        <FormField label="Description" error={errors.description?.message} htmlFor="ef-description">
          <Input
            id="ef-description"
            placeholder="Internal notes: appears on the engagement detail."
            {...register("description")}
          />
        </FormField>
      </FormSection>

      <FormSection title="Period">
        <div className="grid grid-cols-2 gap-3">
          <FormField
            label="Period start"
            error={errors.period_start?.message}
            htmlFor="ef-period-start"
          >
            <Input id="ef-period-start" type="date" {...register("period_start")} />
          </FormField>
          <FormField
            label="Period end"
            description="A past end date with the work undelivered shows as Overdue."
            error={errors.period_end?.message}
            htmlFor="ef-period-end"
          >
            <Input id="ef-period-end" type="date" {...register("period_end")} />
          </FormField>
        </div>
      </FormSection>
    </SheetForm>
  )
}

function LockedClientSummary({ clientId, client }: { clientId: string; client: Client | null }) {
  const enabled = !client && Boolean(clientId)
  const detail = useEntityList<Client>({
    resource: "clients",
    params: { page: 1, limit: 1, search: clientId },
    listFn: clientsApi.list,
    enabled,
  })
  const resolved = client ?? (detail.data?.items ?? []).find((c) => c.id === clientId) ?? null
  return (
    <div className="flex items-center gap-2.5 rounded-sm border border-fg/15 bg-surface px-3 py-2">
      <span
        aria-hidden
        className="grid size-7 shrink-0 place-items-center bg-primary/10 text-[10px] font-semibold text-primary"
      >
        {resolved ? nameInitials(resolved.name) : "··"}
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate text-sm font-medium text-fg">
          {resolved?.name ?? "Selected client"}
        </p>
        <p className={cn("truncate text-[11px] text-fg-muted", !resolved?.code && "font-mono")}>
          {resolved?.code || clientId}
        </p>
      </div>
      <span className="shrink-0 rounded-sm border border-fg/15 bg-bg px-1.5 py-0.5 text-[10px] font-medium tracking-wide text-fg-muted">
        Locked
      </span>
    </div>
  )
}
