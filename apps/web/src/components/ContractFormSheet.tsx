import { useState } from "react"

import { useQueryClient } from "@tanstack/react-query"
import { z } from "zod"

import { clientsApi } from "@/api/endpoints/clients"
import { contractsApi } from "@/api/endpoints/contracts"
import { FormField } from "@/components/common/FormField"
import { FormSection } from "@/components/common/FormSection"
import { SheetForm } from "@/components/common/SheetForm"
import { Input } from "@/components/ui/input"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import { useEntityFormSheet } from "@/hooks/useEntityFormSheet"
import { useEntityList } from "@/lib/queries"
import type { Client, Contract } from "@/types/entities"
import { PaymentFrequency, PaymentStatus } from "@/types/enums"

const FREQUENCY_VALUES = [
  PaymentFrequency.WEEKLY,
  PaymentFrequency.MONTHLY,
  PaymentFrequency.QUARTERLY,
  PaymentFrequency.ANNUALLY,
] as const

const PAYMENT_STATUS_VALUES = [
  PaymentStatus.PENDING,
  PaymentStatus.PAID,
  PaymentStatus.OVERDUE,
  PaymentStatus.CANCELLED,
  PaymentStatus.REFUNDED,
] as const

const contractSchema = z
  .object({
    client_id: z.string().trim().min(1, "Client is required"),
    contract_number: z.string().optional(),
    start_date: z.string().min(1, "Start date is required"),
    end_date: z.string().optional(),
    renewal_date: z.string().optional(),
    billing_frequency: z.string().optional(),
    billing_amount: z.string().optional(),
    currency: z.string().optional(),
    payment_status: z.string().optional(),
  })
  .refine((d) => !d.end_date || d.end_date >= d.start_date, {
    path: ["end_date"],
    message: "End date must be on or after start date",
  })
  .refine((d) => !d.renewal_date || d.renewal_date >= d.start_date, {
    path: ["renewal_date"],
    message: "Renewal date must be on or after start date",
  })
  .refine(
    (d) => !d.billing_amount || !Number.isNaN(Number(d.billing_amount)),
    { path: ["billing_amount"], message: "Must be a number" },
  )

type ContractFormValues = z.infer<typeof contractSchema>

const SELECT_CLASS =
  "flex h-9 w-full rounded-sm border border-fg/20 bg-bg px-3 text-sm text-fg shadow-sm focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 focus-visible:ring-offset-bg"

const EMPTY: ContractFormValues = {
  client_id: "",
  contract_number: "",
  start_date: "",
  end_date: "",
  renewal_date: "",
  billing_frequency: "",
  billing_amount: "",
  currency: "",
  payment_status: "",
}

interface ContractFormSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Pass a contract to edit; omit/null to create. */
  contract?: Contract | null
  /** When set, locks the form to this client and hides the picker. */
  clientId?: string
  /** Pre-resolved client used for the locked summary (avoids extra fetch). */
  client?: Client | null
  onSaved?: (contract: Contract) => void
}

export function ContractFormSheet({
  open,
  onOpenChange,
  contract,
  clientId,
  client,
  onSaved,
}: ContractFormSheetProps) {
  const lockedClientId = clientId ?? contract?.client_id
  const queryClient = useQueryClient()

  const { register, formState, submit, serverError, setValue, watch, isEdit } =
    useEntityFormSheet<
      ContractFormValues,
      Parameters<typeof contractsApi.create>[0],
      Contract,
      Contract
    >({
      resource: "contracts",
      schema: contractSchema,
      defaultValues: { ...EMPTY, client_id: clientId ?? "" },
      open,
      onOpenChange,
      entity: contract,
      toFormValues: (c) => ({
        client_id: c.client_id,
        contract_number: c.contract_number ?? "",
        start_date: c.start_date,
        end_date: c.end_date ?? "",
        renewal_date: c.renewal_date ?? "",
        billing_frequency: c.billing_frequency ?? "",
        billing_amount: c.billing_amount != null ? String(c.billing_amount) : "",
        currency: c.currency ?? "",
        payment_status: c.payment_status ?? "",
      }),
      parsePayload: (values) => ({
        client_id: values.client_id,
        contract_number: values.contract_number?.trim() || undefined,
        start_date: values.start_date,
        end_date: values.end_date || undefined,
        renewal_date: values.renewal_date || undefined,
        billing_frequency: values.billing_frequency
          ? (values.billing_frequency as PaymentFrequency)
          : undefined,
        billing_amount: values.billing_amount ? Number(values.billing_amount) : undefined,
        currency: values.currency?.trim() || undefined,
        payment_status: values.payment_status
          ? (values.payment_status as PaymentStatus)
          : undefined,
      }),
      save: ({ payload, entity, isEdit }) =>
        isEdit && entity
          ? contractsApi.update(entity.id, payload)
          : contractsApi.create(payload),
      successToast: { create: "Contract created", update: "Contract updated" },
      onSaved: (result) => {
        if (lockedClientId) {
          void queryClient.invalidateQueries({
            queryKey: ["clients", "detail", lockedClientId],
          })
        }
        onSaved?.(result)
      },
    })

  const watchedClientId = watch("client_id")

  const errors = formState.errors

  return (
    <SheetForm
      open={open}
      onOpenChange={onOpenChange}
      title={isEdit ? "Edit contract" : "Add contract"}
      description={
        isEdit
          ? "Update lifecycle dates and billing details."
          : "Create a contract for a corporate client. You can refine pricing and renewals later."
      }
      size="md"
      onSubmit={submit}
      isSubmitting={formState.isSubmitting}
      serverError={serverError}
      submitLabel={isEdit ? "Save changes" : "Create contract"}
      submittingLabel={isEdit ? "Saving…" : "Creating…"}
    >
      <FormSection title="Client">
        {lockedClientId ? (
          <LockedClientSummary clientId={lockedClientId} client={client ?? null} />
        ) : (
          <FormField
            label="Client"
            required
            error={errors.client_id?.message}
            description="Select the corporate client this contract is for."
          >
            <ClientPicker
              value={watchedClientId}
              onChange={(id) =>
                setValue("client_id", id, { shouldValidate: true, shouldDirty: true })
              }
            />
          </FormField>
        )}
        <input type="hidden" {...register("client_id")} />
      </FormSection>

      <FormSection title="Identity">
        <FormField
          label="Contract number"
          optional
          description="Reference shown on invoices and reports."
          error={errors.contract_number?.message}
          htmlFor="cf-number"
        >
          <Input
            id="cf-number"
            placeholder="e.g. MSA-2026-014"
            className="font-mono"
            {...register("contract_number")}
          />
        </FormField>
      </FormSection>

      <FormSection title="Lifecycle dates">
        <div className="grid grid-cols-2 gap-3">
          <FormField
            label="Start date"
            required
            error={errors.start_date?.message}
            htmlFor="cf-start"
          >
            <Input id="cf-start" type="date" {...register("start_date")} />
          </FormField>
          <FormField
            label="End date"
            optional
            error={errors.end_date?.message}
            htmlFor="cf-end"
          >
            <Input id="cf-end" type="date" {...register("end_date")} />
          </FormField>
        </div>
        <FormField
          label="Renewal date"
          optional
          description="When this contract is up for renewal review."
          error={errors.renewal_date?.message}
          htmlFor="cf-renewal"
        >
          <Input id="cf-renewal" type="date" {...register("renewal_date")} />
        </FormField>
      </FormSection>

      <FormSection
        title="Billing"
        description="Optional. Used for invoicing and revenue reporting."
      >
        <div className="grid grid-cols-2 gap-3">
          <FormField
            label="Frequency"
            optional
            error={errors.billing_frequency?.message}
            htmlFor="cf-frequency"
          >
            <select
              id="cf-frequency"
              className={SELECT_CLASS}
              {...register("billing_frequency")}
            >
              <option value="">Unset</option>
              {FREQUENCY_VALUES.map((f) => (
                <option key={f} value={f}>
                  {f}
                </option>
              ))}
            </select>
          </FormField>
          <FormField
            label="Payment status"
            optional
            error={errors.payment_status?.message}
            htmlFor="cf-payment-status"
          >
            <select
              id="cf-payment-status"
              className={SELECT_CLASS}
              {...register("payment_status")}
            >
              <option value="">Unset</option>
              {PAYMENT_STATUS_VALUES.map((s) => (
                <option key={s} value={s}>
                  {s}
                </option>
              ))}
            </select>
          </FormField>
        </div>
        <div className="grid grid-cols-[1fr_6rem] gap-3">
          <FormField
            label="Amount"
            optional
            error={errors.billing_amount?.message}
            htmlFor="cf-amount"
          >
            <Input
              id="cf-amount"
              type="number"
              inputMode="decimal"
              step="0.01"
              min="0"
              placeholder="0.00"
              className="font-mono"
              {...register("billing_amount")}
            />
          </FormField>
          <FormField
            label="Currency"
            optional
            error={errors.currency?.message}
            htmlFor="cf-currency"
          >
            <Input
              id="cf-currency"
              placeholder="KES"
              maxLength={3}
              className="font-mono uppercase"
              {...register("currency")}
            />
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
        {resolved ? initial(resolved.name) : "··"}
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

interface ClientPickerProps {
  value: string
  onChange: (clientId: string) => void
}

function ClientPicker({ value, onChange }: ClientPickerProps) {
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
          {initial(selected.name)}
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
            {debounced ? "No clients match that search." : "Start typing to search clients."}
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
                    {initial(c.name)}
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

function initial(name: string): string {
  const trimmed = name.trim()
  if (!trimmed) return "·"
  const parts = trimmed.split(/\s+/)
  if (parts.length >= 2) return (parts[0][0] + parts[1][0]).toUpperCase()
  return trimmed.slice(0, 2).toUpperCase()
}
