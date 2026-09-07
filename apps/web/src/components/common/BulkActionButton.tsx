import type { LucideIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { cn } from "@/lib/utils"

interface BulkActionButtonProps {
  label: string
  icon: LucideIcon
  destructive?: boolean
  running: boolean
  /** Disabled for a reason other than an in-flight run, e.g. an incomplete input. */
  disabled?: boolean
  onClick: () => void
}

/**
 * The trigger both bulk actions share: the icon alone, named on hover.
 *
 * A selection bar held a row of words of equal weight, which read as a
 * sentence rather than a set of choices, and the one that could not be taken
 * back sat a slip away from the one that could. The icon carries the action
 * and the tooltip and label carry the word. Destructive reads in the
 * destructive colour without being filled with it: the filled button belongs
 * in the confirm dialog, where the decision is actually taken.
 */
export function BulkActionButton({
  label,
  icon: Icon,
  destructive,
  running,
  disabled,
  onClick,
}: BulkActionButtonProps) {
  return (
    <TooltipProvider delayDuration={150}>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            type="button"
            variant="ghost"
            size="sm"
            aria-label={label}
            className={cn(
              "size-7 p-0 text-fg/70",
              destructive && "text-destructive/80 hover:bg-destructive/10 hover:text-destructive",
            )}
            disabled={running || disabled}
            onClick={onClick}
          >
            <Icon className="size-3.5" aria-hidden />
          </Button>
        </TooltipTrigger>
        <TooltipContent>{label}</TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
