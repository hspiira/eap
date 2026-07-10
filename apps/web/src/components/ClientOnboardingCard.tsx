import { Check, Rocket } from "lucide-react"

import { Panel } from "@/components/common/Panel"
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
                className="h-full bg-primary transition-[width] duration-200"
                style={{ width: `${percent}%` }}
              />
            </div>
            <span className="font-mono text-xs font-medium tabular-nums text-fg/75">
              {percent}%
            </span>
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
                          : "border-fg/15 text-fg/40",
                    )}
                    aria-hidden
                  >
                    {step.done ? <Check className="size-3" /> : null}
                  </span>
                  <span
                    className={cn(
                      "flex-1 text-sm",
                      step.done ? "text-fg/45 line-through" : "text-fg",
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
    </Panel>
  )
}
