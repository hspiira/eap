import type { ReactNode } from "react"

import { cn } from "@/lib/utils"

export interface EntityNameCellProps {
  /** Initials shown in the avatar circle. Ignored when `icon` is given. */
  initials?: string
  /** An icon node shown in the avatar circle instead of initials. */
  icon?: ReactNode
  name: string
  className?: string
}

/**
 * The avatar-plus-name content for a table row's first, linked column. Wrap
 * it in the row's own typed `<Link>` so route params stay type-checked per
 * route; this only standardizes the avatar and label markup and the
 * group-hover color shared by every entity list table.
 */
export function EntityNameCell({ initials, icon, name, className }: EntityNameCellProps) {
  return (
    <>
      <span
        aria-hidden
        className="grid size-6 shrink-0 place-items-center bg-fg/6 text-[10px] font-semibold text-fg-muted"
      >
        {icon ?? initials}
      </span>
      <span
        className={cn("truncate text-sm font-medium text-fg group-hover:text-primary", className)}
      >
        {name}
      </span>
    </>
  )
}
