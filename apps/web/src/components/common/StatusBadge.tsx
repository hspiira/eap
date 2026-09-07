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

const ICON_CONTAINER_SIZE: Record<NonNullable<StatusBadgeProps["size"]>, string> = {
  sm: "size-5",
  default: "size-6",
  lg: "size-7",
}

export function StatusBadge({ status, size = "default", className, iconOnly }: StatusBadgeProps) {
  const config = getStatusConfig(status)

  if (iconOnly) {
    const Icon = config.icon
    return (
      <TooltipProvider delayDuration={150}>
        <Tooltip>
          <TooltipTrigger asChild>
            <span
              role="img"
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
