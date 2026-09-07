import { useState } from "react"

import { providersApi } from "@/api/endpoints/providers"
import { DetailCard } from "@/components/common/DetailPrimitives"
import { FormField } from "@/components/common/FormField"
import { StatusBadge } from "@/components/common/StatusBadge"
import { ReasonDialog } from "@/components/providers/ReasonDialog"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select"
import { useToast } from "@/contexts/ToastContext"
import { useCurrentRole } from "@/hooks/useCanWrite"
import { normalizeErrorMessage } from "@/lib/errors"
import type { Provider } from "@/types/entities"
import {
  AccreditationStatus,
  BaseStatus,
  PanelStatus,
  ProviderTier,
  TenantRole,
} from "@/types/enums"
import { getStatusLabel } from "@/utils/statusColors"

type Command = "tier" | "panel" | "accreditation" | "status"

const COMMAND_COPY: Record<Command, { title: string; description: string; confirm: string }> = {
  tier: {
    title: "Change tier",
    description: "Tier drives rate and matching. The change is recorded with your reason.",
    confirm: "Change tier",
  },
  panel: {
    title: "Change panel status",
    description:
      "Only an active panel status is eligible for a new booking. Suspending flags affected future bookings for review; it does not cancel them or alter completed sessions.",
    confirm: "Change panel status",
  },
  accreditation: {
    title: "Record accreditation",
    description:
      "Accreditation belongs to the individual and is assessed independently of any organisation's supplier approval. An empty expiry means no expiry is on record, not an indefinite one.",
    confirm: "Save accreditation",
  },
  status: {
    title: "Change record status",
    description:
      "Deactivating hides the practitioner from new bookings. Their past sessions and their attribution are kept.",
    confirm: "Change record status",
  },
}

function EnumSelect<T extends string>({
  id,
  label,
  values,
  value,
  onChange,
}: {
  id: string
  label: string
  values: T[]
  value: T
  onChange: (value: T) => void
}) {
  return (
    <FormField label={label} required htmlFor={id}>
      <Select value={value} onValueChange={(next) => onChange(next as T)}>
        <SelectTrigger id={id}>
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          {values.map((entry) => (
            <SelectItem key={entry} value={entry}>
              {getStatusLabel(entry)}
            </SelectItem>
          ))}
        </SelectContent>
      </Select>
    </FormField>
  )
}

/**
 * The four audited practitioner commands. Each is Admin-only and each needs a
 * reason; general edit cannot reach these fields at all.
 */
export function ProviderLifecyclePanel({
  provider,
  onChanged,
}: {
  provider: Provider
  onChanged: (provider: Provider) => void
}) {
  const toast = useToast()
  const isAdmin = useCurrentRole() === TenantRole.ADMIN
  const [command, setCommand] = useState<Command | null>(null)
  const profile = provider.provider_profile

  const [tier, setTier] = useState(profile.tier)
  const [panelStatus, setPanelStatus] = useState(profile.panel_status)
  const [status, setStatus] = useState(provider.status)
  const [accreditation, setAccreditation] = useState(profile.accreditation_status)
  const [authority, setAuthority] = useState(profile.accreditation_authority ?? "")
  const [expiry, setExpiry] = useState(profile.accreditation_expiry ?? "")

  const open = (next: Command) => {
    setTier(profile.tier)
    setPanelStatus(profile.panel_status)
    setStatus(provider.status)
    setAccreditation(profile.accreditation_status)
    setAuthority(profile.accreditation_authority ?? "")
    setExpiry(profile.accreditation_expiry ?? "")
    setCommand(next)
  }

  const run = async (reason: string) => {
    if (!command) return
    try {
      const updated = await runCommand(provider.id, command, reason, {
        tier: tier ?? ProviderTier.T3,
        panelStatus,
        status,
        accreditation,
        authority,
        expiry,
      })
      onChanged(updated)
      setCommand(null)
      toast.showSuccess("Change recorded")
    } catch (error) {
      toast.showError(normalizeErrorMessage(error, "Could not record the change"))
    }
  }

  return (
    <DetailCard title="Panel and accreditation">
      <dl className="grid gap-3 sm:grid-cols-2">
        <Field label="Tier" value={profile.tier} />
        <Field
          label="Panel status"
          value={<StatusBadge status={profile.panel_status} size="sm" />}
        />
        <Field
          label="Accreditation"
          value={<StatusBadge status={profile.accreditation_status} size="sm" />}
        />
        <Field label="Record status" value={<StatusBadge status={provider.status} size="sm" />} />
        <Field label="Accreditation authority" value={profile.accreditation_authority ?? "-"} />
        <Field
          label="Accreditation expiry"
          value={profile.accreditation_expiry ?? "No expiry on record"}
        />
      </dl>

      {isAdmin ? (
        <div className="mt-4 flex flex-wrap gap-2 border-t border-fg/10 pt-4">
          <Button type="button" variant="outline" size="sm" onClick={() => open("tier")}>
            Change tier
          </Button>
          <Button type="button" variant="outline" size="sm" onClick={() => open("panel")}>
            Change panel status
          </Button>
          <Button type="button" variant="outline" size="sm" onClick={() => open("accreditation")}>
            Record accreditation
          </Button>
          <Button type="button" variant="outline" size="sm" onClick={() => open("status")}>
            Change record status
          </Button>
        </div>
      ) : (
        <p className="mt-4 border-t border-fg/10 pt-4 text-sm text-fg-muted">
          Tier, panel status, accreditation and record status are changed by a tenant admin.
        </p>
      )}

      <ReasonDialog
        open={command !== null}
        onOpenChange={(next) => (next ? null : setCommand(null))}
        title={command ? COMMAND_COPY[command].title : ""}
        description={command ? COMMAND_COPY[command].description : ""}
        confirmLabel={command ? COMMAND_COPY[command].confirm : "Confirm"}
        onConfirm={run}
      >
        {command === "tier" ? (
          <EnumSelect
            id="lifecycle-tier"
            label="Tier"
            values={Object.values(ProviderTier)}
            value={tier ?? ""}
            onChange={(value) => setTier(value as ProviderTier)}
          />
        ) : null}
        {command === "panel" ? (
          <EnumSelect
            id="lifecycle-panel"
            label="Panel status"
            values={Object.values(PanelStatus)}
            value={panelStatus}
            onChange={setPanelStatus}
          />
        ) : null}
        {command === "status" ? (
          <EnumSelect
            id="lifecycle-status"
            label="Record status"
            values={Object.values(BaseStatus)}
            value={status}
            onChange={setStatus}
          />
        ) : null}
        {command === "accreditation" ? (
          <>
            <EnumSelect
              id="lifecycle-accreditation"
              label="Accreditation status"
              values={Object.values(AccreditationStatus)}
              value={accreditation}
              onChange={setAccreditation}
            />
            <FormField label="Authority" htmlFor="lifecycle-authority">
              <Input
                id="lifecycle-authority"
                value={authority}
                onChange={(event) => setAuthority(event.target.value)}
                placeholder="e.g. Uganda Counselling Association"
              />
            </FormField>
            <FormField
              label="Expiry"
              description="Leave empty when no expiry is on record. An expiry is valid through that date in Africa/Kampala."
              htmlFor="lifecycle-expiry"
            >
              <Input
                id="lifecycle-expiry"
                type="date"
                value={expiry}
                onChange={(event) => setExpiry(event.target.value)}
              />
            </FormField>
          </>
        ) : null}
      </ReasonDialog>
    </DetailCard>
  )
}

interface CommandInputs {
  tier: ProviderTier
  panelStatus: PanelStatus
  status: BaseStatus
  accreditation: AccreditationStatus
  authority: string
  expiry: string
}

function runCommand(
  id: string,
  command: Command,
  reason: string,
  inputs: CommandInputs,
): Promise<Provider> {
  if (command === "tier") return providersApi.changeTier(id, { tier: inputs.tier, reason })
  if (command === "panel")
    return providersApi.changePanelStatus(id, { panel_status: inputs.panelStatus, reason })
  if (command === "status") return providersApi.changeStatus(id, { status: inputs.status, reason })
  return providersApi.changeAccreditation(id, {
    accreditation_status: inputs.accreditation,
    accreditation_authority: inputs.authority.trim() || null,
    accreditation_expiry: inputs.expiry || null,
    reason,
  })
}

function Field({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <dt className="text-[11px] font-medium tracking-wide text-fg-muted">{label}</dt>
      <dd className="mt-0.5 text-sm text-fg">{value}</dd>
    </div>
  )
}
