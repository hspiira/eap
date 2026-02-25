import { X, Rocket, Check, ChevronRight } from "lucide-react"

const steps = [
  { id: 1, label: "Set Up Company", done: true },
  { id: 2, label: "Create Resource", done: false },
  { id: 3, label: "Create Service", done: false },
  { id: 4, label: "Link Service with Resource", done: false },
]

export function OnboardingProgressCard() {
  const progressPercent = 25

  return (
    <div className="border border-[#bfc4c9]/25 bg-white p-4">
      <div className="mb-4 flex items-center justify-between">
        <h3 className="text-sm font-semibold text-[#5A626A]">Hey, Let&apos;s Start Now!</h3>
        <button
          type="button"
          className="p-1 text-[#5A626A]/70 hover:text-[#5A626A]"
          aria-label="Close"
        >
          <X className="h-4 w-4" />
        </button>
      </div>

      <div className="mb-4 flex items-center gap-2">
        <div className="flex h-8 w-8 shrink-0 items-center justify-center bg-[#5A626A] text-white">
          <Rocket className="h-4 w-4" />
        </div>
        <div className="min-w-0 flex-1">
          <div className="h-2 w-full bg-[#E6E0D7]">
            <div
              className="h-full bg-[#8BA88B]"
              style={{ width: `${progressPercent}%` }}
            />
          </div>
        </div>
        <span className="text-xs font-medium text-[#5A626A]">{progressPercent}%</span>
      </div>

      <ul className="space-y-2">
        {steps.map((step) => (
          <li key={step.id} className="flex items-center gap-3">
            <div
              className={`flex h-6 w-6 shrink-0 items-center justify-center text-xs font-medium ${
                step.done
                  ? "bg-[#8BA88B] text-white"
                  : "border border-[#bfc4c9]/50 bg-[#E6E0D7]/50 text-[#5A626A]"
              }`}
            >
              {step.done ? <Check className="h-3.5 w-3.5" /> : step.id}
            </div>
            <span
              className={`flex-1 text-sm ${
                step.done ? "text-[#5A626A]" : "text-[#5A626A]/80"
              }`}
            >
              {step.label}
            </span>
            {!step.done && (
              <button
                type="button"
                className="p-0.5 text-[#5A626A]/60 hover:text-[#5A626A]"
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
          className="flex w-full items-center justify-center gap-2 border border-[#bfc4c9]/30 bg-white py-2.5 text-sm font-medium text-[#5A626A] hover:bg-[#fafafa]"
        >
          Let&apos;s Start
          <span className="flex h-5 w-5 items-center justify-center bg-[#8BA88B] text-xs font-medium text-white">
            3
          </span>
        </button>
      </div>
    </div>
  )
}
