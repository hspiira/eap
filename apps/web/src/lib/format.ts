/**
 * Formatting helpers — single source of truth for dates, times, and money.
 * Prefer these over inlining `new Date(x).toLocaleDateString()` or currency
 * string templates in components, so display drift between routes is eliminated.
 */

const EM_DASH = '—'

/** Locale short date, e.g. "7/14/2026". Returns em-dash for nullish/invalid input. */
export function formatDate(value: string | number | Date | null | undefined): string {
  if (value == null || value === '') return EM_DASH
  const d = new Date(value)
  return Number.isNaN(d.getTime()) ? EM_DASH : d.toLocaleDateString()
}

/** Locale date + time. Returns em-dash for nullish/invalid input. */
export function formatDateTime(value: string | number | Date | null | undefined): string {
  if (value == null || value === '') return EM_DASH
  const d = new Date(value)
  return Number.isNaN(d.getTime()) ? EM_DASH : d.toLocaleString()
}

/**
 * Currency amount with an optional currency code prefix, e.g. "USD 1,200".
 * Returns em-dash when the amount is nullish.
 */
export function formatMoney(
  amount: number | null | undefined,
  currency?: string | null,
): string {
  if (amount == null) return EM_DASH
  return `${currency ?? ''} ${amount.toLocaleString()}`.trim()
}

/**
 * Convert an ISO datetime string to the value shape a `<input type="datetime-local">`
 * expects (`YYYY-MM-DDTHH:mm`, local time). Returns '' for nullish/invalid input.
 */
export function toLocalDatetimeInput(value: string | null | undefined): string {
  if (!value) return ''
  const d = new Date(value)
  if (Number.isNaN(d.getTime())) return ''
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`
}
