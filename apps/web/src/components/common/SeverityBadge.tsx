import { cn } from "@/lib/utils"
import { IncidentSeverity } from "@/types/enums"

interface SeverityBadgeProps {
  severity: IncidentSeverity
  className?: string
}

const SEVERITY_TONE: Record<IncidentSeverity, string> = {
  [IncidentSeverity.LOW]: "bg-warm text-ink border-ink/20",
  [IncidentSeverity.MEDIUM]: "bg-natural/10 text-natural border-natural/30",
  [IncidentSeverity.HIGH]: "bg-stone/15 text-stone border-stone/30",
  [IncidentSeverity.CRITICAL]: "bg-danger-soft/30 text-danger border-danger/40",
}

export function SeverityBadge({ severity, className }: SeverityBadgeProps) {
  return (
    <span
      className={cn(
        "inline-flex items-center px-2 py-0.5 text-xs font-medium border rounded-none",
        SEVERITY_TONE[severity],
        className,
      )}
    >
      {severity}
    </span>
  )
}
