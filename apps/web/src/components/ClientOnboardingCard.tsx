import { Check, ChevronRight, Rocket } from "lucide-react"

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

export function ClientOnboardingCard({ steps, title = "Setup progress", className }: ClientOnboardingCardProps) {
  const doneCount = steps.filter((s) => s.done).length
  const progressPercent = steps.length === 0 ? 0 : Math.round((doneCount / steps.length) * 100)

  if (steps.length === 0) {
    return (
      <div
        className={cn(
          "flex flex-col border border-ink/30 rounded-none bg-neutral-50 overflow-hidden",
          className
        )}
      >
        <div className="border-b border-ink/20 px-4 py-3 bg-warm/20">
          <h3 className="text-sm font-semibold text-ink">{title}</h3>
        </div>
        <div className="px-4 py-4 text-sm text-ink/80">No setup steps defined.</div>
      </div>
    )
  }

  return (
    <div
      className={cn(
        "flex flex-col border border-ink/30 rounded-none bg-neutral-50 overflow-hidden",
        className
      )}
    >
      <div className="border-b border-ink/20 px-4 py-3 bg-warm/20">
        <h3 className="text-sm font-semibold text-ink">{title}</h3>
      </div>
      <div className="p-4">
        <div className="mb-4 flex items-center gap-2">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center bg-ink text-white rounded-none">
            <Rocket className="h-4 w-4" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="h-2 w-full bg-warm rounded-none">
              <div
                className="h-full bg-natural rounded-none"
                style={{ width: `${progressPercent}%` }}
              />
            </div>
          </div>
          <span className="text-xs font-medium text-ink">{progressPercent}%</span>
        </div>
        <ul className="space-y-2">
          {steps.map((step) => (
            <li key={step.id} className="flex items-center gap-3">
              <div
                className={cn(
                  "flex h-6 w-6 shrink-0 items-center justify-center text-xs font-medium rounded-none",
                  step.done
                    ? "bg-natural text-white"
                    : "border border-ink/30 bg-warm/50 text-ink"
                )}
              >
                {step.done ? <Check className="h-3.5 w-3.5" /> : null}
              </div>
              <span
                className={cn(
                  "flex-1 text-sm",
                  step.done ? "text-ink" : "text-ink/80"
                )}
              >
                {step.label}
              </span>
              {!step.done && (
                <span className="p-0.5 text-ink/60" aria-hidden>
                  <ChevronRight className="h-4 w-4" />
                </span>
              )}
            </li>
          ))}
        </ul>
      </div>
    </div>
  )
}
