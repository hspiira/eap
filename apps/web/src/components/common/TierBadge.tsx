import { cn } from "@/lib/utils"
import { ClientTier } from "@/types/enums"

interface TierBadgeProps {
  tier: ClientTier | null | undefined
  className?: string
}

const TIER_LABELS: Record<ClientTier, string> = {
  [ClientTier.A]: "Tier A",
  [ClientTier.B]: "Tier B",
  [ClientTier.C]: "Tier C",
}

const TIER_TONE: Record<ClientTier, string> = {
  [ClientTier.A]: "bg-natural/10 text-natural border-natural/30",
  [ClientTier.B]: "bg-warm text-ink border-ink/20",
  [ClientTier.C]: "bg-neutral-100 text-neutral-600 border-neutral-300",
}

export function TierBadge({ tier, className }: TierBadgeProps) {
  if (!tier) {
    return (
      <span
        className={cn(
          "inline-flex items-center px-2 py-0.5 text-xs font-medium border border-neutral-200 text-neutral-400 rounded-none",
          className,
        )}
        aria-label="Tier not set"
      >
        —
      </span>
    )
  }
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 text-xs font-medium border rounded-none",
        TIER_TONE[tier],
        className,
      )}
      aria-label={TIER_LABELS[tier]}
    >
      {TIER_LABELS[tier]}
    </span>
  )
}
