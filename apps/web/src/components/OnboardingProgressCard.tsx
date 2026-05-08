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
        <h3 className="text-sm font-semibold text-fg">Hey, Let&apos;s Start Now!</h3>
        <button
          type="button"
          className="p-1 text-fg/70 hover:text-fg"
          aria-label="Close"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="mb-4 flex items-center gap-2">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center bg-fg text-white">
          <Rocket className="h-4 w-4" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="h-2 w-full bg-surface">
            <div
              className="h-full bg-primary"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
        <span className="text-xs font-medium text-fg">{progressPercent}%</span>
      </div>

      <ul className="space-y-2">
        {steps.map((step) => (
          <li key={step.id} className="flex items-center gap-3">
            <div
              className={`flex h-6 w-6 shrink-0 items-center justify-center text-xs font-medium ${
                step.done
                  ? "bg-primary text-white"
                  : "border border-border/50 bg-surface/50 text-fg"
              }`}
            >
              {step.done ? <Check className="h-3.5 w-3.5" /> : step.id}
            </div>
            <span
              className={`flex-1 text-sm ${
                step.done ? "text-fg" : "text-fg/80"
              }`}
            >
              {step.label}
            </span>
            {!step.done && (
              <button
                type="button"
                className="p-0.5 text-fg/60 hover:text-fg"
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
          className="flex w-full items-center justify-center gap-2 border border-border/30 bg-white py-2.5 text-sm font-medium text-fg hover:bg-neutral-50"
        >
          Let&apos;s Start
          <span className="flex h-5 w-5 items-center justify-center bg-primary text-xs font-medium text-white">
            3
          </span>
        </button>
      </div>
    </div>
  )
}
