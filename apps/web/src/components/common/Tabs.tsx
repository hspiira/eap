import * as React from "react"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

interface TabsContextValue {
  value: string
  setValue: (value: string) => void
  idBase: string
}

const TabsContext = React.createContext<TabsContextValue | null>(null)

function useTabs(): TabsContextValue {
  const ctx = React.useContext(TabsContext)
  if (!ctx) throw new Error("Tabs.* must be used within <Tabs>")
  return ctx
}

interface TabsProps {
  value: string
  onValueChange: (value: string) => void
  children: React.ReactNode
  className?: string
}

export function Tabs({ value, onValueChange, children, className }: TabsProps) {
  const idBase = React.useId()
  const ctx = React.useMemo(
    () => ({ value, setValue: onValueChange, idBase }),
    [value, onValueChange, idBase],
  )
  return (
    <TabsContext.Provider value={ctx}>
      <div className={cn("flex min-h-0 flex-1 flex-col", className)}>{children}</div>
    </TabsContext.Provider>
  )
}

export function TabsList({
  children,
  className,
}: {
  children: React.ReactNode
  className?: string
}) {
  return (
    <div
      role="tablist"
      className={cn(
        "flex h-10 shrink-0 items-end gap-0.5 overflow-x-auto border-b border-fg/10 px-3",
        className,
      )}
    >
      {children}
    </div>
  )
}

interface TabProps {
  value: string
  children: React.ReactNode
  count?: number | null
  icon?: React.ElementType
  disabled?: boolean
}

export function Tab({ value, children, count, icon: Icon, disabled }: TabProps) {
  const { value: active, setValue, idBase } = useTabs()
  const selected = active === value
  return (
    <Button
      type="button"
      role="tab"
      variant="ghost"
      id={`${idBase}-tab-${value}`}
      aria-controls={`${idBase}-panel-${value}`}
      aria-selected={selected}
      aria-disabled={disabled || undefined}
      tabIndex={selected ? 0 : -1}
      disabled={disabled}
      onClick={() => !disabled && setValue(value)}
      className={cn(
        "relative -mb-px h-9 shrink-0 gap-1.5 rounded-none border-b-2 border-transparent px-2.5 text-sm font-medium text-fg/60 hover:bg-transparent hover:text-fg",
        selected && "border-primary text-fg",
        disabled && "pointer-events-none opacity-50",
      )}
    >
      {Icon ? <Icon className="size-3.5" /> : null}
      <span>{children}</span>
      {count != null ? (
        <span
          className={cn(
            "ml-0.5 inline-flex h-4 min-w-[1rem] items-center justify-center rounded-sm bg-fg/10 px-1 font-mono text-[10px] text-fg/65",
            selected && "bg-primary/15 text-primary",
          )}
        >
          {count}
        </span>
      ) : null}
    </Button>
  )
}

export function TabPanel({
  value,
  children,
  className,
}: {
  value: string
  children: React.ReactNode
  className?: string
}) {
  const { value: active, idBase } = useTabs()
  if (active !== value) return null
  return (
    <div
      role="tabpanel"
      id={`${idBase}-panel-${value}`}
      aria-labelledby={`${idBase}-tab-${value}`}
      className={cn("min-h-0 flex-1", className)}
    >
      {children}
    </div>
  )
}
