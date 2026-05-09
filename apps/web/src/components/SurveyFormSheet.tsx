import { useEffect, useState } from "react"

import { useQueryClient } from "@tanstack/react-query"
import { z } from "zod"

import { clientsApi } from "@/api/endpoints/clients"
import { surveysApi } from "@/api/endpoints/surveys"
import { FormField } from "@/components/common/FormField"
import { FormSection } from "@/components/common/FormSection"
import { SheetForm } from "@/components/common/SheetForm"
import { Input } from "@/components/ui/input"
import { useApiForm } from "@/hooks/useApiForm"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import { useEntityList } from "@/lib/queries"
import type { Client, Survey } from "@/types/entities"
import { SurveySource } from "@/types/enums"

const SOURCE_VALUES = [
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

const SELECT_CLASS =
  "flex h-9 w-full rounded-sm border border-fg/20 bg-bg px-3 text-sm text-fg shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg"

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
  const queryClient = useQueryClient()
  const lockedClientId = clientId

  const initial: Values = { ...EMPTY, client_id: clientId ?? "" }

  const { register, reset, formState, submit, serverError, setValue, watch } =
    useApiForm<Values>({
      schema,
      defaultValues: initial,
      successToast: "Survey created — webhook ready to wire",
      onSubmit: async (values) => {
        const created = await surveysApi.create({
          client_id: values.client_id,
          name: values.name,
          description: values.description?.trim() || null,
          source: values.source as SurveySource,
          period_start: values.period_start,
          period_end: values.period_end,
        })
        await queryClient.invalidateQueries({ queryKey: ["surveys", "list"] })
        onSaved?.(created)
        onOpenChange(false)
        reset(EMPTY)
      },
    })

  const watchedClient = watch("client_id")

  useEffect(() => {
    if (!open) return
    reset({ ...EMPTY, client_id: clientId ?? "" })
  }, [open, clientId, reset])

  const errors = formState.errors as Record<string, { message?: string }>

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
        <input type="hidden" {...register("client_id")} />
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
          <select id="sf-source" className={SELECT_CLASS} {...register("source")}>
            {SOURCE_VALUES.map((v) => (
              <option key={v} value={v}>
                {v}
              </option>
            ))}
          </select>
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
        {resolved ? clientInitial(resolved.name) : "··"}
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

function ClientPicker({
  value,
  onChange,
}: {
  value: string
  onChange: (id: string) => void
}) {
  const [query, setQuery] = useState("")
  const debounced = useDebouncedValue(query.trim(), 250)
  const list = useEntityList<Client>({
    resource: "clients",
    params: { page: 1, limit: 8, search: debounced || undefined },
    listFn: clientsApi.list,
  })
  const items = list.data?.items ?? []
  const selected = items.find((c) => c.id === value)

  if (selected) {
    return (
      <div className="flex items-center gap-2.5 rounded-sm border border-fg/15 bg-surface px-3 py-2">
        <span
          aria-hidden
          className="grid size-7 shrink-0 place-items-center bg-primary/10 font-mono text-[10px] font-semibold text-primary"
        >
          {clientInitial(selected.name)}
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-fg">{selected.name}</p>
          <p className="truncate font-mono text-[11px] text-fg/55">{selected.code}</p>
        </div>
        <button
          type="button"
          onClick={() => onChange("")}
          className="shrink-0 rounded-sm px-2 py-1 text-xs font-medium text-fg/65 hover:bg-surface-hover hover:text-fg"
        >
          Change
        </button>
      </div>
    )
  }
  return (
    <div className="space-y-1.5">
      <Input
        placeholder="Search clients by name or code…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <div className="max-h-48 overflow-y-auto rounded-sm border border-fg/15 bg-bg">
        {list.isPending ? (
          <p className="px-3 py-2 text-xs text-fg/55">Loading…</p>
        ) : items.length === 0 ? (
          <p className="px-3 py-2 text-xs text-fg/55">
            {debounced ? "No clients match." : "Start typing to search clients."}
          </p>
        ) : (
          <ul className="divide-y divide-fg/8">
            {items.map((c) => (
              <li key={c.id}>
                <button
                  type="button"
                  onClick={() => onChange(c.id)}
                  className="flex w-full items-center gap-2.5 px-3 py-2 text-left transition-colors hover:bg-surface-hover focus-visible:bg-surface-hover focus-visible:outline-none"
                >
                  <span
                    aria-hidden
                    className="grid size-6 shrink-0 place-items-center bg-primary/10 font-mono text-[10px] font-semibold text-primary"
                  >
                    {clientInitial(c.name)}
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm font-medium text-fg">
                      {c.name}
                    </span>
                    <span className="block truncate font-mono text-[11px] text-fg/55">
                      {c.code}
                    </span>
                  </span>
                </button>
              </li>
            ))}
          </ul>
        )}
      </div>
    </div>
  )
}

function clientInitial(name: string): string {
  const trimmed = name.trim()
  if (!trimmed) return "·"
  const parts = trimmed.split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return trimmed.slice(0, 2).toUpperCase()
}
