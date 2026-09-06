import { useState } from "react"

import { useQuery, useQueryClient } from "@tanstack/react-query"
import { Link } from "@tanstack/react-router"
import { Pencil, Plus, Trash2 } from "lucide-react"

import { membersApi } from "@/api/endpoints/members"
import { DetailCard, RailSection } from "@/components/common/DetailPrimitives"
import { MemberNextOfKinFormSheet } from "@/components/MemberNextOfKinFormSheet"
import { Button } from "@/components/ui/button"
import { useToast } from "@/contexts/ToastContext"
import { useCanWrite } from "@/hooks/useCanWrite"
import { normalizeErrorMessage } from "@/lib/errors"
import type { Member, MemberNextOfKin } from "@/types/entities"

export function MemberNextOfKinCard({ member }: { member: Member }) {
  const queryClient = useQueryClient()
  const canWrite = useCanWrite()
  const toast = useToast()
  const [nextOfKinFormOpen, setNextOfKinFormOpen] = useState(false)
  const [nextOfKinEditing, setNextOfKinEditing] = useState<MemberNextOfKin | null>(null)
  const nextOfKinQuery = useQuery({
    queryKey: ["members", "next-of-kin", member.id],
    queryFn: () => membersApi.listNextOfKin(member.id),
  })
  const openNextOfKinForm = (contact?: MemberNextOfKin) => {
    setNextOfKinEditing(contact ?? null)
    setNextOfKinFormOpen(true)
  }
  const handleNextOfKinDelete = async (contact: MemberNextOfKin) => {
    if (!window.confirm(`Remove ${contact.name} as a next-of-kin contact?`)) return
    try {
      await membersApi.deleteNextOfKin(member.id, contact.id)
      await queryClient.invalidateQueries({ queryKey: ["members", "next-of-kin", member.id] })
      toast.showSuccess("Next-of-kin contact removed")
    } catch (error) {
      toast.showError(normalizeErrorMessage(error, "Could not remove next-of-kin contact"))
    }
  }

  return (
    <>
      <MemberNextOfKinFormSheet
        open={nextOfKinFormOpen}
        onOpenChange={(open) => {
          setNextOfKinFormOpen(open)
          if (!open) setNextOfKinEditing(null)
        }}
        memberId={member.id}
        contact={nextOfKinEditing}
        onSaved={() => {
          void queryClient.invalidateQueries({ queryKey: ["members", "next-of-kin", member.id] })
        }}
      />
      <DetailCard
        title="Next of kin"
        action={
          canWrite ? (
            <Button
              type="button"
              variant="outline"
              size="sm"
              className="h-7 rounded-none gap-1 px-2"
              onClick={() => openNextOfKinForm()}
            >
              <Plus className="size-3.5" />
              Add
            </Button>
          ) : null
        }
      >
        {nextOfKinQuery.isPending ? (
          <p className="text-xs text-fg-muted">Loading contacts…</p>
        ) : nextOfKinQuery.isError ? (
          <p role="alert" className="text-xs text-danger-fg">
            Could not load contacts.{" "}
            <Button
              variant="link"
              className="rounded-none"
              onClick={() => void nextOfKinQuery.refetch()}
            >
              Retry
            </Button>
          </p>
        ) : nextOfKinQuery.data?.length ? (
          <div className="space-y-2">
            {nextOfKinQuery.data.map((contact) => (
              <div
                key={contact.id}
                className="flex items-start justify-between gap-3 border border-fg/10 px-3 py-2"
              >
                <div className="min-w-0">
                  <p className="truncate text-sm font-medium text-fg">
                    {contact.name}
                    {contact.is_primary ? (
                      <span className="ml-2 text-[10px] font-medium tracking-wide text-primary">
                        Primary
                      </span>
                    ) : null}
                  </p>
                  <p className="text-xs text-fg-muted">{contact.relationship}</p>
                  <p className="truncate text-xs text-fg-muted">
                    {[contact.phone, contact.email].filter(Boolean).join(" · ")}
                  </p>
                </div>
                {canWrite ? (
                  <div className="flex shrink-0 items-center gap-1">
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="size-7 rounded-none p-0"
                      onClick={() => openNextOfKinForm(contact)}
                      aria-label={`Edit ${contact.name}`}
                    >
                      <Pencil className="size-3.5" />
                    </Button>
                    <Button
                      type="button"
                      variant="ghost"
                      size="sm"
                      className="size-7 rounded-none p-0 text-danger hover:text-danger"
                      onClick={() => void handleNextOfKinDelete(contact)}
                      aria-label={`Remove ${contact.name}`}
                    >
                      <Trash2 className="size-3.5" />
                    </Button>
                  </div>
                ) : null}
              </div>
            ))}
          </div>
        ) : (
          <p className="text-xs text-fg-muted">No next-of-kin contacts recorded.</p>
        )}
      </DetailCard>
    </>
  )
}

export function MemberBeneficiaries({ member }: { member: Member }) {
  const beneficiariesQuery = useQuery({
    queryKey: ["members", "beneficiaries", member.id],
    queryFn: () => membersApi.listBeneficiaries(member.id),
  })
  return (
    <RailSection title="Beneficiaries">
      {beneficiariesQuery.isPending ? (
        <p className="text-xs text-fg-muted">Loading beneficiaries…</p>
      ) : beneficiariesQuery.isError ? (
        <p role="alert" className="text-xs text-danger-fg">
          Could not load beneficiaries.{" "}
          <Button
            variant="link"
            className="rounded-none"
            onClick={() => void beneficiariesQuery.refetch()}
          >
            Retry
          </Button>
        </p>
      ) : beneficiariesQuery.data?.length ? (
        <div className="space-y-2">
          {beneficiariesQuery.data.map((beneficiary) => (
            <Link
              key={beneficiary.id}
              to="/members/$memberId"
              params={{ memberId: beneficiary.id }}
              className="block border border-fg/10 bg-surface px-2.5 py-2 hover:border-fg/25"
            >
              <p className="truncate text-xs font-medium text-fg">
                {beneficiary.display_label ?? beneficiary.employer_member_id}
              </p>
              <p className="text-[11px] text-fg-muted">{beneficiary.relation}</p>
            </Link>
          ))}
        </div>
      ) : (
        <p className="text-xs text-fg-muted">No beneficiaries linked.</p>
      )}
    </RailSection>
  )
}
