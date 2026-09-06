import type { Contract } from "@/types/entities"

/**
 * What actually happens on the term end date, using the server-computed
 * `is_active` and `days_remaining` rather than re-deriving from the clock.
 */
export function termLabel(c: Contract): string {
  if (!c.is_active) return "Ended"
  const verb = c.is_auto_renew ? "Renews" : "Ends"
  if (c.days_remaining <= 0) return `${verb} today`
  if (c.days_remaining === 1) return `${verb} tomorrow`
  return `${verb} in ${c.days_remaining} days`
}

/** Warns on a term that ends soon without auto-renew; renewals are not at risk. */
export function termTone(c: Contract): string {
  if (!c.is_active) return "text-danger"
  if (!c.is_auto_renew && c.days_remaining <= 30) return "text-warning"
  return "text-fg-muted"
}
