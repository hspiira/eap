import { Check, ChevronRight, Rocket, X } from "lucide-react"

import { Button } from "@/components/ui/button"
import {
  Card,
  CardContent,
  CardHeader,
  CardTitle,
} from "@/components/ui/card"
import { cn } from "@/lib/utils"

interface OnboardingStep {
  id: number
  label: string
  done: boolean
}

const DEFAULT_STEPS: ReadonlyArray<OnboardingStep> = [
  { id: 1, label: "Set up company", done: true },
  { id: 2, label: "Add first client", done: false },
  { id: 3, label: "Create a service", done: false },
  { id: 4, label: "Assign a service to a client", done: false },
]

interface OnboardingProgressCardProps {
  steps?: ReadonlyArray<OnboardingStep>
  onDismiss?: () => void
  onStartStep?: (step: OnboardingStep) => void
}

export function OnboardingProgressCard({
  steps = DEFAULT_STEPS,
  onDismiss,
  onStartStep,
}: OnboardingProgressCardProps = {}) {
  const completed = steps.filter((s) => s.done).length
  const total = steps.length
  const percent = total === 0 ? 0 : Math.round((completed / total) * 100)
  const remaining = total - completed
  const nextStep = steps.find((s) => !s.done)

  return (
    <Card className="rounded-md">
      <CardHeader className="flex-row items-center justify-between gap-2 space-y-0 p-3 pb-2">
        <CardTitle className="text-sm font-semibold text-fg">
          Get started
        </CardTitle>
        {onDismiss ? (
          <Button
            variant="ghost"
            size="icon"
            className="size-7"
            aria-label="Dismiss onboarding"
            onClick={onDismiss}
          >
            <X className="size-4" />
          </Button>
        ) : null}
      </CardHeader>

      <CardContent className="grid gap-3 p-3 pt-0">
        <div className="flex items-center gap-3">
          <span
            className="flex size-8 shrink-0 items-center justify-center rounded-md bg-primary text-primary-foreground"
            aria-hidden
          >
            <Rocket className="size-4" />
          </span>
          <div className="min-w-0 flex-1">
            <div
              className="h-1.5 w-full overflow-hidden rounded-sm bg-muted"
              role="progressbar"
              aria-valuenow={percent}
              aria-valuemin={0}
              aria-valuemax={100}
              aria-label="Onboarding progress"
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
            const isNext = !step.done && step.id === nextStep?.id
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
                  {step.done ? <Check className="size-3.5" /> : step.id}
                </span>
                <span
                  className={cn(
                    "flex-1 text-sm",
                    step.done ? "text-fg-muted line-through" : "text-fg",
                  )}
                >
                  {step.label}
                </span>
                {!step.done && onStartStep ? (
                  <Button
                    variant="ghost"
                    size="icon"
                    className="size-6"
                    aria-label={`Go to ${step.label}`}
                    onClick={() => onStartStep(step)}
                  >
                    <ChevronRight className="size-4" />
                  </Button>
                ) : null}
              </li>
            )
          })}
        </ol>

        {nextStep ? (
          <Button
            variant="outline"
            className="w-full justify-center gap-2"
            onClick={() => onStartStep?.(nextStep)}
          >
            Continue setup
            <span className="inline-flex size-5 items-center justify-center rounded-sm bg-primary font-mono text-xs font-medium tabular-nums text-primary-foreground">
              {remaining}
            </span>
          </Button>
        ) : null}
      </CardContent>
    </Card>
  )
}
