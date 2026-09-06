import type { ErrorDetail } from "@/types/api"
import { ApiError } from "@/types/api"

/** The server's code for a booking refused by the eligibility policy. */
export const PROVIDER_NOT_ELIGIBLE = "PROVIDER_NOT_ELIGIBLE"

/**
 * The reasons a booking was refused, or null if this error is something else.
 *
 * The server sends every reason as its own entry, so all of them are returned:
 * showing only the first hides work the user still has to do.
 */
export function eligibilityReasons(error: unknown): ErrorDetail[] | null {
  if (!(error instanceof ApiError) || error.code !== PROVIDER_NOT_ELIGIBLE) return null
  const reasons = (error.details ?? []).filter((detail) => detail.field === "eligibility")
  return reasons.length > 0 ? reasons : [{ field: null, message: error.message, code: null }]
}

export function EligibilityFailureNotice({ reasons }: { reasons: ErrorDetail[] }) {
  return (
    <div
      role="alert"
      className="border border-danger/30 bg-danger-soft px-3 py-2 text-sm text-danger-fg"
    >
      <p className="font-medium">This practitioner cannot take this booking.</p>
      <ul className="mt-1 list-disc space-y-0.5 pl-4">
        {reasons.map((reason, index) => (
          <li key={reason.code ?? index}>{reason.message}</li>
        ))}
      </ul>
    </div>
  )
}
