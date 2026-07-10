import { CalendarDays, ChevronLeft, ChevronRight, Headphones, Info, Pill, Stethoscope } from "lucide-react"

import { Badge } from "@/components/ui/badge"
import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import {
  Tooltip,
  TooltipContent,
  TooltipTrigger,
} from "@/components/ui/tooltip"
import { cn } from "@/lib/utils"

interface FunnelStage {
  id: string
  label: string
  icon: React.ElementType
  count: number
}

interface OnSiteBehaviorCardProps {
  title?: string
  subtitle?: string
  stages?: ReadonlyArray<FunnelStage>
  totalLabel?: string
  className?: string
}

const DEFAULT_STAGES: ReadonlyArray<FunnelStage> = [
  { id: "intake", label: "Intake", icon: CalendarDays, count: 1240 },
  { id: "session", label: "Session", icon: Headphones, count: 980 },
  { id: "review", label: "Review", icon: Stethoscope, count: 612 },
  { id: "followup", label: "Follow-up", icon: Pill, count: 414 },
]

export function OnSiteBehaviorCard({
  title = "Care funnel",
  subtitle = "Last 30 days",
  stages = DEFAULT_STAGES,
  totalLabel = "Active cases",
  className,
}: OnSiteBehaviorCardProps = {}) {
  const max = stages.reduce((acc, s) => Math.max(acc, s.count), 0) || 1

  return (
    <Card className={cn("rounded-md", className)}>
      <CardHeader className="flex-row items-center justify-between gap-2 space-y-0 border-b border-border-subtle p-3">
        <div className="flex items-center gap-2">
          <CardTitle className="text-sm font-semibold text-fg">
            {title}
          </CardTitle>
          <Tooltip>
            <TooltipTrigger asChild>
              <Button
                type="button"
                variant="ghost"
                size="icon"
                className="size-5 text-fg-subtle hover:text-fg"
                aria-label="Funnel info"
              >
                <Info className="size-3.5" />
              </Button>
            </TooltipTrigger>
            <TooltipContent side="bottom">
              Counts are scoped to {subtitle.toLowerCase()}.
            </TooltipContent>
          </Tooltip>
        </div>
        <div className="flex items-center gap-1">
          <Button variant="ghost" size="icon" className="size-7" aria-label="Previous period">
            <ChevronLeft className="size-3.5" />
          </Button>
          <span className="font-mono text-xs tabular-nums text-fg-muted">
            {subtitle}
          </span>
          <Button variant="ghost" size="icon" className="size-7" aria-label="Next period">
            <ChevronRight className="size-3.5" />
          </Button>
        </div>
      </CardHeader>
      <CardContent className="grid gap-3 p-4">
        <ol className="grid gap-2">
          {stages.map((s, i) => {
            const ratio = s.count / max
            return (
              <li key={s.id} className="grid gap-1">
                <div className="flex items-center gap-2 text-sm">
                  <span
                    className="grid size-7 shrink-0 place-items-center rounded-md bg-muted text-fg-muted"
                    aria-hidden
                  >
                    <s.icon className="size-3.5" />
                  </span>
                  <span className="font-medium text-fg">{s.label}</span>
                  <span className="ml-auto font-mono tabular-nums text-fg-muted">
                    {s.count.toLocaleString()}
                  </span>
                </div>
                <div
                  className="ml-9 h-1.5 overflow-hidden rounded-sm bg-muted"
                  aria-hidden
                >
                  <div
                    className={cn(
                      "h-full transition-[width] duration-200",
                      i === stages.length - 1 ? "bg-primary" : "bg-fg-muted",
                    )}
                    style={{ width: `${Math.max(ratio * 100, 4)}%` }}
                  />
                </div>
              </li>
            )
          })}
        </ol>
        <div className="flex items-center justify-between border-t border-border-subtle pt-3 text-xs">
          <span className="text-fg-muted">{totalLabel}</span>
          <Badge variant="secondary" size="sm" className="font-mono tabular-nums">
            {stages[stages.length - 1]?.count.toLocaleString() ?? "0"}
          </Badge>
        </div>
      </CardContent>
    </Card>
  )
}
