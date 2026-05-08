import { ChevronLeft, ChevronRight, Info, Link2, Lock, Receipt, ShoppingCart } from "lucide-react"

const steps = [
  { icon: Link2, label: "Link", active: false },
  { icon: Lock, label: "Lock", active: false },
  { icon: ShoppingCart, label: "Cart", active: false },
  { icon: Receipt, label: "Receipt", active: true },
]

export function OnSiteBehaviorCard() {
  return (
    <div className="border border-border/25 bg-white p-4">
      <div className="mb-4 flex items-center justify-between">
        <div className="flex items-center gap-2">
          <h3 className="text-sm font-semibold text-fg">On-site behavior</h3>
          <button
            type="button"
            className="flex h-5 w-5 items-center justify-center border border-border/40 bg-surface/50 text-fg"
            aria-label="Info"
          >
            <Info className="h-3 w-3" />
          </button>
        </div>
        <div className="flex items-center gap-1.5 text-xs font-medium text-primary">
          <span className="h-1.5 w-1.5 shrink-0 bg-primary" />
          Live
        </div>
      </div>

      <div className="mb-4 flex items-center gap-2">
        <button
          type="button"
          className="flex items-center justify-center p-0 text-fg/70 hover:text-fg"
          aria-label="Previous"
        >
          <ChevronLeft className="h-4 w-4" />
        </button>
        <span className="border border-border/30 bg-neutral-50 px-3 py-1.5 text-sm text-fg">
          United Kingdom
        </span>
        <button
          type="button"
          className="flex items-center justify-center p-0 text-fg/70 hover:text-fg"
          aria-label="Next"
        >
          <ChevronRight className="h-4 w-4" />
        </button>
      </div>

      <div className="pt-2">
        <div className="flex items-center">
          {steps.map(({ icon: Icon, active }, i) => (
            <div key={i} className="flex flex-1 items-center">
              <div
                className={`flex h-9 w-9 shrink-0 items-center justify-center border ${
                  active
                    ? "border-danger-soft bg-danger-soft text-white"
                    : "border-border/40 bg-white text-fg"
                }`}
              >
                <Icon className="h-4 w-4" />
              </div>
              {i < steps.length - 1 && (
                <div className="relative flex flex-1 items-center">
                  <div className="h-0.5 w-full bg-border/40" />
                  {i === 1 && (
                    <span className="absolute left-1/2 top-0 -translate-x-1/2 -translate-y-full pb-0.5 text-xs text-fg/60">
                      2s
                    </span>
                  )}
                </div>
              )}
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
