import { Rocket } from "lucide-react"

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { cn } from "@/lib/utils"

interface ImplementationMilestone {
  id: string
  label: string
  date?: string
  done: boolean
}

interface FlightProgressCardProps {
  fromLabel?: string
  toLabel?: string
  fromHint?: string
  toHint?: string
  percent?: number
  milestones?: ReadonlyArray<ImplementationMilestone>
  className?: string
}

const DEFAULT_MILESTONES: ReadonlyArray<ImplementationMilestone> = [
  { id: "kickoff", label: "Kickoff", date: "2026-04-15", done: true },
  { id: "data", label: "Data import", date: "2026-04-29", done: true },
  { id: "training", label: "Training", date: "2026-05-13", done: false },
  { id: "go-live", label: "Go live", date: "2026-05-27", done: false },
]

export function FlightProgressCard({
  fromLabel = "Plan",
  toLabel = "Go live",
  fromHint = "Phase 1",
  toHint = "Phase 4",
  percent,
  milestones = DEFAULT_MILESTONES,
  className,
}: FlightProgressCardProps = {}) {
  const computedPercent =
    percent ??
    (milestones.length === 0
      ? 0
      : Math.round(
          (milestones.filter((m) => m.done).length / milestones.length) * 100,
        ))

  return (
    <Card className={cn("rounded-md", className)}>
      <CardHeader className="border-b border-border-subtle p-3 pb-2">
        <CardTitle className="text-sm font-semibold text-fg">
          Implementation progress
        </CardTitle>
      </CardHeader>
      <CardContent className="grid gap-4 p-4">
        <div className="flex items-start justify-between gap-4">
          <div>
            <div className="font-mono text-lg font-semibold text-fg">
              {fromLabel}
            </div>
            <div className="text-xs text-fg-muted">{fromHint}</div>
          </div>
          <div className="text-right">
            <div className="font-mono text-lg font-semibold text-fg">
              {toLabel}
            </div>
            <div className="text-xs text-fg-muted">{toHint}</div>
          </div>
        </div>

        <div className="grid gap-2">
          <div
            className="relative h-1.5 overflow-hidden rounded-sm bg-muted"
            role="progressbar"
            aria-valuenow={computedPercent}
            aria-valuemin={0}
            aria-valuemax={100}
            aria-label="Implementation progress"
          >
            <div
              className="h-full bg-primary transition-[width] duration-200"
              style={{ width: `${computedPercent}%` }}
            />
            <span
              className="absolute top-1/2 -translate-y-1/2 -translate-x-1/2 size-5 grid place-items-center rounded-full bg-bg ring-1 ring-primary text-primary"
              style={{ left: `${computedPercent}%` }}
              aria-hidden
            >
              <Rocket className="size-2.5" />
            </span>
          </div>
          <div className="flex items-center justify-between font-mono text-xs tabular-nums text-fg-muted">
            <span>{computedPercent}%</span>
            <span>
              {milestones.filter((m) => m.done).length}/{milestones.length} done
            </span>
          </div>
        </div>

        <ul className="grid gap-1.5 border-t border-border-subtle pt-3">
          {milestones.map((m) => (
            <li
              key={m.id}
              className="flex items-baseline gap-3 text-sm text-fg"
            >
              <span
                className={cn(
                  "size-1.5 shrink-0 rounded-full",
                  m.done ? "bg-primary" : "bg-fg-subtle",
                )}
                aria-hidden
              />
              <span
                className={cn("flex-1", m.done && "text-fg-muted line-through")}
              >
                {m.label}
              </span>
              {m.date ? (
                <span className="font-mono text-xs tabular-nums text-fg-subtle">
                  {m.date}
                </span>
              ) : null}
            </li>
          ))}
        </ul>
      </CardContent>
    </Card>
  )
}
