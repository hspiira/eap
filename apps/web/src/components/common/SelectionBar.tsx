import type { ReactNode } from "react"

import { Button } from "@/components/ui/button"

interface SelectionBarProps {
  count: number
  onClear: () => void
  children?: ReactNode
}

export function SelectionBar({ count, onClear, children }: SelectionBarProps) {
  if (count === 0) return null
  return (
    <div className="flex shrink-0 flex-wrap items-center gap-1 border-b border-primary/15 bg-primary/5 px-4 py-1.5 text-sm text-fg">
      <span className="mr-1.5 tabular-nums">
        <strong className="font-medium">{count}</strong> selected
      </span>
      {children}
      <Button
        type="button"
        variant="link"
        size="sm"
        onClick={onClear}
        className="ml-auto h-auto p-0 text-primary"
      >
        Clear
      </Button>
    </div>
  )
}
