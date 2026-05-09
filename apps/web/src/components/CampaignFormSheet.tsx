import { useEffect, useState } from "react"

import { useQueryClient } from "@tanstack/react-query"
import { useQuery } from "@tanstack/react-query"
import { X } from "lucide-react"
import { z } from "zod"

import { careCallbacksApi } from "@/api/endpoints/care-callbacks"
import { clientsApi } from "@/api/endpoints/clients"
import { questionnairesApi } from "@/api/endpoints/questionnaires"
import { usersApi } from "@/api/endpoints/users"
import { FormField } from "@/components/common/FormField"
import { FormSection } from "@/components/common/FormSection"
import { SheetForm } from "@/components/common/SheetForm"
import { Input } from "@/components/ui/input"
import { useApiForm } from "@/hooks/useApiForm"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import { useEntityList } from "@/lib/queries"
import type { CallbackCampaign, Client, User } from "@/types/entities"
import {
  CallbackSamplingStrategy,
  QuestionnaireAdministration,
} from "@/types/enums"

const SAMPLING_VALUES = [
  CallbackSamplingStrategy.FULL,
  CallbackSamplingStrategy.RANDOM,
  CallbackSamplingStrategy.STRATIFIED,
] as const

const schema = z
  .object({
    client_id: z.string().trim().min(1, "Client is required"),
    name: z.string().trim().min(3, "Name must be at least 3 characters"),
    description: z.string().trim().optional(),
    period_start: z.string().min(1, "Start date is required"),
    period_end: z.string().min(1, "End date is required"),
    sampling: z.enum(SAMPLING_VALUES as readonly [string, ...string[]]),
    sample_size: z.string().optional(),
    counsellor_user_ids: z.array(z.string()).min(1, "Pick at least one counsellor"),
    questionnaire_code: z.string().min(1, "Pick a triage questionnaire"),
    followup_questionnaire_code: z.string().optional(),
  })
  .refine((v) => Date.parse(v.period_end) >= Date.parse(v.period_start), {
    path: ["period_end"],
    message: "End date must be on or after start date",
  })
  .refine(
    (v) =>
      v.sampling === CallbackSamplingStrategy.FULL ||
      (Number(v.sample_size) > 0 && /^\d+$/.test(v.sample_size ?? "")),
    {
      path: ["sample_size"],
      message: "Sample size required for non-Full sampling",
    },
  )

type Values = z.infer<typeof schema>

const SELECT_CLASS =
  "flex h-9 w-full rounded-sm border border-fg/20 bg-bg px-3 text-sm text-fg shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg"

const EMPTY: Values = {
  client_id: "",
  name: "",
  description: "",
  period_start: "",
  period_end: "",
  sampling: CallbackSamplingStrategy.FULL,
  sample_size: "",
  counsellor_user_ids: [],
  questionnaire_code: "",
  followup_questionnaire_code: "",
}

interface CampaignFormSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** When set, locks the client. */
  clientId?: string
  client?: Client | null
  onSaved?: (campaign: CallbackCampaign) => void
}

export function CampaignFormSheet({
  open,
  onOpenChange,
  clientId,
  client,
  onSaved,
}: CampaignFormSheetProps) {
  const queryClient = useQueryClient()
  const lockedClientId = clientId

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

  const initial: Values = { ...EMPTY, client_id: clientId ?? "" }

  const { register, reset, formState, submit, serverError, setValue, watch } =
    useApiForm<Values>({
      schema,
      defaultValues: initial,
      successToast: "Campaign created",
      onSubmit: async (values) => {
        const created = await careCallbacksApi.createCampaign({
          client_id: values.client_id,
          name: values.name,
          description: values.description?.trim() || null,
          period_start: values.period_start,
          period_end: values.period_end,
          sampling: values.sampling as CallbackSamplingStrategy,
          sample_size:
            values.sampling === CallbackSamplingStrategy.FULL
              ? null
              : Number(values.sample_size),
          counsellor_user_ids: values.counsellor_user_ids,
          questionnaire_code: values.questionnaire_code,
          followup_questionnaire_code: values.followup_questionnaire_code || null,
        })
        await queryClient.invalidateQueries({
          queryKey: ["care-callback-campaigns", "list"],
        })
        onSaved?.(created)
        onOpenChange(false)
        reset(EMPTY)
      },
    })

  const watchedClient = watch("client_id")
  const watchedSampling = watch("sampling")
  const watchedCounsellors = watch("counsellor_user_ids")

  useEffect(() => {
    if (!open) return
    reset({ ...EMPTY, client_id: clientId ?? "" })
  }, [open, clientId, reset])

  const errors = formState.errors as Record<string, { message?: string }>
  const showSampleSize = watchedSampling !== CallbackSamplingStrategy.FULL

  return (
    <SheetForm
      open={open}
      onOpenChange={onOpenChange}
      title="New care-callback campaign"
      description="Define audience, sampling, and the counsellor pool. Cases are generated to each counsellor's worklist when the campaign is activated."
      size="lg"
      onSubmit={submit}
      isSubmitting={formState.isSubmitting}
      serverError={serverError}
      submitLabel="Create campaign"
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
        <FormField label="Name" required error={errors.name?.message} htmlFor="cf-name">
          <Input
            id="cf-name"
            placeholder="e.g. Q2 anxiety/depression follow-up wave"
            {...register("name")}
          />
        </FormField>
        <FormField
          label="Description"
          optional
          error={errors.description?.message}
          htmlFor="cf-description"
        >
          <Input
            id="cf-description"
            placeholder="Internal notes — appears on the campaign detail."
            {...register("description")}
          />
        </FormField>
      </FormSection>

      <FormSection title="Outreach window">
        <div className="grid grid-cols-2 gap-3">
          <FormField
            label="Start date"
            required
            error={errors.period_start?.message}
            htmlFor="cf-start"
          >
            <Input id="cf-start" type="date" {...register("period_start")} />
          </FormField>
          <FormField
            label="End date"
            required
            description="Cases not completed by this date roll into the report as no-answer."
            error={errors.period_end?.message}
            htmlFor="cf-end"
          >
            <Input id="cf-end" type="date" {...register("period_end")} />
          </FormField>
        </div>
      </FormSection>

      <FormSection
        title="Sampling"
        description="Full = every eligible session in the period. Random/Stratified take a sample of N from the eligible pool."
      >
        <div className="grid grid-cols-2 gap-3">
          <FormField
            label="Strategy"
            required
            error={errors.sampling?.message}
            htmlFor="cf-sampling"
          >
            <select id="cf-sampling" className={SELECT_CLASS} {...register("sampling")}>
              {SAMPLING_VALUES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </FormField>
          {showSampleSize ? (
            <FormField
              label="Sample size"
              required
              error={errors.sample_size?.message}
              htmlFor="cf-sample-size"
            >
              <Input
                id="cf-sample-size"
                type="number"
                inputMode="numeric"
                min={1}
                placeholder="e.g. 50"
                className="font-mono"
                {...register("sample_size")}
              />
            </FormField>
          ) : null}
        </div>
      </FormSection>

      <FormSection
        title="Counsellor pool"
        description="Cases are round-robined across these users' worklists when the campaign is activated."
      >
        <FormField
          label="Counsellors"
          required
          error={errors.counsellor_user_ids?.message}
        >
          <CounsellorMultiPicker
            value={watchedCounsellors ?? []}
            onChange={(ids) =>
              setValue("counsellor_user_ids", ids, {
                shouldValidate: true,
                shouldDirty: true,
              })
            }
          />
        </FormField>
      </FormSection>

      <FormSection title="Questionnaires">
        <FormField
          label="Triage questionnaire"
          required
          description="Pre-call form that fires the crisis rules."
          error={errors.questionnaire_code?.message}
          htmlFor="cf-triage"
        >
          <select
            id="cf-triage"
            className={SELECT_CLASS}
            {...register("questionnaire_code")}
          >
            <option value="">— Select —</option>
            {triageOptions.map((q) => (
              <option key={q.code} value={q.code}>
                {q.title}
              </option>
            ))}
          </select>
        </FormField>
        <FormField
          label="Follow-up questionnaire"
          optional
          description="Optional post-call form (e.g. WOS-5)."
          error={errors.followup_questionnaire_code?.message}
          htmlFor="cf-followup"
        >
          <select
            id="cf-followup"
            className={SELECT_CLASS}
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

function CounsellorMultiPicker({
  value,
  onChange,
}: {
  value: string[]
  onChange: (ids: string[]) => void
}) {
  const [query, setQuery] = useState("")
  const debounced = useDebouncedValue(query.trim(), 250)
  const list = useEntityList<User>({
    resource: "users",
    params: { page: 1, limit: 8, search: debounced || undefined },
    listFn: usersApi.list,
  })
  const items = list.data?.items ?? []
  const selectedSet = new Set(value)

  const toggle = (id: string) => {
    if (selectedSet.has(id)) onChange(value.filter((v) => v !== id))
    else onChange([...value, id])
  }

  return (
    <div className="space-y-2">
      {value.length > 0 ? (
        <div className="flex flex-wrap gap-1.5">
          {value.map((id) => {
            const user = items.find((u) => u.id === id)
            return (
              <span
                key={id}
                className="inline-flex items-center gap-1 rounded-sm border border-primary/30 bg-primary/10 px-1.5 py-0.5 text-xs text-primary"
              >
                {user?.email ?? id.slice(0, 12)}
                <button
                  type="button"
                  onClick={() => toggle(id)}
                  aria-label={`Remove ${user?.email ?? id}`}
                  className="grid size-4 place-items-center rounded-sm hover:bg-primary/15"
                >
                  <X className="size-3" />
                </button>
              </span>
            )
          })}
        </div>
      ) : null}
      <Input
        placeholder="Search users by email…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <div className="max-h-44 overflow-y-auto rounded-sm border border-fg/15 bg-bg">
        {list.isPending ? (
          <p className="px-3 py-2 text-xs text-fg/55">Loading…</p>
        ) : items.length === 0 ? (
          <p className="px-3 py-2 text-xs text-fg/55">
            {debounced ? "No users match." : "Start typing to search users."}
          </p>
        ) : (
          <ul className="divide-y divide-fg/8">
            {items.map((u) => {
              const active = selectedSet.has(u.id)
              return (
                <li key={u.id}>
                  <button
                    type="button"
                    onClick={() => toggle(u.id)}
                    className="flex w-full items-center justify-between gap-2.5 px-3 py-2 text-left transition-colors hover:bg-surface-hover focus-visible:bg-surface-hover focus-visible:outline-none"
                  >
                    <span className="min-w-0 truncate text-sm text-fg">{u.email}</span>
                    {active ? (
                      <span className="shrink-0 rounded-sm border border-primary/30 bg-primary/10 px-1.5 py-0.5 text-[10px] font-medium text-primary">
                        Selected
                      </span>
                    ) : null}
                  </button>
                </li>
              )
            })}
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
