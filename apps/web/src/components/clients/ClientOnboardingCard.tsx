import { Check, Rocket } from "lucide-react"

import { Panel } from "@/components/common/Panel"
import { Button } from "@/components/ui/button"
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
  onStep?: (id: string) => void
}

/**
 * Where the bar sits on the scale.
 *
 * Setup is not pass or fail. A client with nothing filled in needs attention,
 * one part way through is in hand, and only a finished one is green, so the
 * bar has to move through the tones rather than read as done from the first
 * step. Tones are the same four `statusColors` assigns to a badge.
 */
function progressTone(percent: number): { bar: string; label: string } {
  if (percent >= 100) return { bar: "bg-success", label: "text-success-fg" }
  if (percent >= 67) return { bar: "bg-info", label: "text-info-fg" }
  if (percent >= 34) return { bar: "bg-warning", label: "text-warning-fg" }
  return { bar: "bg-danger", label: "text-danger-fg" }
}

export function ClientOnboardingCard({
  steps,
  title = "Setup progress",
  className,
  onStep,
}: ClientOnboardingCardProps) {
  const doneCount = steps.filter((s) => s.done).length
  const total = steps.length
  const percent = total === 0 ? 0 : Math.round((doneCount / total) * 100)
  const nextStepId = steps.find((s) => !s.done)?.id
  const tone = progressTone(percent)

  return (
    <Panel icon={Rocket} title={title} className={className}>
      {total === 0 ? (
        <p className="text-sm text-fg/60">No setup steps defined.</p>
      ) : (
        <>
          <div className="mb-3 flex items-center gap-3">
            <div
              className="h-1.5 flex-1 overflow-hidden rounded-sm bg-fg/8"
              role="progressbar"
              aria-valuenow={percent}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label="Setup progress"
            >
              <div
                className={cn("h-full transition-[width] duration-200", tone.bar)}
                style={{ width: `${percent}%` }}
              />
            </div>
            <span className={cn("text-xs font-medium tabular-nums", tone.label)}>{percent}%</span>
          </div>
          <ol className="grid gap-1.5">
            {steps.map((step) => {
              const isNext = !step.done && step.id === nextStepId
              return (
                <li key={step.id} className="flex items-center gap-2.5">
                  <span
                    className={cn(
                      "grid size-5 shrink-0 place-items-center rounded-sm border text-[10px] font-medium",
                      step.done
                        ? "border-primary bg-primary text-primary-foreground"
                        : isNext
                          ? "border-primary text-primary"
                          : "border-fg/15 text-fg-subtle",
                    )}
                    aria-hidden
                  >
                    {step.done ? <Check className="size-3" /> : null}
                  </span>
                  <span
                    className={cn(
                      "flex-1 text-sm",
                      step.done ? "text-fg-subtle line-through" : "text-fg",
                    )}
                  >
                    {step.label}
                  </span>
                  {!step.done && onStep && (
                    <Button
                      variant="link"
                      size="sm"
                      className="h-auto p-0 text-xs"
                      onClick={() => onStep(step.id)}
                    >
                      Continue
                    </Button>
                  )}
                </li>
              )
            })}
          </ol>
        </>
      )}
    </Panel>
  )
}
