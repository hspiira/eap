import { Check, Rocket } from "lucide-react"

import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { cn } from "@/lib/utils"

export interface ClientOnboardingStep {
  id: string
  label: string
  done: boolean
}

interface ClientOnboardingCardProps {
  steps: ClientOnboardingStep[]
  title?: string
  className?: string
}

export function ClientOnboardingCard({
  steps,
  title = "Setup progress",
  className,
}: ClientOnboardingCardProps) {
  const doneCount = steps.filter((s) => s.done).length
  const total = steps.length
  const percent = total === 0 ? 0 : Math.round((doneCount / total) * 100)
  const nextStepId = steps.find((s) => !s.done)?.id

  return (
    <Card className={cn("rounded-md", className)}>
      <CardHeader className="border-b border-border-subtle p-3 pb-2">
        <CardTitle className="text-sm font-semibold text-fg">{title}</CardTitle>
      </CardHeader>
      <CardContent className="p-3">
        {total === 0 ? (
          <p className="text-sm text-fg-muted">No setup steps defined.</p>
        ) : (
          <>
            <div className="mb-3 flex items-center gap-3">
              <span
                className="grid size-8 shrink-0 place-items-center rounded-md bg-primary text-primary-foreground"
                aria-hidden
              >
                <Rocket className="size-4" />
              </span>
              <div className="min-w-0 flex-1">
                <div
                  role="progressbar"
                  aria-valuenow={percent}
                  aria-valuemin={0}
                  aria-valuemax={100}
                  aria-label="Setup progress"
                  className="h-1.5 w-full overflow-hidden rounded-sm bg-muted"
                >
                  <div
                    className="h-full bg-primary transition-[width] duration-200"
                    style={{ width: `${percent}%` }}
                  />
                </div>
              </div>
              <span className="font-mono text-xs font-medium tabular-nums text-fg">
                {percent}%
              </span>
            </div>
            <ol className="grid gap-1.5">
              {steps.map((step) => {
                const isNext = !step.done && step.id === nextStepId
                return (
                  <li key={step.id} className="flex items-center gap-3">
                    <span
                      className={cn(
                        "flex size-6 shrink-0 items-center justify-center rounded-sm text-xs font-medium",
                        step.done
                          ? "bg-primary text-primary-foreground"
                          : isNext
                            ? "border border-primary text-primary"
                            : "border border-border text-fg-muted",
                      )}
                      aria-hidden
                    >
                      {step.done ? <Check className="size-3.5" /> : null}
                    </span>
                    <span
                      className={cn(
                        "flex-1 text-sm",
                        step.done ? "text-fg-muted line-through" : "text-fg",
                      )}
                    >
                      {step.label}
                    </span>
                  </li>
                )
              })}
            </ol>
          </>
        )}
      </CardContent>
    </Card>
  )
}
