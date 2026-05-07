import { ChevronDown, Mic, Plus, Send, X } from "lucide-react"


export function QueryInputCard() {
  return (
    <div className="w-full space-y-3">
      <div className="flex flex-wrap items-center justify-between gap-3">
        <div className="flex rounded-none bg-[#E6E0D7] p-0.5">
          <button
            type="button"
            className="rounded-none bg-[#5A626A] px-4 py-2 text-sm font-medium text-white"
          >
            Rent
          </button>
          <button
            type="button"
            className="rounded-none px-4 py-2 text-sm font-medium text-[#5A626A] hover:bg-[#E0DAD2]"
          >
            Buy
          </button>
        </div>
        <div className="flex items-center rounded-none bg-[#5A626A] pl-3 pr-1 py-1.5">
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
            className="ml-2 flex h-7 w-7 items-center justify-center rounded-none bg-[#5A626A] text-white hover:bg-[#4a5258]"
            aria-label="Clear filters"
          >
            <X className="h-3.5 w-3.5" />
          </button>
        </div>
      </div>
      <div className="rounded-none border border-[#bfc4c9]/25 bg-white p-4">
        <p className="min-h-[4rem] text-sm leading-relaxed text-[#5A626A]">
          San Francisco family home for 4 persons, price between $4K-$7K, with a terrace, pets allowed.
        </p>
        <div className="mt-4 flex items-center justify-between border-t border-[#bfc4c9]/20 pt-3">
          <button
            type="button"
            className="flex items-center gap-1.5 text-sm text-[#5A626A]/80 hover:text-[#5A626A]"
          >
            <Plus className="h-4 w-4" />
            <span>4.10</span>
            <ChevronDown className="h-3.5 w-3.5" />
          </button>
          <div className="flex items-center gap-2">
            <button
              type="button"
              className="flex h-9 w-9 items-center justify-center rounded-none bg-[#5A626A] text-white hover:bg-[#4a5258]"
              aria-label="Voice input"
            >
              <Mic className="h-4 w-4" />
            </button>
            <button
              type="button"
              className="flex h-9 w-9 items-center justify-center rounded-none bg-[#5A626A] text-white hover:bg-[#4a5258]"
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
