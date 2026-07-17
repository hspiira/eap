
import { z } from "zod"

import { contractsApi } from "@/api/endpoints/contracts"
import { serviceAssignmentsApi } from "@/api/endpoints/service-assignments"
import { servicesApi } from "@/api/endpoints/services"
import type { ServiceAssignmentCreate } from "@/api/generated"
import { EntityPicker, PickerRow } from "@/components/common/EntityPicker"
import { FormField } from "@/components/common/FormField"
import { FormSection } from "@/components/common/FormSection"
import { SheetForm } from "@/components/common/SheetForm"
import { Input } from "@/components/ui/input"
import { Textarea } from "@/components/ui/textarea"
import { useEntityFormSheet } from "@/hooks/useEntityFormSheet"
import { useEntityList } from "@/lib/queries"
import type { Contract, Service, ServiceAssignment } from "@/types/entities"

// Schema mirrors the BE `ServiceAssignmentCreate` (see openapi.json). Active-
// period dates are intentionally derived from the parent contract on the BE,
// so we don't collect them here.
const schema = z.object({
  contract_id: z.string().trim().min(1, "Contract is required"),
  service_id: z.string().trim().min(1, "Service is required"),
  notes: z.string().optional(),
})

type Values = z.infer<typeof schema>

const EMPTY: Values = { contract_id: "", service_id: "", notes: "" }

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
  const lockedContractId = contractId ?? assignment?.contract_id

  const { register, formState, submit, serverError, setValue, watch, isEdit } =
    useEntityFormSheet<
      Values,
      Parameters<typeof serviceAssignmentsApi.create>[0],
      ServiceAssignment,
      ServiceAssignment
    >({
      resource: "service-assignments",
      schema,
      defaultValues: { ...EMPTY, contract_id: contractId ?? "" },
      open,
      onOpenChange,
      entity: assignment,
      toFormValues: (a) => ({
        contract_id: a.contract_id,
        service_id: a.service_id,
        notes: a.notes ?? "",
      }),
      parsePayload: (values): ServiceAssignmentCreate => ({
        contract_id: values.contract_id,
        service_id: values.service_id,
        notes: values.notes?.trim() || null,
      }),
      save: ({ payload, entity, isEdit }) =>
        isEdit && entity
          ? serviceAssignmentsApi.update(entity.id, payload)
          : serviceAssignmentsApi.create(payload),
      successToast: { create: "Assignment created", update: "Assignment updated" },
      extraInvalidations: lockedContractId
        ? [{ queryKey: ["contracts", "detail", lockedContractId] }]
        : undefined,
      onSaved,
    })

  const watchedContract = watch("contract_id")
  const watchedService = watch("service_id")

  const errors = formState.errors

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
        <Input type="hidden" {...register("contract_id")} />
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
        <Input type="hidden" {...register("service_id")} />
      </FormSection>

      <FormSection
        title="Notes"
        description="Optional. Active-period dates derive from the parent contract."
      >
        <FormField
          label="Notes"
          optional
          error={errors.notes?.message}
          htmlFor="sa-notes"
        >
          <Textarea
            id="sa-notes"
            rows={3}
            placeholder="Internal notes about this service assignment…"
            {...register("notes")}
          />
        </FormField>
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
  const label = resolved?.id ?? contractId
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

function ContractPicker({ value, onChange }: { value: string; onChange: (id: string) => void }) {
  const row = (c: Contract) => (
    <PickerRow initials="SA" primary={c.id.slice(0, 8)} secondary={`Client ${c.client_id.slice(0, 8)}`} />
  )
  return (
    <EntityPicker<Contract>
      resource="contracts"
      listFn={contractsApi.list}
      value={value}
      onChange={onChange}
      placeholder="Search contracts by number…"
      emptyPrompt="Start typing to search contracts."
      emptyNoMatch="No contracts match."
      renderSelected={row}
      renderRow={row}
    />
  )
}

function ServicePicker({ value, onChange }: { value: string; onChange: (id: string) => void }) {
  const row = (s: Service) => (
    <PickerRow
      initials="SV"
      primary={s.name}
      secondary={s.service_type ?? s.category ?? s.id.slice(0, 8)}
    />
  )
  return (
    <EntityPicker<Service>
      resource="services"
      listFn={servicesApi.list}
      value={value}
      onChange={onChange}
      placeholder="Search services by name…"
      emptyPrompt="Start typing to search services."
      emptyNoMatch="No services match."
      renderSelected={row}
      renderRow={row}
    />
  )
}
