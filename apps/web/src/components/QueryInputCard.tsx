import { ChevronDown, Mic, Plus, Send, X } from "lucide-react"


export function QueryInputCard() {
  return (
    <div className="w-full space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex rounded-none bg-warm p-0.5">
          <button
            type="button"
            className="rounded-none bg-ink px-4 py-2 text-sm font-medium text-white"
          >
            Rent
          </button>
          <button
            type="button"
            className="rounded-none px-4 py-2 text-sm font-medium text-ink hover:bg-warm-dark"
          >
            Buy
          </button>
        </div>
        <div className="flex items-center rounded-none bg-ink pl-3 pr-1 py-1.5">
          <button type="button" className="flex items-center gap-1 text-sm text-white">
            Location
            <ChevronDown className="h-3.5 w-3.5" />
          </button>
          <div className="mx-2 h-4 w-px bg-white/40" />
          <button type="button" className="flex items-center gap-1 text-sm text-white">
            Bedrooms
            <ChevronDown className="h-3.5 w-3.5" />
          </button>
          <div className="mx-2 h-4 w-px bg-white/40" />
          <button type="button" className="flex items-center gap-1 text-sm text-white">
            Price
            <ChevronDown className="h-3.5 w-3.5" />
          </button>
          <button
            type="button"
            className="ml-2 flex h-7 w-7 items-center justify-center rounded-none bg-ink text-white hover:bg-surface-slate-light"
            aria-label="Clear filters"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>
      <div className="rounded-none border border-border/25 bg-white p-4">
        <p className="min-h-[4rem] text-sm leading-relaxed text-ink">
          San Francisco family home for 4 persons, price between $4K-$7K, with a terrace, pets allowed.
        </p>
        <div className="mt-4 flex items-center justify-between border-t border-border/20 pt-3">
          <button
            type="button"
            className="flex items-center gap-1.5 text-sm text-ink/80 hover:text-ink"
          >
            <Plus className="h-4 w-4" />
            <span>4.10</span>
            <ChevronDown className="h-3.5 w-3.5" />
          </button>
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="flex h-9 w-9 items-center justify-center rounded-none bg-ink text-white hover:bg-surface-slate-light"
              aria-label="Voice input"
            >
              <Mic className="h-4 w-4" />
            </button>
            <button
              type="button"
              className="flex h-9 w-9 items-center justify-center rounded-none bg-ink text-white hover:bg-surface-slate-light"
              aria-label="Send"
            >
              <Send className="h-4 w-4" />
            </button>
          </div>
        </div>
      </div>
    </div>
  )
}
