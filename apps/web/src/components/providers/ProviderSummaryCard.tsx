import { Link } from "@tanstack/react-router"
import { ExternalLink, Stethoscope, X } from "lucide-react"

import { DetailGrid, DetailRow, RailSection } from "@/components/common/DetailPrimitives"
import { StatusBadge } from "@/components/common/StatusBadge"
import { Button } from "@/components/ui/button"
import { nameInitials } from "@/lib/display"
import type { Provider } from "@/types/entities"
import { getStatusLabel } from "@/utils/statusColors"

/**
 * The directory preview card: where a practitioner stands in onboarding
 * without leaving the list. Mirrors MemberSummaryCard so the two directories
 * read the same way.
 */
export function ProviderSummaryCard({
  provider,
  onClose,
}: {
  provider: Provider
  onClose: () => void
}) {
  const profile = provider.provider_profile
  const name = provider.formal_name || provider.display_name
  const summary = [getStatusLabel(profile.panel_status), profile.tier, profile.region]
    .filter(Boolean)
    .join(" · ")

  return (
    <div className="flex min-h-0 flex-1 flex-col border border-fg/10 bg-surface">
      <header className="flex items-start gap-3 border-b border-fg/10 px-4 py-3">
        <span
          aria-hidden
          className="grid size-9 shrink-0 place-items-center bg-fg/6 text-xs font-semibold text-fg-muted"
        >
          {nameInitials(provider.display_name)}
        </span>
        <div className="min-w-0 flex-1">
          <h3 className="truncate text-sm font-semibold leading-tight text-fg">{name}</h3>
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

      <div className="min-h-0 flex-1 overflow-y-auto">
        <RailSection title="Booking readiness">
          <DetailGrid>
            <DetailRow
              label="Panel"
              value={<StatusBadge status={profile.panel_status} size="sm" />}
            />
            <DetailRow
              label="Accreditation"
              value={<StatusBadge status={profile.accreditation_status} size="sm" />}
            />
            <DetailRow label="Tier" value={profile.tier ?? "Not set"} />
            <DetailRow label="Region" value={profile.region ?? "Not set"} />
          </DetailGrid>
        </RailSection>
        <RailSection title="Contact">
          <DetailGrid>
            <DetailRow label="Email" value={provider.email ?? "None"} />
            <DetailRow label="Phone" value={provider.phone ?? "None"} />
            <DetailRow label="Account" value={provider.user_id ? "Linked" : "None"} />
          </DetailGrid>
        </RailSection>
      </div>

      <footer className="border-t border-fg/10 px-4 py-2.5">
        <Link
          to="/providers/$providerId"
          params={{ providerId: provider.id }}
          className="inline-flex items-center gap-1.5 text-xs font-medium text-primary hover:underline"
        >
          Open full profile
          <ExternalLink className="size-3" />
        </Link>
      </footer>
    </div>
  )
}

export function ProviderSummaryPlaceholder() {
  return (
    <div className="flex flex-1 flex-col items-center justify-center gap-1 border border-dashed border-fg/15 p-8 text-center">
      <div className="mb-2 grid size-9 place-items-center bg-fg/6">
        <Stethoscope className="size-4 text-primary" />
      </div>
      <h3 className="text-sm font-semibold text-fg">Pick a practitioner</h3>
      <p className="max-w-[26ch] text-xs text-fg/60">
        Select a row to see their readiness without leaving the list.
      </p>
    </div>
  )
}
