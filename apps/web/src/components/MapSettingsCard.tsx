import { BookOpen, ChevronDown, ChevronUp, X } from "lucide-react"

import { cn } from "@/lib/utils"

const speedRanges = [
  { label: "0 - 29 km/h", color: "bg-fg" },
  { label: "30 - 69 km/h", color: "bg-primary" },
  { label: "69 - ∞ km/h", color: "bg-danger" },
]

export function MapSettingsCard() {
  return (
    <div
      className={cn(
        "flex flex-col rounded-lg border border-border/25 bg-white",
        "shadow-[0_1px_4px_rgba(0,0,0,0.06)]"
      )}
    >
      <div className="flex items-center justify-between border-b border-border/20 px-4 py-3">
        <div className="flex items-center gap-2">
          <BookOpen className="h-4 w-4 text-fg" />
          <h3 className="text-sm font-semibold text-fg">Map settings</h3>
        </div>
        <button
          type="button"
          className="p-1 text-fg/70 hover:bg-surface-tile hover:text-fg"
          aria-label="Close"
        >
          <X className="h-4 w-4" />
        </button>
      </div>
      <div className="flex flex-col gap-4 p-4">
        <div className="grid grid-cols-12 gap-4">
          <div className="col-span-8">
            <label className="mb-1 block text-xs font-medium text-fg/80">Line color</label>
            <div className="flex h-9 items-center justify-between rounded border border-border/40 bg-neutral-50 px-3">
              <span className="text-sm text-fg">By Speed</span>
              <ChevronDown className="h-3.5 w-3.5 shrink-0 text-fg/60" />
            </div>
          </div>
          <div className="col-span-4">
            <label className="mb-1 block text-xs font-medium text-fg/80">Thickness</label>
            <div className="flex h-9 items-center justify-between rounded border border-border/40 bg-neutral-50 px-3">
              <span className="text-sm text-fg">4 px</span>
              <div className="flex flex-col">
                <button type="button" className="text-fg/60 hover:text-fg" aria-label="Increase">
                  <ChevronUp className="h-3.5 w-3.5" />
                </button>
                <button type="button" className="text-fg/60 hover:text-fg" aria-label="Decrease">
                  <ChevronDown className="h-3.5 w-3.5" />
                </button>
              </div>
            </div>
          </div>
        </div>
        <div className="flex items-center gap-3">
          {speedRanges.map(({ label, color }) => (
            <div key={label} className="flex min-w-0 flex-1 items-center gap-1.5">
              <div className={cn("h-1.5 w-8 shrink-0 rounded-full", color)} />
              <span className="truncate text-xs leading-tight text-fg/80">{label}</span>
            </div>
          ))}
        </div>
        <div>
          <label className="mb-1.5 block text-xs font-medium text-fg/80">Markings</label>
          <div className="grid grid-cols-11 gap-1">
            {[
              { label: "3", className: "rounded-md bg-neutral-200 text-fg text-xs font-semibold" },
              { label: "@", className: "rounded-md bg-neutral-200 text-fg text-xs" },
              { label: "Y", className: "rounded-md bg-neutral-200 text-fg text-xs font-semibold" },
              { label: "", className: "rounded-sm bg-danger" },
              { label: "B", className: "rounded-md bg-primary text-white text-xs font-bold" },
              { label: "⚡", className: "rounded-md bg-accent-olive text-white text-xs" },
              { label: "P", className: "rounded-md bg-danger-soft text-fg text-xs font-bold" },
              { label: "", className: "rounded-sm border border-fg/50 bg-white" },
              { label: "", className: "rounded-full bg-fg ring-2 ring-white ring-offset-0.5" },
              { label: "P", className: "rounded-md border border-fg/40 bg-white text-fg text-xs font-bold" },
              { label: "S", className: "rounded-md border border-fg/40 bg-white text-fg text-xs font-semibold" },
            ].map((item, i) => (
              <div
                key={i}
                className={cn(
                  "flex aspect-square min-h-0 w-full max-w-full items-center justify-center border border-border/20",
                  item.className
                )}
              >
                {item.label}
              </div>
            ))}
          </div>
        </div>
      </div>
    </div>
  )
}
