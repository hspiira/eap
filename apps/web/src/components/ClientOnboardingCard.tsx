import { Rocket, Check, ChevronRight } from "lucide-react"
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
          "flex flex-col border border-[#5A626A]/30 rounded-none bg-[#fafafa] overflow-hidden",
          className
        )}
      >
        <div className="border-b border-[#5A626A]/20 px-4 py-3 bg-[#E6E0D7]/20">
          <h3 className="text-sm font-semibold text-[#5A626A]">{title}</h3>
        </div>
        <div className="px-4 py-4 text-sm text-[#5A626A]/80">No setup steps defined.</div>
      </div>
    )
  }

  return (
    <div
      className={cn(
        "flex flex-col border border-[#5A626A]/30 rounded-none bg-[#fafafa] overflow-hidden",
        className
      )}
    >
      <div className="border-b border-[#5A626A]/20 px-4 py-3 bg-[#E6E0D7]/20">
        <h3 className="text-sm font-semibold text-[#5A626A]">{title}</h3>
      </div>
      <div className="p-4">
        <div className="mb-4 flex items-center gap-2">
          <div className="flex h-8 w-8 shrink-0 items-center justify-center bg-[#5A626A] text-white rounded-none">
            <Rocket className="h-4 w-4" />
          </div>
          <div className="min-w-0 flex-1">
            <div className="h-2 w-full bg-[#E6E0D7] rounded-none">
              <div
                className="h-full bg-natural rounded-none"
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
                className={cn(
                  "flex h-6 w-6 shrink-0 items-center justify-center text-xs font-medium rounded-none",
                  step.done
                    ? "bg-natural text-white"
                    : "border border-[#5A626A]/30 bg-[#E6E0D7]/50 text-[#5A626A]"
                )}
              >
                {step.done ? <Check className="h-3.5 w-3.5" /> : null}
              </div>
              <span
                className={cn(
                  "flex-1 text-sm",
                  step.done ? "text-[#5A626A]" : "text-[#5A626A]/80"
                )}
              >
                {step.label}
              </span>
              {!step.done && (
                <span className="p-0.5 text-[#5A626A]/60" aria-hidden>
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
