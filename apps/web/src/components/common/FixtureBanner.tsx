import { FlaskConical } from "lucide-react"

import { useFixtures } from "@/lib/fixtures"

/**
 * Marks the session as running on fixture data.
 *
 * Several resources (engagements, surveys, care-callbacks, incidents,
 * diagnoses, questionnaires, pricing) serve local fixtures rather than calling
 * the API. That was previously silent, so fabricated rows were indistinguishable
 * from real ones and a broken BE endpoint looked like a working screen.
 */
export function FixtureBanner() {
  if (!useFixtures()) return null
  return (
    <div
      role="status"
      className="flex shrink-0 items-center justify-center gap-1.5 bg-warning-soft px-3 py-1 text-[11px] font-medium text-warning-fg"
    >
      <FlaskConical className="size-3 shrink-0" aria-hidden />
      <span>
        Fixture mode — some data is local sample data, not from the API. Set{" "}
        <code className="font-mono">VITE_USE_FIXTURES=false</code> to use the real API.
      </span>
    </div>
  )
}
