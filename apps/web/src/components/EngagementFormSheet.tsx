import { useEffect, useState } from "react"

import { useQueryClient } from "@tanstack/react-query"
import { z } from "zod"

import { clientsApi } from "@/api/endpoints/clients"
import { engagementsApi } from "@/api/endpoints/engagements"
import { usersApi } from "@/api/endpoints/users"
import { FormField } from "@/components/common/FormField"
import { FormSection } from "@/components/common/FormSection"
import { SheetForm } from "@/components/common/SheetForm"
import { Input } from "@/components/ui/input"
import { useApiForm } from "@/hooks/useApiForm"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import { useEntityList } from "@/lib/queries"
import type { Client, Engagement, User } from "@/types/entities"
import { EngagementType } from "@/types/enums"

const TYPE_VALUES = [
  EngagementType.POLICY_DRAFT,
  EngagementType.TRAINING,
  EngagementType.ASSESSMENT,
  EngagementType.ADVISORY,
  EngagementType.AUDIT,
  EngagementType.OTHER,
] as const

const schema = z
  .object({
    client_id: z.string().trim().min(1, "Client is required"),
    name: z.string().trim().min(3, "Name must be at least 3 characters"),
    description: z.string().trim().optional(),
    engagement_type: z.enum(TYPE_VALUES as readonly [string, ...string[]]),
    start_date: z.string().min(1, "Start date is required"),
    due_date: z.string().optional(),
    hourly_rate: z
      .string()
      .optional()
      .refine((v) => !v || !Number.isNaN(Number(v)), "Must be a number"),
    currency: z.string().trim().optional(),
    budget_hours: z
      .string()
      .optional()
      .refine((v) => !v || /^\d+$/.test(v), "Must be a positive integer"),
    lead_user_id: z.string().optional(),
  })
  .refine(
    (v) => !v.due_date || Date.parse(v.due_date) >= Date.parse(v.start_date),
    {
      path: ["due_date"],
      message: "Due date must be on or after the start date",
    },
  )

type Values = z.infer<typeof schema>

const SELECT_CLASS =
  "flex h-9 w-full rounded-sm border border-fg/20 bg-bg px-3 text-sm text-fg shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg"

const EMPTY: Values = {
  client_id: "",
  name: "",
  description: "",
  engagement_type: EngagementType.POLICY_DRAFT,
  start_date: "",
  due_date: "",
  hourly_rate: "",
  currency: "UGX",
  budget_hours: "",
  lead_user_id: "",
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
  const queryClient = useQueryClient()
  const lockedClientId = clientId

  const initial: Values = { ...EMPTY, client_id: clientId ?? "" }

  const { register, reset, formState, submit, serverError, setValue, watch } =
    useApiForm<Values>({
      schema,
      defaultValues: initial,
      successToast: "Engagement created",
      onSubmit: async (values) => {
        const created = await engagementsApi.create({
          client_id: values.client_id,
          name: values.name,
          description: values.description?.trim() || null,
          engagement_type: values.engagement_type as EngagementType,
          start_date: values.start_date,
          due_date: values.due_date || null,
          hourly_rate: values.hourly_rate ? Number(values.hourly_rate) : null,
          currency: values.currency?.trim() || null,
          budget_hours: values.budget_hours ? Number(values.budget_hours) : null,
          lead_user_id: values.lead_user_id || null,
        })
        await queryClient.invalidateQueries({ queryKey: ["engagements", "list"] })
        onSaved?.(created)
        onOpenChange(false)
        reset(EMPTY)
      },
    })

  const watchedClient = watch("client_id")
  const watchedLead = watch("lead_user_id")

  useEffect(() => {
    if (!open) return
    reset({ ...EMPTY, client_id: clientId ?? "" })
  }, [open, clientId, reset])

  const errors = formState.errors as Record<string, { message?: string }>

  return (
    <SheetForm
      open={open}
      onOpenChange={onOpenChange}
      title="New consultancy engagement"
      description="Scope the work, agreed dates, and the rate-card snapshot. Deliverables and hours get logged from the engagement detail page once active."
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
        <input type="hidden" {...register("client_id")} />
      </FormSection>

      <FormSection title="Identity">
        <FormField label="Name" required error={errors.name?.message} htmlFor="ef-name">
          <Input
            id="ef-name"
            placeholder="e.g. Wellness policy refresh — Q3"
            {...register("name")}
          />
        </FormField>
        <FormField
          label="Description"
          optional
          error={errors.description?.message}
          htmlFor="ef-description"
        >
          <Input
            id="ef-description"
            placeholder="Internal notes — appears on the engagement detail."
            {...register("description")}
          />
        </FormField>
      </FormSection>

      <FormSection title="Type & schedule">
        <FormField
          label="Type"
          required
          error={errors.engagement_type?.message}
          htmlFor="ef-type"
        >
          <select id="ef-type" className={SELECT_CLASS} {...register("engagement_type")}>
            {TYPE_VALUES.map((t) => (
              <option key={t} value={t}>
                {t}
              </option>
            ))}
          </select>
        </FormField>
        <div className="grid grid-cols-2 gap-3">
          <FormField
            label="Start date"
            required
            error={errors.start_date?.message}
            htmlFor="ef-start"
          >
            <Input id="ef-start" type="date" {...register("start_date")} />
          </FormField>
          <FormField
            label="Due date"
            optional
            description="Slips trigger an Overdue indicator in the list."
            error={errors.due_date?.message}
            htmlFor="ef-due"
          >
            <Input id="ef-due" type="date" {...register("due_date")} />
          </FormField>
        </div>
      </FormSection>

      <FormSection
        title="Commercials"
        description="Optional. Snapshot of rate-card terms for this engagement."
      >
        <div className="grid grid-cols-[1fr_6rem] gap-3">
          <FormField
            label="Hourly rate"
            optional
            error={errors.hourly_rate?.message}
            htmlFor="ef-rate"
          >
            <Input
              id="ef-rate"
              type="number"
              inputMode="decimal"
              min={0}
              step="0.01"
              placeholder="0.00"
              className="font-mono"
              {...register("hourly_rate")}
            />
          </FormField>
          <FormField
            label="Currency"
            optional
            error={errors.currency?.message}
            htmlFor="ef-currency"
          >
            <Input
              id="ef-currency"
              maxLength={3}
              className="font-mono uppercase"
              {...register("currency")}
            />
          </FormField>
        </div>
        <FormField
          label="Budget (hours)"
          optional
          description="Leave blank for open-ended."
          error={errors.budget_hours?.message}
          htmlFor="ef-budget"
        >
          <Input
            id="ef-budget"
            type="number"
            inputMode="numeric"
            min={0}
            placeholder="40"
            className="font-mono"
            {...register("budget_hours")}
          />
        </FormField>
      </FormSection>

      <FormSection
        title="Lead consultant"
        description="Optional. Owner accountable for delivery."
      >
        <FormField label="Lead" optional error={errors.lead_user_id?.message}>
          <UserPicker
            value={watchedLead ?? ""}
            onChange={(id) =>
              setValue("lead_user_id", id, { shouldValidate: true, shouldDirty: true })
            }
          />
        </FormField>
        <input type="hidden" {...register("lead_user_id")} />
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

function UserPicker({
  value,
  onChange,
}: {
  value: string
  onChange: (id: string) => void
}) {
  const [query, setQuery] = useState("")
  const debounced = useDebouncedValue(query.trim(), 250)
  const list = useEntityList<User>({
    resource: "users",
    params: { page: 1, limit: 8, search: debounced || undefined },
    listFn: usersApi.list,
  })
  const items = list.data?.items ?? []
  const selected = items.find((u) => u.id === value)

  if (selected) {
    return (
      <div className="flex items-center gap-2.5 rounded-sm border border-fg/15 bg-surface px-3 py-2">
        <span
          aria-hidden
          className="grid size-7 shrink-0 place-items-center bg-primary/10 font-mono text-[10px] font-semibold text-primary"
        >
          U
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-fg">{selected.email}</p>
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
            {items.map((u) => (
              <li key={u.id}>
                <button
                  type="button"
                  onClick={() => onChange(u.id)}
                  className="flex w-full items-center gap-2.5 px-3 py-2 text-left transition-colors hover:bg-surface-hover focus-visible:bg-surface-hover focus-visible:outline-none"
                >
                  <span
                    aria-hidden
                    className="grid size-6 shrink-0 place-items-center bg-primary/10 font-mono text-[10px] font-semibold text-primary"
                  >
                    U
                  </span>
                  <span className="truncate text-sm text-fg">{u.email}</span>
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
