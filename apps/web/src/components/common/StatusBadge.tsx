import { Badge } from "@/components/ui/badge"
import { cn } from "@/lib/utils"
import { getStatusConfig } from "@/utils/statusConfig"

export interface StatusBadgeProps {
  status: string
  size?: "sm" | "default" | "lg"
  className?: string
}

export function StatusBadge({ status, size = "default", className }: StatusBadgeProps) {
  const config = getStatusConfig(status)
  return (
    <Badge
      className={cn(config.bg, config.text, config.border && `border ${config.border}`, className)}
      size={size}
    >
      {config.label}
    </Badge>
  )
}
