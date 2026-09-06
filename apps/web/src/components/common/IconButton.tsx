import * as React from "react"

import { Button } from "@/components/ui/button"

/** Compact icon-only action for page headers. */
export function IconButton({
  label,
  icon: Icon,
  onClick,
  disabled,
}: {
  label: string
  icon: React.ElementType
  onClick?: () => void
  /** Kept rendered rather than hidden, so a row's controls do not shift. */
  disabled?: boolean
}) {
  return (
    <Button
      type="button"
      variant="ghost"
      size="sm"
      onClick={onClick}
      disabled={disabled}
      aria-label={label}
      title={label}
      className="size-7 p-0 text-fg/70"
    >
      <Icon className="size-3.5" />
    </Button>
  )
}
