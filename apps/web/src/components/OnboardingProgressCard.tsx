import { Check, ChevronRight, Rocket, X } from "lucide-react"

const steps = [
  { id: 1, label: "Set Up Company", done: true },
  { id: 2, label: "Create Resource", done: false },
  { id: 3, label: "Create Service", done: false },
  { id: 4, label: "Link Service with Resource", done: false },
]

export function OnboardingProgressCard() {
  const progressPercent = 25

  return (
    <div className="border border-border/25 bg-white p-4">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-ink">Hey, Let&apos;s Start Now!</h3>
        <button
          type="button"
          className="p-1 text-ink/70 hover:text-ink"
          aria-label="Close"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="mb-4 flex items-center gap-2">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center bg-ink text-white">
          <Rocket className="h-4 w-4" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="h-2 w-full bg-warm">
            <div
              className="h-full bg-natural"
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
              className={`flex h-6 w-6 shrink-0 items-center justify-center text-xs font-medium ${
                step.done
                  ? "bg-natural text-white"
                  : "border border-border/50 bg-warm/50 text-ink"
              }`}
            >
              {step.done ? <Check className="h-3.5 w-3.5" /> : step.id}
            </div>
            <span
              className={`flex-1 text-sm ${
                step.done ? "text-ink" : "text-ink/80"
              }`}
            >
              {step.label}
            </span>
            {!step.done && (
              <button
                type="button"
                className="p-0.5 text-ink/60 hover:text-ink"
                aria-label={`Go to ${step.label}`}
              >
                <ChevronRight className="h-4 w-4" />
              </button>
            )}
          </li>
        ))}
      </ul>

      <div className="mt-4">
        <button
          type="button"
          className="flex w-full items-center justify-center gap-2 border border-border/30 bg-white py-2.5 text-sm font-medium text-ink hover:bg-neutral-50"
        >
          Let&apos;s Start
          <span className="flex h-5 w-5 items-center justify-center bg-natural text-xs font-medium text-white">
            3
          </span>
        </button>
      </div>
    </div>
  )
}
