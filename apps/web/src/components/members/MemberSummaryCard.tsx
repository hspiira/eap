import { Link } from "@tanstack/react-router"
import { ExternalLink, Users, X } from "lucide-react"

import { DetailGrid, DetailRow, RailSection } from "@/components/common/DetailPrimitives"
import { Button } from "@/components/ui/button"
import { memberLabel, nameInitials } from "@/lib/display"
import type { Member } from "@/types/entities"
import { getStatusLabel } from "@/utils/statusColors"

/**
 * The roster preview card: who a member is without leaving the list. Shared by
 * the members list and the client roster tab so the two cannot drift.
 */
export function MemberSummaryCard({ member, onClose }: { member: Member; onClose: () => void }) {
  const label = memberLabel(member)
  const summary = [
    getStatusLabel(member.relation),
    getStatusLabel(member.status),
    member.employer_member_id,
  ]
    .filter(Boolean)
    .join(" · ")

  return (
    <div className="flex min-h-0 flex-1 flex-col border border-fg/10 bg-surface">
      <header className="flex items-start gap-3 border-b border-fg/10 px-4 py-3">
        <span
          aria-hidden
          className="grid size-9 shrink-0 place-items-center bg-primary/10 text-xs font-semibold text-primary"
        >
          {nameInitials(label)}
        </span>
        <div className="min-w-0 flex-1">
          <h3 className="truncate text-sm font-semibold leading-tight text-fg">{label}</h3>
          <p className="mt-1 truncate text-xs text-fg-muted">{summary}</p>
        </div>
        <Button
          type="button"
          variant="ghost"
          size="sm"
          onClick={onClose}
          aria-label="Close details"
          className="size-7 shrink-0 p-0 text-fg-muted"
        >
          <X className="size-4" />
        </Button>
      </header>

      <div className="flex min-h-0 flex-1 flex-col gap-5 overflow-y-auto p-4">
        <RailSection title="Personal">
          <DetailGrid>
            <DetailRow label="Date of birth" value={member.date_of_birth} />
            <DetailRow
              label="Gender"
              value={member.gender ? getStatusLabel(member.gender) : null}
            />
          </DetailGrid>
        </RailSection>
        <RailSection title="Contact" className="border-t border-fg/10 pt-4">
          <DetailGrid>
            <DetailRow label="Phone" value={member.phone} />
            <DetailRow label="Work email" value={member.work_email} />
            <DetailRow label="Personal email" value={member.personal_email} fullWidth />
          </DetailGrid>
        </RailSection>
        <RailSection title="Identification" className="border-t border-fg/10 pt-4">
          <DetailGrid>
            <DetailRow label="Staff number" value={member.staff_number} />
            <DetailRow label="National ID" value={member.national_id} />
            <DetailRow label="Passport" value={member.passport_number} />
          </DetailGrid>
        </RailSection>
        <Link
          to="/members/$memberId"
          params={{ memberId: member.id }}
          className="mt-auto inline-flex items-center gap-1.5 border-t border-fg/10 pt-4 text-sm font-medium text-primary hover:underline"
        >
          Open full profile
          <ExternalLink className="size-3.5" />
        </Link>
      </div>
    </div>
  )
}

export function MemberSummaryPlaceholder({
  description = "Select a row to view their summary.",
}: {
  description?: string
}) {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-1 border border-dashed border-fg/15 p-8 text-center">
      <div className="mb-2 grid size-9 place-items-center bg-primary/10">
        <Users className="size-4 text-primary" />
      </div>
      <h3 className="text-sm font-semibold text-fg">Pick a member</h3>
      <p className="max-w-[24ch] text-xs text-fg/60">{description}</p>
    </div>
  )
}
