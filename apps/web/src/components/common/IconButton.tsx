import * as React from "react"

import { Button } from "@/components/ui/button"

/** Compact icon-only action for page headers. */
export function IconButton({
  label,
  icon: Icon,
  onClick,
}: {
  label: string
  icon: React.ElementType
  onClick?: () => void
}) {
  return (
    <Button
      type="button"
      variant="ghost"
      size="sm"
      onClick={onClick}
      aria-label={label}
      title={label}
      className="size-7 p-0 text-fg/70"
    >
      <Icon className="size-3.5" />
    </Button>
  )
}
