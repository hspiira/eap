import type { LucideIcon } from "lucide-react"

import { Button } from "@/components/ui/button"
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip"
import { cn } from "@/lib/utils"

/**
 * How much an action stands out from the ones beside it.
 *
 * `quiet` is the default and is what most controls are. `raised` sets one
 * apart without making it the page's primary action, which stays a labelled
 * button: a row of identical icons with one of them filled reads as a mistake.
 */
type Emphasis = "quiet" | "raised"

export interface IconButtonProps {
  /** Names the action. Read aloud, shown on hover, and never rendered inline. */
  label: string
  icon: LucideIcon
  onClick?: () => void
  /** Kept rendered rather than hidden, so a row's controls do not shift. */
  disabled?: boolean
  emphasis?: Emphasis
  /** Reads in the destructive colour without being filled with it. */
  destructive?: boolean
}

/**
 * Compact icon-only action, named on hover.
 *
 * The one control for page headers, toolbars and selection bars. A toolbar of
 * labelled buttons reads as a sentence rather than a set of choices, and the
 * labels are the part a reader skips after the first visit: the icon carries
 * the action and the tooltip carries the word for whoever still needs it.
 * `label` is also the accessible name, so the button is never unnamed.
 */
export function IconButton({
  label,
  icon: Icon,
  onClick,
  disabled,
  emphasis = "quiet",
  destructive,
}: IconButtonProps) {
  return (
    <TooltipProvider delayDuration={150}>
      <Tooltip>
        <TooltipTrigger asChild>
          <Button
            type="button"
            variant={emphasis === "raised" ? "outline" : "ghost"}
            size="sm"
            onClick={onClick}
            disabled={disabled}
            aria-label={label}
            className={cn(
              "size-7 shrink-0 p-0 text-fg/70",
              destructive && "text-destructive/80 hover:bg-destructive/10 hover:text-destructive",
            )}
          >
            <Icon className="size-3.5" aria-hidden />
          </Button>
        </TooltipTrigger>
        <TooltipContent>{label}</TooltipContent>
      </Tooltip>
    </TooltipProvider>
  )
}
