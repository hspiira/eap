import { useEffect, useState } from "react"

import { useQueryClient } from "@tanstack/react-query"
import { z } from "zod"

import { contractsApi } from "@/api/endpoints/contracts"
import { serviceAssignmentsApi } from "@/api/endpoints/service-assignments"
import { servicesApi } from "@/api/endpoints/services"
import { FormField } from "@/components/common/FormField"
import { FormSection } from "@/components/common/FormSection"
import { SheetForm } from "@/components/common/SheetForm"
import { Input } from "@/components/ui/input"
import { useApiForm } from "@/hooks/useApiForm"
import { useDebouncedValue } from "@/hooks/useDebouncedValue"
import { useEntityList } from "@/lib/queries"
import type { Contract, Service, ServiceAssignment } from "@/types/entities"

const schema = z
  .object({
    contract_id: z.string().trim().min(1, "Contract is required"),
    service_id: z.string().trim().min(1, "Service is required"),
    start_date: z.string().optional(),
    end_date: z.string().optional(),
  })
  .refine((d) => !d.end_date || !d.start_date || d.end_date >= d.start_date, {
    path: ["end_date"],
    message: "End date must be on or after start date",
  })

type Values = z.infer<typeof schema>

const EMPTY: Values = { contract_id: "", service_id: "", start_date: "", end_date: "" }

interface ServiceAssignmentFormSheetProps {
  open: boolean
  onOpenChange: (open: boolean) => void
  /** Pass an assignment to edit; omit to create. */
  assignment?: ServiceAssignment | null
  /** When set, locks the contract picker (e.g. launched from contract detail). */
  contractId?: string
  /** Pre-resolved contract used for the locked summary. */
  contract?: Contract | null
  onSaved?: (assignment: ServiceAssignment) => void
}

export function ServiceAssignmentFormSheet({
  open,
  onOpenChange,
  assignment,
  contractId,
  contract,
  onSaved,
}: ServiceAssignmentFormSheetProps) {
  const isEdit = Boolean(assignment)
  const queryClient = useQueryClient()
  const lockedContractId = contractId ?? assignment?.contract_id

  const initial: Values = assignment
    ? {
        contract_id: assignment.contract_id,
        service_id: assignment.service_id,
        start_date: assignment.start_date ?? "",
        end_date: assignment.end_date ?? "",
      }
    : { ...EMPTY, contract_id: contractId ?? "" }

  const { register, reset, formState, submit, serverError, setValue, watch } =
    useApiForm<Values>({
      schema,
      defaultValues: initial,
      successToast: isEdit ? "Assignment updated" : "Assignment created",
      onSubmit: async (values) => {
        const payload = {
          contract_id: values.contract_id,
          service_id: values.service_id,
          start_date: values.start_date || undefined,
          end_date: values.end_date || undefined,
        }
        const result = assignment
          ? await serviceAssignmentsApi.update(assignment.id, payload)
          : await serviceAssignmentsApi.create(
              payload as Parameters<typeof serviceAssignmentsApi.create>[0],
            )
        await queryClient.invalidateQueries({
          queryKey: ["service-assignments", "list"],
        })
        if (assignment) {
          await queryClient.invalidateQueries({
            queryKey: ["service-assignments", "detail", assignment.id],
          })
        }
        if (lockedContractId) {
          await queryClient.invalidateQueries({
            queryKey: ["contracts", "detail", lockedContractId],
          })
        }
        onSaved?.(result)
        onOpenChange(false)
        reset(EMPTY)
      },
    })

  const watchedContract = watch("contract_id")
  const watchedService = watch("service_id")

  useEffect(() => {
    if (!open) return
    if (assignment) {
      reset({
        contract_id: assignment.contract_id,
        service_id: assignment.service_id,
        start_date: assignment.start_date ?? "",
        end_date: assignment.end_date ?? "",
      })
    }
  }, [open, assignment, reset])

  const errors = formState.errors as Record<string, { message?: string }>

  return (
    <SheetForm
      open={open}
      onOpenChange={onOpenChange}
      title={isEdit ? "Edit assignment" : "Add service to contract"}
      description={
        isEdit
          ? "Update which service this assignment covers and its active period."
          : "Link a service to a contract. Sessions billed against this contract must reference an active assignment."
      }
      size="md"
      onSubmit={submit}
      isSubmitting={formState.isSubmitting}
      serverError={serverError}
      submitLabel={isEdit ? "Save changes" : "Create assignment"}
      submittingLabel={isEdit ? "Saving…" : "Creating…"}
    >
      <FormSection title="Contract">
        {lockedContractId ? (
          <LockedContractSummary
            contractId={lockedContractId}
            contract={contract ?? null}
          />
        ) : (
          <FormField
            label="Contract"
            required
            error={errors.contract_id?.message}
            description="The master agreement this assignment falls under."
          >
            <ContractPicker
              value={watchedContract ?? ""}
              onChange={(id) =>
                setValue("contract_id", id, { shouldValidate: true, shouldDirty: true })
              }
            />
          </FormField>
        )}
        <input type="hidden" {...register("contract_id")} />
      </FormSection>

      <FormSection title="Service">
        <FormField
          label="Service"
          required
          error={errors.service_id?.message}
          description="What this contract covers."
        >
          <ServicePicker
            value={watchedService ?? ""}
            onChange={(id) =>
              setValue("service_id", id, { shouldValidate: true, shouldDirty: true })
            }
          />
        </FormField>
        <input type="hidden" {...register("service_id")} />
      </FormSection>

      <FormSection
        title="Active period"
        description="Optional. Leave blank to inherit the contract's term."
      >
        <div className="grid grid-cols-2 gap-3">
          <FormField
            label="Start date"
            optional
            error={errors.start_date?.message}
            htmlFor="sa-start"
          >
            <Input id="sa-start" type="date" {...register("start_date")} />
          </FormField>
          <FormField
            label="End date"
            optional
            error={errors.end_date?.message}
            htmlFor="sa-end"
          >
            <Input id="sa-end" type="date" {...register("end_date")} />
          </FormField>
        </div>
      </FormSection>
    </SheetForm>
  )
}

function LockedContractSummary({
  contractId,
  contract,
}: {
  contractId: string
  contract: Contract | null
}) {
  const enabled = !contract && Boolean(contractId)
  const detail = useEntityList<Contract>({
    resource: "contracts",
    params: { page: 1, limit: 1, search: contractId },
    listFn: contractsApi.list,
    enabled,
  })
  const resolved =
    contract ?? (detail.data?.items ?? []).find((c) => c.id === contractId) ?? null
  const label = resolved?.contract_number ?? resolved?.id ?? contractId
  return (
    <div className="flex items-center gap-2.5 rounded-sm border border-fg/15 bg-surface px-3 py-2">
      <span
        aria-hidden
        className="grid size-7 shrink-0 place-items-center bg-primary/10 font-mono text-[10px] font-semibold text-primary"
      >
        SA
      </span>
      <div className="min-w-0 flex-1">
        <p className="truncate font-mono text-sm font-medium text-fg">{label}</p>
        <p className="truncate text-[11px] text-fg/55">
          {resolved ? `Client ${resolved.client_id.slice(0, 8)}` : contractId.slice(0, 8)}
        </p>
      </div>
      <span className="shrink-0 rounded-sm border border-fg/15 bg-bg px-1.5 py-0.5 text-[10px] font-medium tracking-wide text-fg/55">
        Locked
      </span>
    </div>
  )
}

function ContractPicker({
  value,
  onChange,
}: {
  value: string
  onChange: (id: string) => void
}) {
  const [query, setQuery] = useState("")
  const debounced = useDebouncedValue(query.trim(), 250)
  const list = useEntityList<Contract>({
    resource: "contracts",
    params: { page: 1, limit: 8, search: debounced || undefined },
    listFn: contractsApi.list,
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
          SA
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate font-mono text-sm font-medium text-fg">
            {selected.contract_number ?? selected.id.slice(0, 8)}
          </p>
          <p className="truncate text-[11px] text-fg/55">
            Client {selected.client_id.slice(0, 8)}
          </p>
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
        placeholder="Search contracts by number…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <div className="max-h-48 overflow-y-auto rounded-sm border border-fg/15 bg-bg">
        {list.isPending ? (
          <p className="px-3 py-2 text-xs text-fg/55">Loading…</p>
        ) : items.length === 0 ? (
          <p className="px-3 py-2 text-xs text-fg/55">
            {debounced ? "No contracts match." : "Start typing to search contracts."}
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
                    SA
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate font-mono text-sm font-medium text-fg">
                      {c.contract_number ?? c.id.slice(0, 8)}
                    </span>
                    <span className="block truncate text-[11px] text-fg/55">
                      Client {c.client_id.slice(0, 8)} · {c.status}
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

function ServicePicker({
  value,
  onChange,
}: {
  value: string
  onChange: (id: string) => void
}) {
  const [query, setQuery] = useState("")
  const debounced = useDebouncedValue(query.trim(), 250)
  const list = useEntityList<Service>({
    resource: "services",
    params: { page: 1, limit: 10, search: debounced || undefined },
    listFn: servicesApi.list,
  })
  const items = list.data?.items ?? []
  const selected = items.find((s) => s.id === value)

  if (selected) {
    return (
      <div className="flex items-center gap-2.5 rounded-sm border border-fg/15 bg-surface px-3 py-2">
        <span
          aria-hidden
          className="grid size-7 shrink-0 place-items-center bg-primary/10 font-mono text-[10px] font-semibold text-primary"
        >
          SV
        </span>
        <div className="min-w-0 flex-1">
          <p className="truncate text-sm font-medium text-fg">{selected.name}</p>
          <p className="truncate text-[11px] text-fg/55">
            {selected.service_type ?? selected.category ?? selected.id.slice(0, 8)}
          </p>
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
        placeholder="Search services by name…"
        value={query}
        onChange={(e) => setQuery(e.target.value)}
      />
      <div className="max-h-48 overflow-y-auto rounded-sm border border-fg/15 bg-bg">
        {list.isPending ? (
          <p className="px-3 py-2 text-xs text-fg/55">Loading…</p>
        ) : items.length === 0 ? (
          <p className="px-3 py-2 text-xs text-fg/55">
            {debounced ? "No services match." : "Start typing to search services."}
          </p>
        ) : (
          <ul className="divide-y divide-fg/8">
            {items.map((s) => (
              <li key={s.id}>
                <button
                  type="button"
                  onClick={() => onChange(s.id)}
                  className="flex w-full items-center gap-2.5 px-3 py-2 text-left transition-colors hover:bg-surface-hover focus-visible:bg-surface-hover focus-visible:outline-none"
                >
                  <span
                    aria-hidden
                    className="grid size-6 shrink-0 place-items-center bg-primary/10 font-mono text-[10px] font-semibold text-primary"
                  >
                    SV
                  </span>
                  <span className="min-w-0 flex-1">
                    <span className="block truncate text-sm font-medium text-fg">
                      {s.name}
                    </span>
                    <span className="block truncate text-[11px] text-fg/55">
                      {s.service_type ?? s.category ?? "—"}
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
