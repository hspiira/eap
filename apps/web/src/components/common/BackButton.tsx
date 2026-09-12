import { ArrowLeft } from "lucide-react"

import { Button } from "@/components/ui/button"
import { useBackTo } from "@/hooks/useBackTo"

/** The leading arrow on a detail page header. */
export function BackButton({ to, label }: { to: string; label: string }) {
  const back = useBackTo(to)
  return (
    <Button
      type="button"
      variant="ghost"
      size="sm"
      onClick={back}
      aria-label={label}
      title={label}
      className="size-7 p-0 text-fg/70"
    >
      <ArrowLeft className="size-3.5" />
    </Button>
  )
}
