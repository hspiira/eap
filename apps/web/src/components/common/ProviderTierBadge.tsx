import { cn } from "@/lib/utils"
import { ProviderTier } from "@/types/enums"

const TIER_TONE: Record<ProviderTier, string> = {
  [ProviderTier.T1]: "bg-natural/15 text-natural border-natural/40",
  [ProviderTier.T2]: "bg-warm text-ink border-ink/20",
  [ProviderTier.T3]: "bg-neutral-100 text-neutral-600 border-neutral-300",
}

export function ProviderTierBadge({ tier, className }: { tier: ProviderTier; className?: string }) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 text-xs font-medium border rounded-none",
        TIER_TONE[tier],
        className,
      )}
    >
      {tier}
    </span>
  )
}
