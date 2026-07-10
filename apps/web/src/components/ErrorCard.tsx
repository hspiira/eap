import { ChevronRight, RotateCcw } from "lucide-react"

import { Button } from "@/components/ui/button"
import { cn } from "@/lib/utils"

export function ErrorCard() {
  return (
    <div className="w-full rounded-none border border-fg/30 bg-fg p-4">
      <div className="space-y-3 text-sm">
        <div className="leading-relaxed text-white/95">
          <span className="font-medium">TimeoutError:</span> Supplier API timed out after 30 s at
          step &quot;Fetch <span className="text-primary">from API</span>&quot;
        </div>
        <div className="pt-2">
          <div className="mb-1.5 text-xs font-medium text-white/80">Stack trace excerpt:</div>
          <div className="font-mono text-xs leading-relaxed">
            <div className="text-white/90">
              at httpClient.<span className="text-danger-soft">request</span> (http.js:<span className="text-danger">45</span>)
            </div>
            <div className="text-white/90">
              at OrdersImporter.<span className="text-danger-soft">fetchNew</span> (orders_importer.js:<span className="text-danger">102</span>)
            </div>
          </div>
        </div>
      </div>
      <div className="mt-4 flex gap-2">
        <Button
          type="button"
          variant="outline"
          className={cn(
            "h-auto gap-2 rounded-none border-fg bg-surface-shadow px-3 py-2 text-sm text-white/95",
            "hover:bg-fg hover:text-white/95"
          )}
        >
          <RotateCcw className="h-3.5 w-3.5" />
          Re-run
        </Button>
        <Button
          type="button"
          variant="outline"
          className={cn(
            "h-auto gap-1 rounded-none border-fg bg-surface-shadow px-3 py-2 text-sm text-white/95",
            "hover:bg-fg hover:text-white/95"
          )}
        >
          Full log
          <ChevronRight className="h-3.5 w-3.5" />
        </Button>
      </div>
    </div>
  )
}
