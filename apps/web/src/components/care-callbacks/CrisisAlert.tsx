/**
 * Crisis-protocol alert + checklist. Rendered inline whenever the questionnaire
 * answers fire a crisis rule (currently PHQ-9 item 9 > 0). Submitting the outcome
 * with this active will latch the case as `CRISIS_ESCALATED`.
 */

import { AlertTriangle } from "lucide-react"

interface Props {
  reasons: string[]
}

const PROTOCOL_STEPS = [
  "Stay on the line — do not transfer cold.",
  "Run the immediate-risk script (means, plan, intent).",
  "Warm-handoff to the on-call clinician via the crisis bridge.",
  "Notify the supervisor in the on-call channel before closing the case.",
]

export function CrisisAlert({ reasons }: Props) {
  if (reasons.length === 0) return null
  return (
    <div
      role="alert"
      className="border border-danger-soft bg-danger-soft/10 p-4 space-y-3"
    >
      <div className="flex items-center gap-2 text-danger-soft">
        <AlertTriangle className="h-4 w-4" />
        <p className="text-sm font-semibold uppercase tracking-wide">Crisis flag triggered</p>
      </div>
      <ul className="list-disc pl-5 text-sm text-fg space-y-1">
        {reasons.map((r) => (
          <li key={r}>{r}</li>
        ))}
      </ul>
      <div>
        <p className="text-xs font-semibold text-fg/80 uppercase tracking-wide">
          Crisis protocol checklist
        </p>
        <ol className="mt-1 list-decimal pl-5 text-sm text-fg/80 space-y-1">
          {PROTOCOL_STEPS.map((s) => (
            <li key={s}>{s}</li>
          ))}
        </ol>
      </div>
    </div>
  )
}
