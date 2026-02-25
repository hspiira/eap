import { RotateCcw, ChevronRight } from "lucide-react"
import { cn } from "@/lib/utils"

export function ErrorCard() {
  return (
    <div className="w-full rounded-none border border-[#5A626A]/30 bg-[#5A626A] p-4">
      <div className="space-y-3 text-sm">
        <div className="leading-relaxed text-white/95">
          <span className="font-medium">TimeoutError:</span> Supplier API timed out after 30 s at
          step &quot;Fetch <span className="text-natural">from API</span>&quot;
        </div>
        <div className="pt-2">
          <div className="mb-1.5 text-xs font-medium text-white/80">Stack trace excerpt:</div>
          <div className="font-mono text-xs leading-relaxed">
            <div className="text-white/90">
              at httpClient.<span className="text-[#D0B5B3]">request</span> (http.js:<span className="text-[#b85c4a]">45</span>)
            </div>
            <div className="text-white/90">
              at OrdersImporter.<span className="text-[#D0B5B3]">fetchNew</span> (orders_importer.js:<span className="text-[#b85c4a]">102</span>)
            </div>
          </div>
        </div>
      </div>
      <div className="mt-4 flex gap-2">
        <button
          type="button"
          className={cn(
            "flex items-center gap-2 rounded-none border border-[#5A626A] bg-[#6e6e6e] px-3 py-2 text-sm text-white/95",
            "hover:bg-[#5A626A]"
          )}
        >
          <RotateCcw className="h-3.5 w-3.5" />
          Re-run
        </button>
        <button
          type="button"
          className={cn(
            "flex items-center gap-1 rounded-none border border-[#5A626A] bg-[#6e6e6e] px-3 py-2 text-sm text-white/95",
            "hover:bg-[#5A626A]"
          )}
        >
          Full log
          <ChevronRight className="h-3.5 w-3.5" />
        </button>
      </div>
    </div>
  )
}
