import { useState } from "react"

import { useQueryClient } from "@tanstack/react-query"
import { createFileRoute, useNavigate } from "@tanstack/react-router"
import { Building, Pencil } from "lucide-react"

import { providerOrganisationsApi } from "@/api/endpoints/provider-organisations"
import { DetailCard, DetailGrid, DetailRow } from "@/components/common/DetailPrimitives"
import { renderDetailState } from "@/components/common/DetailStates"
import { PageShell } from "@/components/common/PageShell"
import { StatusBadge } from "@/components/common/StatusBadge"
import { OrganisationAffiliationsPanel } from "@/components/providers/OrganisationAffiliationsPanel"
import { ProviderOrganisationFormSheet } from "@/components/providers/ProviderOrganisationFormSheet"
import { ReasonDialog } from "@/components/providers/ReasonDialog"
import { Button } from "@/components/ui/button"
import { useToast } from "@/contexts/ToastContext"
import { useCanWrite, useCurrentRole } from "@/hooks/useCanWrite"
import { normalizeErrorMessage } from "@/lib/errors"
import { entityDetailKey, useEntityDetail } from "@/lib/queries"
import type { ProviderOrganisation } from "@/types/entities"
import { ProviderApprovalStatus, TenantRole } from "@/types/enums"

export const Route = createFileRoute("/provider-organisations/$organisationId")({
  component: ProviderOrganisationDetailPage,
})

type Command = "approve" | "suspend" | "revoke" | "deactivate" | "reactivate"

const COMMAND_COPY: Record<Command, { title: string; description: string }> = {
  approve: {
    title: "Approve this supplier",
    description:
      "Approval lets practitioners deliver sessions through this firm. It is the firm's supplier approval and does not accredit any individual.",
  },
  suspend: {
    title: "Suspend this supplier",
    description:
      "New organisation-delivered bookings through this firm will be refused. Completed sessions and their attribution are unchanged.",
  },
  revoke: {
    title: "Revoke this supplier's approval",
    description:
      "New organisation-delivered bookings through this firm will be refused. Completed sessions and their attribution are unchanged.",
  },
  deactivate: {
    title: "Deactivate this organisation",
    description:
      "The firm is kept because affiliations and past sessions refer to it. It is not deleted, and no history is removed.",
  },
  reactivate: {
    title: "Reactivate this organisation",
    description: "The firm becomes active again. Supplier approval is a separate state.",
  },
}

function ApprovalCommands({
  organisation,
  onSelect,
}: {
  organisation: ProviderOrganisation
  onSelect: (command: Command) => void
}) {
  const approved = organisation.approval_status === ProviderApprovalStatus.APPROVED
  return (
    <div className="flex flex-wrap gap-2">
      {approved ? null : (
        <Button type="button" variant="outline" size="sm" onClick={() => onSelect("approve")}>
          Approve
        </Button>
      )}
      {approved ? (
        <Button type="button" variant="outline" size="sm" onClick={() => onSelect("suspend")}>
          Suspend
        </Button>
      ) : null}
      <Button type="button" variant="outline" size="sm" onClick={() => onSelect("revoke")}>
        Revoke approval
      </Button>
      {organisation.is_active ? (
        <Button type="button" variant="outline" size="sm" onClick={() => onSelect("deactivate")}>
          Deactivate
        </Button>
      ) : (
        <Button type="button" variant="outline" size="sm" onClick={() => onSelect("reactivate")}>
          Reactivate
        </Button>
      )}
    </div>
  )
}

function ProviderOrganisationDetailPage() {
  const { organisationId } = Route.useParams()
  const navigate = useNavigate()
  const queryClient = useQueryClient()
  const toast = useToast()
  const canWrite = useCanWrite()
  const isAdmin = useCurrentRole() === TenantRole.ADMIN
  const [editOpen, setEditOpen] = useState(false)
  const [command, setCommand] = useState<Command | null>(null)

  const query = useEntityDetail<ProviderOrganisation>({
    resource: "provider-organisations",
    id: organisationId,
    detailFn: providerOrganisationsApi.getById,
  })

  const back = () => void navigate({ to: "/provider-organisations" })
  const state = renderDetailState(query, {
    icon: Building,
    breadcrumb: "Provider organisations",
    entity: "organisation",
    backTo: back,
    backLabel: "Back to organisations",
  })
  if (state) return state

  const organisation = query.data as ProviderOrganisation

  const run = async (reason: string) => {
    if (!command) return
    try {
      await providerOrganisationsApi.runCommand(organisation.id, command, reason)
      await queryClient.invalidateQueries({
        queryKey: entityDetailKey("provider-organisations", organisation.id),
      })
      await queryClient.invalidateQueries({ queryKey: ["provider-organisations", "list"] })
      setCommand(null)
      toast.showSuccess("Change recorded")
    } catch (error) {
      toast.showError(normalizeErrorMessage(error, "Could not record the change"))
    }
  }

  const deliverable =
    organisation.is_active && organisation.approval_status === ProviderApprovalStatus.APPROVED

  return (
    <PageShell
      icon={Building}
      trail={[{ label: "Provider organisations", to: "/provider-organisations" }]}
      title={organisation.name}
      actions={
        canWrite ? (
          <Button
            type="button"
            variant="outline"
            size="sm"
            className="h-7 gap-1.5 rounded-none px-2"
            onClick={() => setEditOpen(true)}
          >
            <Pencil className="size-3.5" />
            Edit
          </Button>
        ) : null
      }
    >
      <div className="flex flex-wrap items-center gap-2 border-b border-fg/10 bg-surface px-3 py-2">
        <StatusBadge status={organisation.approval_status} size="sm" />
        <span className="text-xs text-fg/70">{organisation.is_active ? "Active" : "Inactive"}</span>
        {deliverable ? null : (
          <span className="text-xs text-danger-fg">
            Organisation delivery through this firm will be refused.
          </span>
        )}
      </div>

      <ProviderOrganisationFormSheet
        open={editOpen}
        onOpenChange={setEditOpen}
        organisation={organisation}
      />

      <div className="min-h-0 flex-1 overflow-auto p-5">
        <div className="mx-auto grid max-w-5xl gap-4 lg:grid-cols-2">
          <DetailCard title="Organisation">
            <DetailGrid>
              <DetailRow label="Name" value={organisation.name} />
              <DetailRow
                label="Registration number"
                value={organisation.registration_number ?? ""}
              />
              <DetailRow label="Contact email" value={organisation.contact_email ?? ""} />
              <DetailRow label="Contact phone" value={organisation.contact_phone ?? ""} />
            </DetailGrid>
          </DetailCard>

          <DetailCard title="Supplier approval">
            <DetailGrid>
              <DetailRow
                label="Approval"
                value={<StatusBadge status={organisation.approval_status} size="sm" />}
              />
              <DetailRow label="Record" value={organisation.is_active ? "Active" : "Inactive"} />
            </DetailGrid>
            <p className="mt-3 text-xs text-fg-muted">
              Approval of a firm is not accreditation of a person. Each practitioner is assessed
              independently.
            </p>
            <div className="mt-4 border-t border-fg/10 pt-4">
              {isAdmin ? (
                <ApprovalCommands organisation={organisation} onSelect={setCommand} />
              ) : (
                <p className="text-sm text-fg-muted">
                  Approval and active state are changed by a tenant admin.
                </p>
              )}
            </div>
          </DetailCard>

          <div className="lg:col-span-2">
            <OrganisationAffiliationsPanel organisationId={organisation.id} />
          </div>
        </div>
      </div>

      <ReasonDialog
        open={command !== null}
        onOpenChange={(open) => (open ? null : setCommand(null))}
        title={command ? COMMAND_COPY[command].title : ""}
        description={command ? COMMAND_COPY[command].description : ""}
        confirmLabel="Confirm"
        onConfirm={run}
      />
    </PageShell>
  )
}
