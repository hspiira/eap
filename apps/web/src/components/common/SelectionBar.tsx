import { Button } from "@/components/ui/button"

interface SelectionBarProps {
  count: number
  onClear: () => void
  children?: React.ReactNode
}

export function SelectionBar({ count, onClear, children }: SelectionBarProps) {
  if (count === 0) return null
  return (
    <div className="flex shrink-0 items-center gap-2 border-b border-primary/15 bg-primary/5 px-4 py-1.5 text-sm text-fg">
      <span>
        {count} {count === 1 ? "item" : "items"} selected
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
