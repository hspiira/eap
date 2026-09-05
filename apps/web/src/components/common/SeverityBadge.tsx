import { cn } from "@/lib/utils"
import { IncidentSeverity } from "@/types/enums"

interface SeverityBadgeProps {
  severity: IncidentSeverity
  className?: string
}

const SEVERITY_TONE: Record<IncidentSeverity, string> = {
  [IncidentSeverity.LOW]: "bg-surface text-fg border-fg/20",
  [IncidentSeverity.MEDIUM]: "bg-primary/10 text-primary border-primary/30",
  [IncidentSeverity.HIGH]: "bg-danger/15 text-danger border-stone/30",
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
