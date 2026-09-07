import { AlertCircle, CheckCircle2, Circle, Clock, type LucideIcon } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { cn } from "@/lib/utils"
import { getStatusConfig } from "@/utils/statusConfig"

export interface StatusBadgeProps {
  status: string
  size?: "sm" | "default" | "lg"
  className?: string
  /** Render a colored icon with the label on hover, instead of text. Saves column width. */
  iconOnly?: boolean
}

/** Keyed by the same `bg-*` tone getStatusColors already assigns, so the icon tracks the color without a second status-keyword map. */
const TONE_ICON: Record<string, LucideIcon> = {
  "bg-primary": CheckCircle2,
  "bg-warning": Clock,
  "bg-danger": AlertCircle,
  "bg-muted": Circle,
}

const ICON_CONTAINER_SIZE: Record<NonNullable<StatusBadgeProps["size"]>, string> = {
  sm: "size-5",
  default: "size-6",
  lg: "size-7",
}

export function StatusBadge({ status, size = "default", className, iconOnly }: StatusBadgeProps) {
  const config = getStatusConfig(status)

  if (iconOnly) {
    const Icon = TONE_ICON[config.bg] ?? Circle
    return (
      <TooltipProvider delayDuration={150}>
        <Tooltip>
          <TooltipTrigger asChild>
            <span
              aria-label={config.label}
              className={cn(
                "inline-flex items-center justify-center rounded-sm",
                config.bg,
                config.text,
                config.border && `border ${config.border}`,
                ICON_CONTAINER_SIZE[size],
                className,
              )}
            >
              <Icon className="size-3.5" aria-hidden />
            </span>
          </TooltipTrigger>
          <TooltipContent>{config.label}</TooltipContent>
        </Tooltip>
      </TooltipProvider>
    )
  }

  return (
    <Badge
      className={cn(config.bg, config.text, config.border && `border ${config.border}`, className)}
      size={size}
    >
      {config.label}
    </Badge>
  )
}
